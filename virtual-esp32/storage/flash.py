import json


class Flash:

    def __init__(self):

        self.boot_file = "storage/boot.json"

    def read_boot(self):

        with open(self.boot_file) as f:

            return json.load(f)

    def write_boot(self, data):

        with open(self.boot_file, "w") as f:

            json.dump(data, f, indent=4)