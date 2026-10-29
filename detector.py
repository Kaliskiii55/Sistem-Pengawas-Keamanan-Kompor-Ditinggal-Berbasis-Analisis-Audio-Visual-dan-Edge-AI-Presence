"""NODE 3 — Laptop: Fusion Rules & Dashboard Server."""

import json
from shared.dashboard_server import start_dashboard_server, update_dashboard_data
from shared.mqtt_connection import get_mqtt_client, project_id

# State terkini dari kedua Edge
SYSTEM_STATE = {
    "person_detected": True,
    "stove_active": False,
    "idle_seconds": 0,
    "overall_status": "NORMAL"  # NORMAL, MONITORING, ALERT_DANGER
}

def evaluate_rules():
    """Sensor Fusion: Jika kompor aktif & orang tidak terdeteksi melebihi batas -> ALERT."""
    if SYSTEM_STATE["stove_active"] and not SYSTEM_STATE["person_detected"]:
        if SYSTEM_STATE["idle_seconds"] >= 10:
            SYSTEM_STATE["overall_status"] = "ALERT_DANGER: KOMPOR DITINGGAL!"
        else:
            SYSTEM_STATE["overall_status"] = "WARNING: ORANG MENJAUH"
    else:
        SYSTEM_STATE["overall_status"] = "SAFE / NORMAL"
    
    update_dashboard_data(SYSTEM_STATE)
    print(f"[DECISION ENGINE] {SYSTEM_STATE['overall_status']}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        dev = data.get("device")
        
        if dev == "edge1_presence":
            SYSTEM_STATE["person_detected"] = data.get("person_detected", False)
            SYSTEM_STATE["idle_seconds"] = data.get("idle_seconds", 0)
        elif dev == "edge2_stove":
            SYSTEM_STATE["stove_active"] = data.get("stove_active", False)
            
        evaluate_rules()
    except Exception as e:
        print(f"[ERROR] Parse MQTT: {e}")

def run():
    server, thread, url = start_dashboard_server()
    print(f"\nStoveWatch — NODE 3 Laptop Dashboard: {url}")[cite: 6]
    print(f"MQTT Topic Prefix: {project_id()}/*\n")

    client = get_mqtt_client("laptop_detector")
    client.on_message = on_message
    client.connect_to_cloud()
    client.subscribe(f"{project_id()}/+/telemetry")
    client.loop_forever()

if __name__ == "__main__":
    run()