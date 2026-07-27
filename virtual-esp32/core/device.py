class VirtualESP32:

    def __init__(self,
                 firmware,
                 mqtt,
                 ota):

        self.firmware = firmware

        self.mqtt = mqtt

        self.ota = ota

    def setup(self):

        self.mqtt.connect()

        self.firmware.setup(self)

    def loop(self):

        self.firmware.loop(self)

        self.publish_status()

        self.check_update()

    def publish_status(self):

        self.mqtt.publish()

    def check_update(self):

        self.ota.check()