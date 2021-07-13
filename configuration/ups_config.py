from xknx.devices import Sensor, BinarySensor, Switch
from configuration.channel import Channel
from configuration.group import Group


class UPSConfiguration:

    def __init__(self, ups, config_json):
        self.ups = ups
        self.general_configuration =  config_json
        self.config = config_json[self.ups.name]

        self.channel_list = self.create_channels()
        self.group_list = self.create_groups()
        self.prezenta_tensiune = self.create_binary_sensor_for_ups()

        self.global_minim = self.config["global_minim"]
        self.global_maxim = self.config["global_maxim"]

    def create_channels(self):
        interval_canale = self.config['interval_canale']
        start_canal = interval_canale[0]
        end_canal = interval_canale[1]

        estimated_value_channels = self.general_configuration['curent_estimat_canale']

        channels = []
        for i in range(start_canal, end_canal + 1):
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
            )
            switch = Switch(
                self.ups.xknx,
                name=f'switch {i}',
                group_address=self.config["switch"] + "/" + str(i),
            )
            channels.append(Channel(sensor=sensor, binary_sensor=binary_sensor, switch=switch,
                                    estimated_value=estimated_value_channels[i], index=i))
        return channels

    def create_binary_sensor_for_ups(self) -> BinarySensor:
        group_adress_tensiune = self.config["prezenta_tensiune"]
        return BinarySensor(
            self.ups.xknx,
            name=f'Prezenta tensiune {self.ups.name}',
            group_address_state=group_adress_tensiune,
        )

    def create_groups(self):
        interval_canale = self.config['interval_canale']
        start_canal = interval_canale[0]
        config_groups = self.config['grupe']
        group_list = []
        for group_config in config_groups:

            mapped_indexes = [index_canal - start_canal for index_canal in group_config['canale']]
            channels_for_group = [self.channel_list[index_canal] for index_canal in mapped_indexes]
            created_group = Group(name=group_config['name'], max_current=group_config['max_current'],
                                  channel_list=channels_for_group)
            group_list.append(created_group)
        return group_list
