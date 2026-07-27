class OTAManager:

    def __init__(self, device):
        self.device = device

    def check(self):
        print("[OTA] Checking for update...")