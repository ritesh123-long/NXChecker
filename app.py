import re
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def check_instagram(username: str):
    username = username.strip().lower()

    if username.startswith("@"):
        username = username[1:]

    if not re.match(r"^[a-z0-9._]+$", username):
        return {"valid": False, "error": "Invalid username format"}

    url = f"https://www.instagram.com/{username}/"

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        if res.status_code == 200:
            is_private = '"is_private":true' in res.text
            return {
                "valid": True,
                "exists": True,
                "private": is_private,
                "url": url
            }

        elif res.status_code == 404:
            return {"valid": True, "exists": False}

        return {"valid": True, "exists": None}

    except Exception:
        return {"valid": True, "exists": None}


# ---------- Public API ----------
@app.get("/api/check")
def api_check():
    username = request.args.get("u", "").strip()

    if not username:
        return jsonify({"error": "username param required ?u="}), 400

    data = check_instagram(username)
    return jsonify(data)


# ---------- Frontend ----------
@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
