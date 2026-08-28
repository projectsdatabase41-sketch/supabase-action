#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный апдейтер эмбеддингов через OpenRouter (все таблицы)"""
import os
import requests
from datetime import datetime

EMBED_MODEL = "nvidia/nemotron-3-embed-1b:free"  # бесплатно, 2048d → режем до 2000
TARGET_DIM = 2000
TEXT_LIMIT = 1500
LIMIT = 50

OR_KEY = os.getenv("OPENROUTER_KEY_MY")
URL_MY = os.getenv("SUPABASE_URL_MY")
KEY_MY = os.getenv("SUPABASE_KEY_MY")
URL_PUB = os.getenv("SUPABASE_PUB_URL")
KEY_PUB = os.getenv("SUPABASE_PUB_KEY")

# Расширенный список кандидат-полей для автодетекта
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
    """Эмбеддинг через OpenRouter"""
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
    # обрезаем до TARGET_DIM
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
