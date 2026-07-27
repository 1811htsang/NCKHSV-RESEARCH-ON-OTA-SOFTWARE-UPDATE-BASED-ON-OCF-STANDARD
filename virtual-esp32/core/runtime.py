import time

from config import CHECK_INTERVAL


class Runtime:

    def __init__(self, device):

        self.device = device

    def run(self):

        self.device.setup()

        while True:

            self.device.loop()

            time.sleep(CHECK_INTERVAL)