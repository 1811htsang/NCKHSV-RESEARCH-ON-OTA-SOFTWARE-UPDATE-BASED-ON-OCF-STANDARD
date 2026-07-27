import importlib

from storage.flash import Flash


class Bootloader:

    def __init__(self):

        self.flash = Flash()

    def load_firmware(self):

        boot = self.flash.read_boot()

        module_name = boot["firmware"]

        module = importlib.import_module(
            f"firmware.{module_name}"
        )

        return module.Firmware()