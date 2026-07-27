from storage.flash import Flash
from network.mqtt_client import MQTTClient
from ota.ota_manager import OTAManager


class VirtualESP32:

    def __init__(self, device_id, firmware):

        self.device_id = device_id

        self.firmware = firmware

        self.version = firmware.VERSION

        # Hardware / Services
        self.flash = Flash()
        self.mqtt = MQTTClient(self)
        self.ota = OTAManager(self)

    def setup(self):

        print(f"[{self.device_id}] Booting...")

        print(f"[Firmware] Version {self.version}")

        # Connect MQTT
        self.mqtt.connect()

        # Run firmware setup
        self.firmware.setup(self)

    def loop(self):

        # Execute firmware loop
        self.firmware.loop(self)

        # Publish heartbeat
        self.mqtt.publish_status()

        # Check OTA
        self.ota.check()