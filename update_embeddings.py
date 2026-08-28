#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный апдейтер эмбеддингов через OpenRouter (все таблицы)"""
import os
import requests
from datetime import datetime

EMBED_MODEL = "openai/text-embedding-3-large"
TARGET_DIM = 2000
TEXT_LIMIT = 1500
LIMIT = 50

OR_KEY = os.getenv("OPENROUTER_KEY_MY")
URL_MY = os.getenv("SUPABASE_URL_MY")
KEY_MY = os.getenv("SUPABASE_KEY_MY")
URL_PUB = os.getenv("SUPABASE_PUB_URL")
KEY_PUB = os.getenv("SUPABASE_PUB_KEY")

CANDIDATE_FIELDS = [
    "topic", "title", "name", "problem", "solution", "summary", "content",
    "details", "description", "author", "text", "body", "rule_text",
    "rule_name", "book_title", "product_name", "product_description",
    "category", "note", "full_text", "short_description", "long_description"
]

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
]


def hdr(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def gen_emb(text):
    if not text.strip():
        return None
    r = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": text[:TEXT_LIMIT]},
        timeout=45
    )
    if r.status_code != 200:
        raise Exception(f"OpenRouter {r.status_code}: {r.text[:80]}")
    emb = r.json()["data"][0]["embedding"]
    if len(emb) > TARGET_DIM:
        emb = emb[:TARGET_DIM]
    elif len(emb) < TARGET_DIM:
        emb = emb + [0.0] * (TARGET_DIM - len(emb))
    return emb


def detect(t):
    r = requests.get(f"{t['url']}/{t['name']}", headers=hdr(t["key"]),
                     params={"limit": 1}, timeout=30)
    cols = set(r.json()[0].keys()) if r.status_code == 200 and r.json() else set()
    if isinstance(t["text_fields"], list):
        fields = [f for f in t["text_fields"] if f in cols] if cols else t["text_fields"]
    else:
        fields = [f for f in CANDIDATE_FIELDS if f in cols]
        print(f"Авто-поля: {fields} (все колонки: {sorted(cols)})")
    return fields, cols


def get_rows(t, fields, cols):
    rows = []
    H = hdr(t["key"])
    base = "id," + ",".join(fields)

    params = {"embedding": "is.null", "select": base, "limit": LIMIT}
    if t["filter"]:
        params.update(t["filter"])
    r = requests.get(f"{t['url']}/{t['name']}", headers=H, params=params, timeout=30)
    if r.status_code == 200:
        rows.extend(r.json())

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


def update_row(t, row_id, vec):
    r = requests.patch(f"{t['url']}/{t['name']}", headers=hdr(t["key"]),
                       params={"id": f"eq.{row_id}"},
                       json={"embedding": vec, "embedding_model": EMBED_MODEL},
                       timeout=30)
    return r.status_code in (200, 204)


def main():
    if not OR_KEY:
        print("OPENROUTER_KEY_MY не задан!")
        return
    for t in TABLES:
        print(f"\n=== {t['name']} ===")
        fields, cols = detect(t)
        if not fields or "embedding" not in cols:
            print("Нет текстовых полей или embedding — скип")
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
                vec = gen_emb(text)
                if not vec:
                    continue
                if update_row(t, row["id"], vec):
                    print(f"[{i}/{len(rows)}] ✓ id={row['id']}")
                else:
                    print(f"[{i}/{len(rows)}] ✗ id={row['id']} patch fail")
            except Exception as e:
                print(f"[{i}/{len(rows)}] ✗ id={row['id']}: {str(e)[:80]}")


if __name__ == "__main__":
    main()
