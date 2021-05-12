class Channel:
    def __init__(self, sensor, binary_sensor, switch, index):
        self.sensor = sensor
        self.binary_sensor = binary_sensor
        self.switch = switch
        self.index = index