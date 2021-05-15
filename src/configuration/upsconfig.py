from xknx.devices import Sensor, BinarySensor, Switch

from src.configuration.channel import Channel
from src.configuration.group import Group


class UPSConfiguration():

    def __init__(self, ups, config_json):
        self.ups = ups
        self.config = config_json

        self.channel_list = self.create_channels()
        self.group_list = self.create_groups()

        self.estimated_value_channels = self.config['curent_estimat_canale']

    def create_channels(self):
        channel_number = int(self.config["numar_canale"])
        channels = [Channel] * (channel_number + 1)
        for i in range(1, channel_number + 1):
            sensor = Sensor(
                self.ups.xknx,
                name=f'Curent {i}',
                group_address_state=self.config["sensor"] + "/" + str(i),
                value_type='electric_current',
            )
            binary_sensor = BinarySensor(
                self.ups.xknx,
                name=f'CH{i}_state',
                group_address_state=self.config["binary_sensor"] + "/" + str(i),
                device_class='motion',
            )
            switch = Switch(
                self.ups.xknx,
                name=f'switch {i}',
                group_address=self.config["switch"] + "/" + str(i),
            )
            channels[i] = Channel(sensor=sensor, binary_sensor=binary_sensor, switch=switch, index=i)
        return channels

    def create_groups(self):
        config_groups = self.config['grupe']
        group_list = []
        for group_config in config_groups:
            created_group = Group(name=group_config['name'], max_current=group_config['max_current'],
                                  channel_list=group_config['canale'])
            group_list.append(created_group)
        return group_list