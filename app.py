"""
app.py — Flask server for OSINT-Privacy-Scanner
Exposes backend functions as REST API endpoints.
Run with: python app.py
"""

from flask import Flask, request, jsonify, render_template
from privacy_scanner import (
    scan_platforms,
    calculate_risk,
    save_scan_history,
    view_database_history,
    search_username_history,
    view_statistics,
    init_db,
    DB_PATH,
    max_score as MAX_SCORE,
)
import sqlite3

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helper — fetch raw rows from DB (returns list of dicts)
# ---------------------------------------------------------------------------

def query_db(sql, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # lets us access columns by name
    cur = conn.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    result = [dict(row) for row in rows]
    return result[0] if (one and result) else result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the frontend page."""
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    """
    POST /api/scan
    Body: { "username": "someuser" }
    Returns scan results, score, and risk level.
    """
    data = request.get_json()
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"error": "Username cannot be empty."}), 400

    score, results = scan_platforms(username)
    risk = calculate_risk(score)
    save_scan_history(username, score, risk)

    # Build a clean list for the frontend
    platforms = [
        {"platform": platform, "found": exists, "detail": detail}
        for platform, exists, detail in results
    ]

    return jsonify({
        "username": username,
        "score": score,
        "max_score": MAX_SCORE,
        "risk": risk,
        "platforms": platforms,
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    """
    GET /api/history?limit=10
    Returns recent scan history from the database.
    """
    limit = request.args.get("limit", 10, type=int)
    rows = query_db(
        "SELECT username, score, risk, timestamp FROM scan_history ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    return jsonify(rows)


@app.route("/api/search", methods=["GET"])
def api_search():
    """
    GET /api/search?username=someuser
    Returns all scans for a specific username.
    """
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username parameter is required."}), 400

    rows = query_db(
        "SELECT username, score, risk, timestamp FROM scan_history WHERE username = ? ORDER BY timestamp DESC",
        (username,)
    )
    return jsonify(rows)


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """
    GET /api/stats
    Returns total scans, risk breakdown, and most scanned username.
    """
    total = query_db("SELECT COUNT(*) as total FROM scan_history", one=True)
    risk_breakdown = query_db("SELECT risk, COUNT(*) as count FROM scan_history GROUP BY risk")
    top_user = query_db(
        "SELECT username, COUNT(*) as count FROM scan_history GROUP BY username ORDER BY count DESC LIMIT 1",
        one=True
    )

    return jsonify({
        "total_scans": total["total"] if total else 0,
        "risk_breakdown": risk_breakdown,
        "most_scanned": top_user or {},
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)