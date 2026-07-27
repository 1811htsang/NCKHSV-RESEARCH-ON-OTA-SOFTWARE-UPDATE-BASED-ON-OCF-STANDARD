from core.bootloader import Bootloader
from core.runtime import Runtime

print("Virtual ESP32 Booting...")

boot = Bootloader()

firmware = boot.load()

runtime = Runtime(firmware)

runtime.run()