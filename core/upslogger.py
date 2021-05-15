class UPSLogger:

    def __init__(self, ups):
        self.ups = ups
        self.config = ups.config

    def print_initialization(self):
        print("Afisam grupele citite din JSON")
        for group in self.config.group_list:
            print(group)
        print("Afisam device-urile, adica sensor, binary sensor si switch")
        for device in self.ups.xknx.devices:
            print(device.get_name())

    def print_debug_information(self):
        total_current_ups = 0
        sum_group = []  # suma curentilor pe grup UPS

        for group in self.config.group_list:
            total_group = 0  # initializare suma curentilor pe grup UPS
            for channel in group.channel_list:
                sensor = channel.sensor
                if sensor.resolve_state() is not None:
                    total_current_ups += sensor.resolve_state()
                    total_group += sensor.resolve_state()
            sum_group.append(total_group)
        print("===============")
        for index in range(1, len(self.config.channel_list)):
            print(self.config.channel_list[index], end=' ')
        print()
        print("Total UPS", total_current_ups)
        print("Grupe UPS", sum_group)
