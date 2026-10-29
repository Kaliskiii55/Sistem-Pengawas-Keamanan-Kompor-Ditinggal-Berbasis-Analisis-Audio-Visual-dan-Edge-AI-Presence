import os
import ssl
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

def project_id() -> str:
    return os.getenv("PROJECT_ID", "stovewatch_kelompok_07")

def get_mqtt_client(client_id_suffix: str) -> mqtt.Client:
    host = os.getenv("MQTT_HOST", "broker.hivemq.com")
    port = int(os.getenv("MQTT_PORT", 8883))
    use_tls = os.getenv("MQTT_TLS", "true").lower() == "true"
    
    full_client_id = f"{project_id()}_{client_id_suffix}"
    
    # Callback API v2 kompatibel
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, full_client_id)
    except AttributeError:
        client = mqtt.Client(full_client_id)

    if use_tls:
        context = ssl.create_default_context()
        client.tls_set_context(context)

    # Tambahkan helper method connect_to_cloud agar cocok dengan kode runner
    def connect_to_cloud():
        client.connect(host, port, keepalive=60)

    client.connect_to_cloud = connect_to_cloud
    return client