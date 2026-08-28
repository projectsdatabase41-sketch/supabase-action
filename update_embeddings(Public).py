#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный апдейтер эмбеддингов для всех таблиц (notes + qwen_public_instructions)"""
import os
import requests
from datetime import datetime
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-large"
TARGET_DIM = 2000
TEXT_LIMIT = 1500

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === КОНФИГУРАЦИЯ ТАБЛИЦ ===
TABLES = [
    {
        "name": "notes",
        "url": os.getenv("SUPABASE_URL_MY"),
        "key": os.getenv("SUPABASE_KEY_MY"),
        "text_fields": ["topic", "summary", "content"],
        "filter": None,
        "limit": 50,
    },
    {
        "name": "qwen_public_instructions",
        "url": os.getenv("SUPABASE_PUB_URL"),
        "key": os.getenv("SUPABASE_PUB_KEY"),
        "text_fields": ["topic", "problem", "solution", "details"],
        "filter": {"status": "eq.active"},  # только активные инструкции
        "limit": 50,
    },
    # rag_documents НЕ трогаем
]


def hdr(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def get_rows_to_update(t):
    """Пустые эмбеддинги + устаревшие (запись новее эмбеддинга)"""
    rows = []
    H = hdr(t["key"])

    # 1. Пустые
    params = {"embedding": "is.null",
              "select": "id," + ",".join(t["text_fields"]),
              "limit": t["limit"]}
    if t["filter"]:
        params.update(t["filter"])
    r = requests.get(f"{t['url']}/{t['name']}", headers=H, params=params, timeout=30)
    if r.status_code == 200:
        rows.extend(r.json())

    # 2. Устаревшие
    params = {"embedding": "not.is.null",
              "select": "id,updated_at,embedding_created_at," + ",".join(t["text_fields"]),
              "limit": 100}
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


def gen_embedding(text):
    resp = client.embeddings.create(
        input=text[:TEXT_LIMIT],
        model=EMBED_MODEL,
        dimensions=TARGET_DIM
    )
    return resp.data[0].embedding


def update_row(t, row_id, vec):
    r = requests.patch(
        f"{t['url']}/{t['name']}",
        headers=hdr(t["key"]),
        params={"id": f"eq.{row_id}"},
        json={"embedding": vec, "embedding_model": EMBED_MODEL},
        timeout=30
    )
    return r.status_code in (200, 204)


def main():
    for t in TABLES:
        print(f"\n=== {t['name']} ===")
        rows = get_rows_to_update(t)
        if not rows:
            print("Нечего обновлять")
            continue
        print(f"К обработке: {len(rows)}")

        for i, row in enumerate(rows, 1):
            text = " ".join(str(row.get(f) or "") for f in t["text_fields"]).strip()
            if not text:
                continue
            try:
                vec = gen_embedding(text)
                if update_row(t, row["id"], vec):
                    print(f"[{i}/{len(rows)}] ✓ id={row['id']}")
                else:
                    print(f"[{i}/{len(rows)}] ✗ id={row['id']} patch failed")
            except Exception as e:
                print(f"[{i}/{len(rows)}] ✗ id={row['id']}: {str(e)[:60]}")


if __name__ == "__main__":
    main()
