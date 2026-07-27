import json
import paho.mqtt.client as mqtt

from config import MQTT_HOST
from config import MQTT_PORT


class MQTTClient:

    def __init__(self, device):

        self.device = device

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

    def connect(self):

        self.client.connect(
            MQTT_HOST,
            MQTT_PORT
        )

        self.client.loop_start()

        print("[MQTT] Connected")

    def publish_status(self):

        payload = {

            "device": self.device.device_id,

            # "version": self.device.version,

            "status": "running"

        }

        self.client.publish(
            "virtual-esp32/status",
            json.dumps(payload)
        )