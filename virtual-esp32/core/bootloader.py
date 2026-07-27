import json
import importlib


class Bootloader:

    def load(self):

        with open("storage/boot.json") as f:

            boot = json.load(f)

        module = importlib.import_module(
            f"firmware.{boot['firmware']}"
        )

        firmware = module.Firmware()

        return firmware