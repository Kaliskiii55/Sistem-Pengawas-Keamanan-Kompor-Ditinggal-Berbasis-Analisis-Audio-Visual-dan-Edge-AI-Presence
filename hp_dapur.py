"""NODE 1: HP Dapur (Edge 1) - Pemantau Keberadaan Manusia."""

import time
import json
import cv2
import paho.mqtt.client as mqtt
from sharedprocessing import PresenceTimeDecay
from shared.mqtt_connection import get_mqtt_client, project_id

def run():
    client = get_mqtt_client("edge1_presence")
    client.connect_to_cloud()
    client.loop_start()

    topic = f"{project_id()}/edge1/telemetry"
    decay_analyzer = PresenceTimeDecay(max_idle_sec=15)
    
    # Inisialisasi model AI deteksi tubuh/wajah OpenCV bawaan
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)

    print(f"[EDGE 1] Kamera aktif, memantau kehadiran... Topik: {topic}")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.5)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            person_detected = len(faces) > 0

            # Processing 2: Hitung status idle
            presence_info = decay_analyzer.update(person_detected, delta_time=1.0)
            
            payload = {
                "device": "edge1_presence",
                "person_detected": person_detected,
                **presence_info,
                "timestamp": time.time()
            }
            client.publish(topic, json.dumps(payload))
            print(f"[EDGE 1] Person: {person_detected} | Status: {presence_info['state']} ({presence_info['idle_seconds']}s)")
            time.sleep(1.0)
    finally:
        cap.release()
        client.loop_stop()

if __name__ == "__main__":
    run()