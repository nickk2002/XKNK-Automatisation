class MyClass:

    def __init__(self, name, default_callback: callable):
        self.callbacks = []
        self.name = name

        self.single_callback = default_callback
        self.add_callback(self.single_callback)

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        self.callbacks.remove(callback)

    def call_everything(self):
        for callback in self.callbacks:
            callback(self)


class UsingClass:

    def __init__(self):
        self.device = MyClass(name="My class name", default_callback=self.callback_function)
        self.value = 10

    def callback_function(self, myclass: MyClass):
        print(myclass.name, self.value)

    def run(self):
        self.device.call_everything()


using_class = UsingClass()
using_class.run()
