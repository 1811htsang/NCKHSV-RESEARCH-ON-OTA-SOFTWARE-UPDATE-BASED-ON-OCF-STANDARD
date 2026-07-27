class WiFi:

    def __init__(self):

        self.connected = False

    def connect(self):

        print("[WiFi] Connecting...")

        self.connected = True

        print("[WiFi] Connected")

    def is_connected(self):

        return self.connected