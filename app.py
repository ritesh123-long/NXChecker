import re
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --------- Accurate Instagram Check Logic ---------
def check_instagram(username: str):
    username = username.strip().lower()

    if username.startswith("@"):
        username = username[1:]

    if not re.match(r"^[a-z0-9._]+$", username):
        return {"valid": False, "error": "Invalid username format"}

    url = f"https://www.instagram.com/{username}/"

    try:
        res = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        html = res.text.lower()

        # ❌ Real 404
        if res.status_code == 404:
            return {"valid": True, "exists": False}

        # ❌ Soft-404 (returns 200 but page not found)
        soft404_signals = [
            "page isn't available",
            "page not found",
            "user not found",
            "the link you followed may be broken",
        ]
        if any(s in html for s in soft404_signals):
            return {"valid": True, "exists": False}

        # 🔍 Detect JSON flags inside HTML
        is_private = '"is_private":true' in html
        is_verified = '"is_verified":true' in html

        # If JSON flags exist → account exists
        if '"is_private":' in html or '"is_verified":' in html:
            return {
                "valid": True,
                "exists": True,
                "private": is_private,
                "verified": is_verified,
                "url": url
            }

        # ⚠️ Could not confirm
        return {"valid": True, "exists": None}

    except Exception:
        return {"valid": True, "exists": None}


# --------- Public API ---------
@app.get("/api/check")
def api_check():
    username = request.args.get("u", "").strip()

    if not username:
        return jsonify({"error": "username param required ?u="}), 400

    return jsonify(check_instagram(username))


# --------- Frontend ---------
@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
