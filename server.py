from flask import Flask, request, jsonify
import requests

ESP_IP = "192.168.4.1"
ESP_PORT = 80

app = Flask(__name__)

# ---------------- ESP HELPER ----------------

def esp_get(path, params=None):
    url = f"http://{ESP_IP}:{ESP_PORT}{path}"
    try:
        r = requests.get(url, params=params, timeout=2)
        print(f"[ESP] {url} -> {r.status_code} {r.text}")
        return r
    except Exception as e:
        print("[ESP ERROR]", e)
        return None


# ---------------- TEST PING ----------------

@app.route("/ping_esp")
def ping_esp():
    r = esp_get("/ping")
    if not r:
        return jsonify({"ok": False, "error": "no response"}), 500
    return jsonify({"ok": True, "response": r.text})


# ---------------- RAW STATUS ----------------

@app.route("/esp_status")
def esp_status():
    r = esp_get("/status")

    if not r:
        return jsonify({"ok": False, "error": "no response"}), 500

    try:
        data = r.json()
        return jsonify({
            "ok": True,
            "data": data
        })

    except Exception as e:
        print("JSON ERROR:", r.text)

        return jsonify({
            "ok": False,
            "raw": r.text
        })



# ---------------- SET RELAYS (RAW) ----------------

@app.route("/set_relays", methods=["GET"])
def set_relays():

    r1 = request.args.get("r1", "0")
    r2 = request.args.get("r2", "0")
    r3 = request.args.get("r3", "0")

    print(f"[REQUEST] r1={r1} r2={r2} r3={r3}")

    r = esp_get("/setRelays", params={
        "r1": r1,
        "r2": r2,
        "r3": r3
    })

    if not r:
        return jsonify({"ok": False, "error": "ESP not reachable"}), 500

    return jsonify({
        "ok": True,
        "esp_response": r.text
    })


# ---------------- QUICK TEST PATTERNS ----------------

@app.route("/test_cycle")
def test_cycle():
    """
    Быстрый тест: включает/выключает реле по шагам
    """

    steps = [
        (1,0,0),
        (1,1,0),
        (1,1,1),
        (0,0,0),
    ]

    results = []

    for r1, r2, r3 in steps:
        r = esp_get("/setRelays", params={
            "r1": r1,
            "r2": r2,
            "r3": r3
        })

        results.append({
            "state": [r1, r2, r3],
            "ok": bool(r),
            "resp": r.text if r else None
        })

    return jsonify(results)


# ---------------- BASIC HOME ----------------

@app.route("/")
def home():
    return """
    <h2>ESP DEBUG SERVER</h2>
    <ul>
        <li>/ping_esp</li>
        <li>/esp_status</li>
        <li>/set_relays?r1=1&r2=0&r3=1</li>
        <li>/test_cycle</li>
    </ul>
    """
# ---------------- APP STATUS ----------------

@app.route("/status")
def app_status():

    r = esp_get("/status")

    if not r:
        return jsonify({"error": "ESP not reachable"}), 500

    try:
        data = r.json()
        return jsonify(data)

    except:
        return jsonify({"error": "bad json"}), 500


# ---------------- APP LEVEL CONTROL ----------------

@app.route("/set")
def set_level():

    level = request.args.get("level", "0")

    level = int(level)

    r1 = 1 if level >= 1 else 0
    r2 = 1 if level >= 2 else 0
    r3 = 1 if level >= 3 else 0

    r = esp_get("/setRelays", params={
        "r1": r1,
        "r2": r2,
        "r3": r3
    })

    if not r:
        return jsonify({"error": "ESP not reachable"}), 500

    return jsonify({"ok": True})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
