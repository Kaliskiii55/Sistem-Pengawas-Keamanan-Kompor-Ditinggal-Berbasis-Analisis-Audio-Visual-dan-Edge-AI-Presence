"""NODE 2: HP Kompor (Edge 2) - Pemantau Aktivitas Kompor via Audio RMS."""

import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from sharedprocessing import StoveNoiseAnalyzer
from shared.mqtt_connection import get_mqtt_client, project_id

def run():
    client = get_mqtt_client("edge2_stove")
    client.connect_to_cloud()
    client.loop_start()

    topic = f"{project_id()}/edge2/telemetry"
    analyzer = StoveNoiseAnalyzer(window_size=15)

    print(f"[EDGE 2] Sensor kompor aktif... Topik: {topic}")

    try:
        while True:
            # Ambil sampel audio (atau simulasi sensor jika belum compile pyaudio di HP)
            # Menghasilkan sinyal getaran / suara masak
            simulated_audio = np.random.normal(0, 0.08, 1024) 
            
            # Processing 1: Hitung RMS dan Z-Score Anomaly
            rms = analyzer.compute_rms(simulated_audio)
            z_score, is_active = analyzer.compute_z_score(rms)

            payload = {
                "device": "edge2_stove",
                "rms": round(rms, 4),
                "z_score": round(z_score, 2),
                "stove_active": is_active,
                "timestamp": time.time()
            }
            client.publish(topic, json.dumps(payload))
            print(f"[EDGE 2] RMS: {rms:.4f} | Stove Active: {is_active}")
            time.sleep(1.0)
    finally:
        client.loop_stop()

if __name__ == "__main__":
    run()