import asyncio
import json
from asyncio import Lock

from termcolor import colored
from xknx import XKNX
from xknx.devices import Sensor, BinarySensor, Switch
from xknx.io import ConnectionConfig, ConnectionType

from channel import Channel
from group import Group


class UPS:
    def __init__(self, xknx: XKNX, config_json: json):
        self.xknx = xknx
        self.config = config_json
        self.group_list = []  # lista de grupe pe care un UPS le are
        self.channels = []  # lista de toate canalele pe care un UPS le are
        self.maximum_current = 10

        self.estimated_value_channels = []  # Valoare estimata a intensitatii atunci cand pornesc un canal
        self.lacat = Lock()

        self.initialization_finished = False

    async def initialize_from_configuration(self):
        self.estimated_value_channels = self.config['curent_estimat_canale']
        self.create_groups()
        self.create_devices()

        for device in self.xknx.devices:
            await device.sync()

    def create_groups(self):
        config_groups = self.config['grupe']
        for group_config in config_groups:
            created_group = Group(name=group_config['name'], max_current=group_config['max_current'],
                                  channel_list=group_config['canale'])
            self.group_list.append(created_group)

    async def binary_sensor_update(self, binary_sensor: BinarySensor):
        print(f"Binary sensor {binary_sensor.name} is {binary_sensor.state}")

    async def switch_update(self, switch: Switch):
        print(f"The value of the {switch.name} is {switch.state}")

    def all_channels_intialized(self) -> bool:
        for channel in self.channels:
            if channel.sensor.resolve_state() is None:
                return False
        return True

    # chemat de fiecare data cand s-a modificat valoarea unui senzor
    async def sensor_update(self, sensor: Sensor):
        print("Sensor updated", sensor.name, sensor.resolve_state())

        if self.initialization_finished is False and self.all_channels_intialized():
            print(colored("All initialized!", 'green', attrs=['bold']))
            self.initialization_finished = True
        await self.lestare_delestare()

    def create_devices(self):
        channel_number = int(self.config["numar_canale"])
        self.channels = [Channel] * (channel_number + 1)
        for i in range(1, channel_number + 1):
            sensor = Sensor(
                self.xknx,
                name=f'Curent {i}',
                group_address_state=self.config["sensor"] + "/" + str(i),
                value_type='electric_current',
                device_updated_cb=self.sensor_update,
            )
            binary_sensor = BinarySensor(
                self.xknx,
                name=f'CH{i}_state',
                group_address_state=self.config["binary_sensor"] + "/" + str(i),
                device_class='motion',
                device_updated_cb=self.binary_sensor_update,
            )
            switch = Switch(
                self.xknx,
                name=f'switch {i}',
                group_address=self.config["switch"] + "/" + str(i),
                device_updated_cb=self.switch_update,
            )
            self.channels[i] = Channel(sensor=sensor, binary_sensor=binary_sensor, switch=switch, index=i)

    def print_initialization(self):
        print("Afisam grupele citite din JSON")
        for group in self.group_list:
            print(group)
        print("Afisam device-urile, adica sensor, binary sensor si switch")
        for device in self.xknx.devices:
            print(device.get_name())

    def get_maximum_current(self):
        return self.maximum_current

    def print_sensor_state(self):
        total_current_UPS = 0
        sum_group = []  # suma curentilor pe grup UPS

        for group in self.group_list:
            total_group = 0  # initializare suma curentilor pe grup UPS
            for channel in group.channel_list:
                sensor = channel.sensor
                if sensor.resolve_state() is not None:
                    total_current_UPS += sensor.resolve_state()
                    total_group += sensor.resolve_state()
            sum_group.append(total_group)
        print("===============")
        for index in range(1, len(self.channels)):
            print(self.channels[index], end=' ')
        print()
        print("Total UPS", total_current_UPS)
        print("Grupe UPS", sum_group)

    async def lestare_delestare(self):
        async with self.lacat:
            print("Lestare delestare")
            suma_totala = 0

            for group in self.group_list:
                suma_grupa = 0
                for channel in group.channel_list:
                    switch = channel.switch
                    sensor = channel.sensor
                    binary_sensor = channel.binary_sensor

                    current_value = sensor.resolve_state()
                    estimated_current_value = self.estimated_value_channels[channel.index]

                    if current_value is None:
                        colored(f"Am gasit None {channel.index} !!!", 'red')
                        return
                    if channel.binary_sensor.state == 1:
                        # daca ma aflu pe un canal deschis verific sa nu depaseasca limitele
                        # daca pe grupa este mai mare sau egal sau pe total e mai mare sau egal il inchid direct
                        if suma_grupa + current_value >= group.max_current or suma_totala + current_value >= self.get_maximum_current():
                            await channel.switch.set_off()
                            if suma_grupa + current_value >= group.max_current:
                                print(
                                    colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de grup", "grey",
                                            attrs=['bold']))
                            elif suma_grupa + current_value >= self.maximum_current:
                                print(colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de totala",
                                              "grey",
                                              attrs=['bold']))
                            else:
                                print(colored("Avem o problema la sincronizare sigurr", 'red', attrs=['bold']))
                            self.print_sensor_state()
                        else:
                            suma_totala += current_value
                            suma_grupa += current_value
                    elif binary_sensor.state == 0:
                        if suma_grupa + estimated_current_value < group.max_current and suma_totala + estimated_current_value < self.get_maximum_current():
                            await switch.set_on()
                            print(colored(f"Inchid canalul {switch.name} Pentru ca e ok", "grey", attrs=['bold']))
                            self.print_sensor_state()
                            suma_grupa += estimated_current_value
                            suma_totala += estimated_current_value


async def main():
    xknx = XKNX(
        daemon_mode=True,
        connection_config=ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip="192.168.1.52", gateway_port=3671,
            local_ip="192.168.1.233")
    )
    file = open(file="config.json")
    json_configuration = json.load(file)
    ups1 = UPS(xknx=xknx, config_json=json_configuration['UPS1'])
    await ups1.initialize_from_configuration()
    ups1.print_initialization()


asyncio.run(main())
