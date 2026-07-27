class Runtime:

    def __init__(self, firmware):

        self.firmware = firmware

    def run(self):

        self.firmware.setup()

        while True:

            self.firmware.loop()