import json
import os
import uuid
import threading
import time
import random
import paho.mqtt.client as mqtt
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

load_dotenv()

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "stations.json"

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/data/phupham")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "dev_tok_947953e60e985ebf4c9ebfad32ee3f9a")

mqtt_client = None
simulation_intervals = {}
simulation_lock = threading.Lock()

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_mqtt():
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = mqtt.Client(client_id="simulator_server")
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_client.loop_start()
        except Exception as e:
            print(f"MQTT connect failed: {e}")
    return mqtt_client

def generate_metrics(metrics_def):
    return {
        m["name"]: round(random.uniform(m["min"], m["max"]), m.get("decimals", 1))
        for m in metrics_def
    }

def send_sensor_data(station, sensor):
    client = get_mqtt()
    if not client:
        return False
    device_id = station.get("device_id", station["id"])
    token = station.get("token", DEVICE_TOKEN)
    payload = {
        "observation_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "station_id": station["id"],
        "station_name": station["name"],
        "sensor_type": sensor.get("type", sensor["name"]),
        "metrics": generate_metrics(sensor.get("metrics", [])),
        "raw_payload": {
            "device_id": device_id,
            "token": token,
            "rssi": random.randint(-90, -50)
        }
    }
    result = client.publish(MQTT_TOPIC, json.dumps(payload))
    return result.rc == mqtt.MQTT_ERR_SUCCESS

def simulation_loop(station_id, sensor_id, interval):
    while True:
        with simulation_lock:
            key = f"{station_id}_{sensor_id}"
            if key not in simulation_intervals or not simulation_intervals[key]:
                break
        data = load_data()
        for st in data:
            if st["id"] == station_id:
                for se in st.get("sensors", []):
                    if se["id"] == sensor_id:
                        send_sensor_data(st, se)
                        break
        time.sleep(interval)
    with simulation_lock:
        simulation_intervals.pop(f"{station_id}_{sensor_id}", None)

# ─── API ────────────────────────────────────────────────

@app.route("/api/stations", methods=["GET"])
def get_stations():
    return jsonify(load_data())

@app.route("/api/stations", methods=["POST"])
def create_station():
    data = load_data()
    body = request.get_json()
    station = {
        "id": body.get("id", str(uuid.uuid4())),
        "name": body.get("name", "Trạm mới"),
        "device_id": body.get("device_id", ""),
        "token": body.get("token", DEVICE_TOKEN),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sensors": []
    }
    data.append(station)
    save_data(data)
    return jsonify(station), 201

@app.route("/api/stations/<station_id>", methods=["DELETE"])
def delete_station(station_id):
    data = load_data()
    data = [s for s in data if s["id"] != station_id]
    save_data(data)
    with simulation_lock:
        for key in list(simulation_intervals.keys()):
            if key.startswith(f"{station_id}_"):
                simulation_intervals[key] = False
    return jsonify({"ok": True})

@app.route("/api/stations/<station_id>/sensors", methods=["POST"])
def add_sensor(station_id):
    data = load_data()
    body = request.get_json()
    for st in data:
        if st["id"] == station_id:
            sensor = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", "Cảm biến mới"),
                "type": body.get("type", body.get("name", "unknown")),
                "metrics": body.get("metrics", []),
                "running": False
            }
            st["sensors"].append(sensor)
            save_data(data)
            return jsonify(sensor), 201
    return jsonify({"error": "Station not found"}), 404

@app.route("/api/stations/<station_id>/sensors/<sensor_id>", methods=["DELETE"])
def delete_sensor(station_id, sensor_id):
    data = load_data()
    for st in data:
        if st["id"] == station_id:
            st["sensors"] = [s for s in st["sensors"] if s["id"] != sensor_id]
            save_data(data)
            with simulation_lock:
                simulation_intervals.pop(f"{station_id}_{sensor_id}", None)
            return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/stations/<station_id>/sensors/<sensor_id>/simulation", methods=["POST"])
def toggle_simulation(station_id, sensor_id):
    body = request.get_json()
    action = body.get("action", "start")
    interval = body.get("interval", 5)

    data = load_data()
    for st in data:
        if st["id"] == station_id:
            for se in st.get("sensors", []):
                if se["id"] == sensor_id:
                    key = f"{station_id}_{sensor_id}"
                    if action == "start":
                        se["running"] = True
                        with simulation_lock:
                            simulation_intervals[key] = True
                        t = threading.Thread(target=simulation_loop, args=(station_id, sensor_id, interval), daemon=True)
                        t.start()
                    else:
                        se["running"] = False
                        with simulation_lock:
                            simulation_intervals[key] = False
                    save_data(data)
                    return jsonify({"ok": True, "running": se["running"]})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/simulation/start_all", methods=["POST"])
def start_all():
    data = load_data()
    for st in data:
        for se in st.get("sensors", []):
            key = f"{st['id']}_{se['id']}"
            se["running"] = True
            with simulation_lock:
                if key not in simulation_intervals:
                    simulation_intervals[key] = True
                    t = threading.Thread(target=simulation_loop, args=(st["id"], se["id"], 5), daemon=True)
                    t.start()
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/simulation/stop_all", methods=["POST"])
def stop_all():
    with simulation_lock:
        for key in list(simulation_intervals.keys()):
            simulation_intervals[key] = False
    data = load_data()
    for st in data:
        for se in st.get("sensors", []):
            se["running"] = False
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/mqtt/status", methods=["GET"])
def mqtt_status():
    client = get_mqtt()
    if client and client.is_connected():
        return jsonify({"connected": True, "broker": MQTT_BROKER, "topic": MQTT_TOPIC})
    return jsonify({"connected": False, "broker": MQTT_BROKER, "topic": MQTT_TOPIC})

# ─── Serve HTML ─────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(Path(__file__).parent, "index.html")

if __name__ == "__main__":
    import uuid
    app.run(host="0.0.0.0", port=5000, debug=True)