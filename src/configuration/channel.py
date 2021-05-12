from xknx.devices import Sensor,Switch,BinarySensor


class Channel:
    def __init__(self, sensor : Sensor, binary_sensor : BinarySensor, switch : Switch, index):
        self.sensor = sensor
        self.binary_sensor = binary_sensor
        self.switch = switch
        self.index = index