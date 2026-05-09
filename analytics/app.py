import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "mydatabase")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)


@app.route("/health_check")
def health_check():
    return jsonify({"status": "ok"})


@app.route("/readiness_check")
def readiness_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "ready"})
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return jsonify({"status": "not ready", "error": str(e)}), 500


@app.route("/api/reports/daily_usage")
def daily_usage():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DATE(joined_at) AS date, COUNT(*) AS visits
                FROM tokens
                GROUP BY DATE(joined_at)
                ORDER BY date
                """
            )
        ).fetchall()
    return jsonify({str(r[0]): r[1] for r in rows})


@app.route("/api/reports/user_visits")
def user_visits():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT u.id,
                       u.joined_at,
                       COUNT(t.id) AS visits
                FROM users u
                LEFT JOIN tokens t ON u.id = t.user_id
                GROUP BY u.id, u.joined_at
                ORDER BY u.id
                """
            )
        ).fetchall()
    result = [
        {"id": r[0], "joined_at": str(r[1]), "visits": r[2]}
        for r in rows
    ]
    return jsonify(result)


if __name__ == "__main__":
    logger.info("Starting coworking analytics service on port 5153")
    app.run(host="0.0.0.0", port=5153)
