#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный апдейтер эмбеддингов для всех таблиц"""
import os
import requests
from datetime import datetime
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-large"
TARGET_DIM = 2000
TEXT_LIMIT = 1500
LIMIT = 50

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

URL_MY = os.getenv("SUPABASE_URL_MY")
KEY_MY = os.getenv("SUPABASE_KEY_MY")
URL_PUB = os.getenv("SUPABASE_PUB_URL")
KEY_PUB = os.getenv("SUPABASE_PUB_KEY")

CANDIDATE_FIELDS = ["topic", "title", "name", "problem", "solution",
                    "summary", "content", "details", "description", "author"]

TABLES = [
    {"name": "notes", "url": URL_MY, "key": KEY_MY,
     "text_fields": ["topic", "summary", "content"], "filter": None},
    {"name": "qwen_ops_memory", "url": URL_MY, "key": KEY_MY,
     "text_fields": ["topic", "content"], "filter": None},
    {"name": "qwen_public_instructions", "url": URL_PUB, "key": KEY_PUB,
     "text_fields": ["topic", "problem", "solution", "details"],
     "filter": {"status": "eq.active"}},
    {"name": "books", "url": URL_PUB, "key": KEY_PUB, "text_fields": "auto", "filter": None},
    {"name": "products_bs_shooting", "url": URL_PUB, "key": KEY_PUB, "text_fields": "auto", "filter": None},
    {"name": "shooting_rules", "url": URL_PUB, "key": KEY_PUB, "text_fields": "auto", "filter": None},
    # search_log — это лог, эмбеддинги ему не нужны. Надо — добавь строкой выше.
]


def hdr(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def detect(t):
    """Возвращает (текстовые поля, все колонки таблицы)"""
    r = requests.get(f"{t['url']}/{t['name']}", headers=hdr(t["key"]),
                     params={"limit": 1}, timeout=30)
    cols = set(r.json()[0].keys()) if r.status_code == 200 and r.json() else set()
    if isinstance(t["text_fields"], list):
        fields = [f for f in t["text_fields"] if f in cols] if cols else t["text_fields"]
    else:
        fields = [f for f in CANDIDATE_FIELDS if f in cols]
        print(f"Авто-поля: {fields}")
    return fields, cols


def get_rows(t, fields, cols):
    rows = []
    H = hdr(t["key"])
    base = "id," + ",".join(fields)

    # 1. Пустые эмбеддинги
    params = {"embedding": "is.null", "select": base, "limit": LIMIT}
    if t["filter"]:
        params.update(t["filter"])
    r = requests.get(f"{t['url']}/{t['name']}", headers=H, params=params, timeout=30)
    if r.status_code == 200:
        rows.extend(r.json())

    # 2. Устаревшие (если в таблице есть даты)
    if {"updated_at", "embedding_created_at"} <= cols:
        params = {"embedding": "not.is.null",
                  "select": base + ",updated_at,embedding_created_at", "limit": 100}
        if t["filter"]:
            params.update(t["filter"])
        r = requests.get(f"{t['url']}/{t['name']}", headers=H, params=params, timeout=30)
        if r.status_code == 200:
            for row in r.json():
                upd, emb = row.get("updated_at"), row.get("embedding_created_at")
                if upd and emb:
                    try:
                        if datetime.fromisoformat(upd.replace("Z", "+00:00")) > \
                           datetime.fromisoformat(emb.replace("Z", "+00:00")):
                            rows.append(row)
                    except Exception:
                        pass
    return rows


def gen_emb(text):
    resp = client.embeddings.create(input=text[:TEXT_LIMIT],
                                    model=EMBED_MODEL, dimensions=TARGET_DIM)
    return resp.data[0].embedding


def update_row(t, row_id, vec):
    r = requests.patch(f"{t['url']}/{t['name']}", headers=hdr(t["key"]),
                       params={"id": f"eq.{row_id}"},
                       json={"embedding": vec, "embedding_model": EMBED_MODEL},
                       timeout=30)
    return r.status_code in (200, 204)


def main():
    for t in TABLES:
        print(f"\n=== {t['name']} ===")
        fields, cols = detect(t)
        if not fields or "embedding" not in cols:
            print("Нет текстовых полей или колонки embedding — скип")
            continue
        rows = get_rows(t, fields, cols)
        if not rows:
            print("Нечего обновлять")
            continue
        print(f"К обработке: {len(rows)}")
        for i, row in enumerate(rows, 1):
            text = " ".join(str(row.get(f) or "") for f in fields).strip()
            if not text:
                continue
            try:
                if update_row(t, row["id"], gen_emb(text)):
                    print(f"[{i}/{len(rows)}] ✓ id={row['id']}")
                else:
                    print(f"[{i}/{len(rows)}] ✗ id={row['id']}")
            except Exception as e:
                print(f"[{i}/{len(rows)}] ✗ id={row['id']}: {str(e)[:60]}")


if __name__ == "__main__":
    main()
