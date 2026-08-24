import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
PAYHIP_VERIFY_URL = "https://payhip.com/api/v2/license/verify"


def verify_license():
    payload = request.get_json(silent=True) or request.form
    license_key = str(payload.get("license_key", "")).strip()
    api_key = os.environ.get("PAYHIP_API_KEY", "").strip()

    if not api_key:
        return jsonify({"success": False, "error": "server_not_configured"}), 500
    if not license_key or len(license_key) > 200:
        return jsonify({"success": False, "error": "invalid_license_key"}), 400

    try:
        response = requests.post(
            PAYHIP_VERIFY_URL,
            data={"api_key": api_key, "license_key": license_key},
            timeout=15,
        )
    except requests.RequestException:
        return jsonify({"success": False, "error": "payhip_unavailable"}), 502

    if response.status_code == 401:
        return jsonify({"success": False, "error": "payhip_authentication_failed"}), 502
    if response.status_code >= 500:
        return jsonify({"success": False, "error": "payhip_unavailable"}), 502

    try:
        payhip_data = response.json()
    except ValueError:
        return jsonify({"success": False, "error": "invalid_payhip_response"}), 502

    if payhip_data.get("success") is True:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "invalid_license"}), 200


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/verify-license")
def verify_license_endpoint():
    return verify_license()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
