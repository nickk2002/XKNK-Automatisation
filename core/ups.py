import json
from asyncio.locks import Lock

from termcolor import colored
from xknx import XKNX
from xknx.devices import BinarySensor, Switch, Sensor

from configuration.upsconfig import UPSConfiguration
from core.upslogger import UPSLogger


class UPS:
    def __init__(self, xknx: XKNX, name: str, config_json: json):
        self.xknx = xknx
        self.name = name
        self.config = UPSConfiguration(ups=self, config_json=config_json)

        self.logger = UPSLogger(ups=self)
        self.logger.print_groups()

        self.maxim_allowed_current = self.config.global_minim

        self.lestare_delestare_lock = Lock()
        self.prezenta_tensiune_lock = Lock()

        self.initialization_finished = False

        self.add_callbacks_to_devices()

    def all_channels_intialized(self) -> bool:
        for channel in self.config.channel_list:
            if channel.sensor.resolve_state() is None:
                return False
        return True

    # Callbacks #
    @staticmethod
    async def binary_sensor_update(binary_sensor: BinarySensor):
        print(f"Binary sensor {binary_sensor.name} is {binary_sensor.state}")

    @staticmethod
    async def switch_update(switch: Switch):
        print(f"The value of the {switch.name} is {switch.state}")

    async def sensor_update(self, sensor: Sensor):
        print("Sensor updated", sensor.name, sensor.resolve_state())

        if not self.all_channels_intialized():
            return
        if self.initialization_finished is False and self.all_channels_intialized():
            print(colored("All initialized!", 'green', attrs=['bold']))
            self.initialization_finished = True
        await self.lestare_delestare()

    async def prezenta_tensiune_update(self, binary_sensor: BinarySensor):
        async with self.prezenta_tensiune_lock:
            if binary_sensor.state == 0:
                self.maxim_allowed_current = self.config.global_minim
                print(f"Tensiunea maxima {self.name} =", self.maxim_allowed_current)
            else:
                self.maxim_allowed_current = self.config.global_minim
                print(f"Tensiunea maxima {self.name} =", self.maxim_allowed_current)
            await self.lestare_delestare()

    def add_callbacks_to_devices(self):
        for device in self.xknx.devices:
            if type(device) == type(Sensor):
                device.device_updated_cb = self.sensor_update
            elif type(device) == type(BinarySensor):
                device.device_updated_cb = self.binary_sensor_update
                if "tensiune" in device.name:
                    device.device_updated_cb = self.prezenta_tensiune_update
            elif type(device) == type(Switch):
                device.device_updated_cb = self.switch_update

    async def sync_devices(self):
        for device in self.xknx.devices:
            await device.sync()

    async def initialize(self):
        self.logger.print_initialization()
        await self.sync_devices()

    def get_maximum_current(self):
        return self.maxim_allowed_current

    async def lestare_delestare(self):
        async with self.lestare_delestare_lock:
            print("Lestare delestare")
            total_sum = 0

            for group in self.config.group_list:
                group_sum = 0
                for channel in group.channel_list:
                    switch = channel.switch
                    sensor = channel.sensor
                    binary_sensor = channel.binary_sensor

                    current_value = sensor.resolve_state()
                    estimated_current_value = self.config.estimated_value_channels[channel.index]

                    if current_value is None:
                        colored(f"Am gasit None {channel.index} !!!", 'red')
                        return
                    if channel.binary_sensor.state == 1:
                        # daca ma aflu pe un canal deschis verific sa nu depaseasca limitele
                        if group_sum + current_value >= group.max_current or \
                                total_sum + current_value >= self.get_maximum_current():
                            await channel.switch.set_off()
                            if group_sum + current_value >= group.max_current:
                                print(
                                    colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de grup", "grey",
                                            attrs=['bold']))
                            elif group_sum + current_value >= self.get_maximum_current():
                                print(colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de totala",
                                              "grey",
                                              attrs=['bold']))
                            else:
                                print(colored("Avem o problema la sincronizare sigurr", 'red', attrs=['bold']))
                            self.logger.print_debug_information()
                        else:
                            total_sum += current_value
                            group_sum += current_value
                    elif binary_sensor.state == 0:
                        if group_sum + estimated_current_value < group.max_current and \
                                total_sum + estimated_current_value < self.get_maximum_current():
                            await switch.set_on()
                            print(colored(f"Inchid canalul {switch.name} Pentru ca e ok", "grey", attrs=['bold']))
                            self.logger.print_debug_information()
                            group_sum += estimated_current_value
                            total_sum += estimated_current_value
