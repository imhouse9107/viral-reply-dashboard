#!/usr/bin/env python3
"""Viral Reply Dashboard — mobile-friendly suggestion viewer with copy buttons."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "dashboard.db"
API_KEY = os.environ.get("DASHBOARD_API_KEY", "alba-viral-2026")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL,
            profile TEXT NOT NULL,
            brand TEXT,
            platform TEXT,
            post_url TEXT,
            post_author TEXT,
            post_text TEXT,
            suggested_reply TEXT,
            engagement INTEGER DEFAULT 0,
            velocity REAL DEFAULT 0,
            content_type TEXT DEFAULT 'reply',
            created_at TEXT,
            push_date TEXT
        )
    """)
    conn.commit()
    return conn


@app.route("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.route("/api/push", methods=["POST"])
def push_suggestions():
    """Receive suggestions from the bot."""
    key = request.headers.get("X-API-Key") or request.args.get("key")
    if key != API_KEY:
        abort(401, "Invalid API key")

    data = request.get_json()
    if not data or "suggestions" not in data:
        abort(400, "Missing suggestions array")

    conn = get_db()
    count = 0
    for s in data["suggestions"]:
        conn.execute("""
            INSERT INTO suggestions (person, profile, brand, platform, post_url,
                post_author, post_text, suggested_reply, engagement, velocity,
                content_type, created_at, push_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s.get("person", ""),
            s.get("profile", ""),
            s.get("brand", ""),
            s.get("platform", ""),
            s.get("post_url", ""),
            s.get("post_author", ""),
            s.get("post_text", ""),
            s.get("suggested_reply", ""),
            s.get("engagement", 0),
            s.get("velocity", 0),
            s.get("content_type", "reply"),
            s.get("created_at", datetime.utcnow().isoformat()),
            datetime.utcnow().strftime("%Y-%m-%d"),
        ))
        count += 1
    conn.commit()
    conn.close()
    return {"pushed": count}


@app.route("/")
def index():
    """Redirect to today's view."""
    return render_template("index.html")


@app.route("/<person>")
@app.route("/<person>/<date>")
def dashboard(person, date=None):
    """Dashboard for a specific person."""
    if person.lower() not in ("henry", "scott", "lewis"):
        abort(404, "Unknown person")

    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM suggestions
        WHERE LOWER(person) = ? AND push_date = ?
        ORDER BY engagement DESC, velocity DESC
    """, (person.lower(), date)).fetchall()
    conn.close()

    suggestions = [dict(r) for r in rows]

    # Calculate max engagement for relative sizing
    max_eng = max((s["engagement"] for s in suggestions), default=1) or 1

    return render_template(
        "dashboard.html",
        person=person.title(),
        date=date,
        suggestions=suggestions,
        max_engagement=max_eng,
        count=len(suggestions),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5555))
    app.run(host="0.0.0.0", port=port, debug=True)
