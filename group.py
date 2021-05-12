class Group:
    def __init__(self, name: str, max_current: float, channel_list: list):
        self.name = name
        self.max_current = max_current
        self.channel_list = channel_list

    def __str__(self):
        output = f"{self.name} are curentul maxim admis {self.max_current} si canalele {self.channel_list}"
        return output