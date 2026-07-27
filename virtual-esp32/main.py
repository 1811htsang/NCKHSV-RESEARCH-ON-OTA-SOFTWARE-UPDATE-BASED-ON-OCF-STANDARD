from core.bootloader import Bootloader
from core.device import VirtualESP32
from core.runtime import Runtime

from config import DEVICE_ID


def main():
    bootloader = Bootloader()

    firmware = bootloader.load_firmware()

    device = VirtualESP32(
        device_id=DEVICE_ID,
        firmware=firmware
    )

    runtime = Runtime(device)

    runtime.run()


if __name__ == "__main__":
    main()