import json
import sqlite3
from datetime import datetime

from .config import DB_PATH


def db_init():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        reviewId TEXT PRIMARY KEY,
        placeTitle TEXT,
        branch_city TEXT,
        stars INTEGER,
        text TEXT,
        publishedAtDate TEXT,
        reviewUrl TEXT,
        likesCount INTEGER,
        isLocalGuide INTEGER,
        reviewerNumberOfReviews INTEGER,
        food_rating REAL,
        service_rating REAL,
        atmosphere_rating REAL,
        reviewDetailedRating_json TEXT,
        reviewContext_json TEXT,
        has_images INTEGER,
        images_json TEXT,
        owner_response_date TEXT,
        owner_response_text TEXT,
        has_owner_response INTEGER,
        inserted_at TEXT DEFAULT (datetime('now')),
        raw_json TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS analysis (
        reviewId TEXT PRIMARY KEY,
        branch_city TEXT,
        is_issue INTEGER,
        issue_types_json TEXT,
        severity TEXT,
        affected_dimensions_json TEXT,
        key_signals_json TEXT,
        summary TEXT,
        recommended_actions_json TEXT,
        suggested_owner_reply TEXT,
        analyzed_at TEXT DEFAULT (datetime('now')),
        raw_analysis_json TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS state (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    con.commit()
    con.close()


def db_has_review(review_id: str) -> bool:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM reviews WHERE reviewId = ?", (review_id,))
    exists = cur.fetchone() is not None
    con.close()
    return exists


def db_has_analysis(review_id: str) -> bool:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM analysis WHERE reviewId = ?", (review_id,))
    exists = cur.fetchone() is not None
    con.close()
    return exists


def db_save_review(item: dict):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO reviews
        (reviewId, placeTitle, branch_city, stars, text, publishedAtDate, reviewUrl,
         likesCount, isLocalGuide, reviewerNumberOfReviews,
         food_rating, service_rating, atmosphere_rating,
         reviewDetailedRating_json, reviewContext_json,
         has_images, images_json,
         owner_response_date, owner_response_text, has_owner_response,
         raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("reviewId"),
        item.get("title", ""),
        item.get("branch_city"),
        item.get("stars"),
        (item.get("text") or ""),
        (item.get("publishedAtDate") or ""),
        (item.get("reviewUrl") or ""),

        item.get("likesCount"),
        1 if item.get("isLocalGuide") else 0,
        item.get("reviewerNumberOfReviews"),

        item.get("food_rating"),
        item.get("service_rating"),
        item.get("atmosphere_rating"),

        json.dumps(item.get("reviewDetailedRating") or {}, ensure_ascii=False),
        json.dumps(item.get("reviewContext") or {}, ensure_ascii=False),

        item.get("has_images", 0),
        json.dumps(item.get("reviewImageUrls") or [], ensure_ascii=False),

        item.get("responseFromOwnerDate"),
        (item.get("responseFromOwnerText") or ""),
        1 if (item.get("responseFromOwnerText") and str(item.get("responseFromOwnerText")).strip()) else 0,

        json.dumps(item, ensure_ascii=False)
    ))
    con.commit()
    con.close()


def db_save_analysis(review_id: str, branch_city: str, analysis: dict):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO analysis
        (reviewId, branch_city, is_issue, issue_types_json, severity,
         affected_dimensions_json, key_signals_json, summary,
         recommended_actions_json, suggested_owner_reply, raw_analysis_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        review_id,
        branch_city,
        1 if analysis.get("is_issue") else 0,
        json.dumps(analysis.get("issue_types", []), ensure_ascii=False),
        analysis.get("severity", "low"),
        json.dumps(analysis.get("affected_dimensions", []), ensure_ascii=False),
        json.dumps(analysis.get("key_signals", []), ensure_ascii=False),
        analysis.get("summary", ""),
        json.dumps(analysis.get("recommended_actions", []), ensure_ascii=False),
        analysis.get("suggested_owner_reply", ""),
        json.dumps(analysis, ensure_ascii=False),
    ))
    con.commit()
    con.close()


def get_state(key: str) -> str | None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT value FROM state WHERE key = ?", (key,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None


def set_state(key: str, value: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO state(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    con.commit()
    con.close()
