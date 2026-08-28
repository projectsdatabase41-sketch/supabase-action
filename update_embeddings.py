#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновление эмбеддингов через text-embedding-3-large (GitHub Actions)"""
import os
import requests
import json
from datetime import datetime
from openai import OpenAI

# === КОНФИГУРАЦИЯ (секреты из GitHub) ===
SUPABASE_URL = os.getenv("SUPABASE_URL_MY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_MY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY_MY")  # запасной, для других моделей

EMBED_MODEL = "text-embedding-3-large"
TARGET_DIM = 2000
TEXT_LIMIT = 1500

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

client = OpenAI(api_key=OPENAI_API_KEY)


def get_notes_to_update():
    """Найти записи требующие обновления эмбеддинга"""
    notes_to_update = []

    # 1. Записи без эмбеддинга
    r = requests.get(
        f"{SUPABASE_URL}/notes",
        headers=HEADERS,
        params={
            "embedding": "is.null",
            "select": "id,topic,summary,content,updated_at",
            "limit": 50
        },
        timeout=30
    )
    if r.status_code == 200:
        data = r.json()
        notes_to_update.extend(data)
        print(f"Без эмбеддинга: {len(data)}")

    # 2. Записи где эмбеддинг устарел (запись отредактирована позже эмбеддинга)
    r = requests.get(
        f"{SUPABASE_URL}/notes",
        headers=HEADERS,
        params={
            "embedding": "not.is.null",
            "select": "id,topic,summary,content,updated_at,embedding_created_at",
            "limit": 100
        },
        timeout=30
    )
    if r.status_code == 200:
        stale = []
        for note in r.json():
            updated = note.get("updated_at")
            emb_created = note.get("embedding_created_at")
            if updated and emb_created:
                try:
                    upd_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    emb_dt = datetime.fromisoformat(emb_created.replace("Z", "+00:00"))
                    if upd_dt > emb_dt:
                        stale.append(note)
                except:
                    pass
        if stale:
            print(f"Устаревшие эмбеддинги: {len(stale)}")
            notes_to_update.extend(stale)

    return notes_to_update


def generate_embedding(text):
    """Генерация эмбеддинга через text-embedding-3-large с обрезкой до 2000d"""
    text = text[:TEXT_LIMIT]
    response = client.embeddings.create(
        input=text,
        model=EMBED_MODEL,
        dimensions=TARGET_DIM
    )
    return response.data[0].embedding


def update_note_embedding(note_id, embedding_vector):
    """Обновить эмбеддинг записи (дата ставится триггером автоматически)"""
    payload = {
        "embedding": embedding_vector,
        "embedding_model": EMBED_MODEL
    }
    r = requests.patch(
        f"{SUPABASE_URL}/notes",
        headers=HEADERS,
        params={"id": f"eq.{note_id}"},
        json=payload,
        timeout=30
    )
    return r.status_code in (200, 204)


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Поиск записей для обновления...")
    notes = get_notes_to_update()

    if not notes:
        print("Нет записей для обновления.")
        return

    print(f"К обработке: {len(notes)}")

    for i, note in enumerate(notes, 1):
        full_text = f"{note.get('topic', '')} {note.get('summary', '')} {note.get('content', '')}".strip()
        if not full_text:
            continue

        try:
            vec = generate_embedding(full_text)
            if update_note_embedding(note["id"], vec):
                print(f"[{i}/{len(notes)}] ✓ {note.get('topic', '')[:40]}")
            else:
                print(f"[{i}/{len(notes)}] ✗ Failed: {note.get('topic', '')[:40]}")
        except Exception as e:
            print(f"[{i}/{len(notes)}] ✗ Error {note['id']}: {str(e)[:60]}")


if __name__ == "__main__":
    main()
