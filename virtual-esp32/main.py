from core.bootloader import Bootloader
from core.device import VirtualESP32
from core.runtime import Runtime

from network.mqtt_client import MQTTClient
from ota.ota_manager import OTAManager

bootloader = Bootloader()

firmware = bootloader.load_firmware()

mqtt = MQTTClient()

ota = OTAManager()

device = VirtualESP32(
    firmware,
    mqtt,
    ota
)

runtime = Runtime(device)

runtime.run()