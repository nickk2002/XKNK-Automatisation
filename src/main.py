import asyncio

from termcolor import colored
from xknx import XKNX
from xknx.devices import Sensor, Switch, BinarySensor
from xknx.io import ConnectionConfig, ConnectionType


async def binary_sensor_update(binary_sensor):
    print(f"Binary sensor {binary_sensor.name} is {binary_sensor.state}")


async def switch_update(switch):
    print(f"The value of the {switch.name} is {switch.state}")


T_UPS1 = 11
GLOBAL_MAXIM_UPS1 = 16
GLOBAL_MINIM_UPS1 = 5

LIMITA_GRUPA1 = 8
LIMITA_GRUPA2 = 10
LIMITA_GRUPA3 = 4.9

T_UPS2 = 11
GLOBAL_MINIM_UPS2 = 16
GLOBAL_MAXIM_UPS2 = 5

# canal = (binary_sensor,sensor,switch,indexCanal)
# grupa = contine canale
lista_grupe_totale = []  # combinatia intre o grupa si curentul maxim admis pe acea grupa
lista_curenti = []
#                      1  2  3    4   5     6     7   8
# current_estimat = [-1, 1, 1, 3, 3.5, 12.5, 12.5, 4.5, 1]
current_estimat = [-1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1]

lacat = asyncio.Lock()


async def lestare_delestare():
    async with lacat:
        print("Lestare delestare")
        suma_totala = 0

        for (group, group_limit) in lista_grupe_totale:
            suma_grupa = 0
            for (sensor, binary_sensor, switch, canal) in group:
                valoare_curent = sensor.resolve_state()
                curent_estimat_canal = current_estimat[canal]
                if valoare_curent is None:
                    colored(f"Am gasit None {canal} !!!", 'red')
                    return
                if binary_sensor.state == 1:
                    # daca ma aflu pe un canal deschis verific sa nu depaseasca limitele
                    # daca pe grupa este mai mare sau egal sau pe total e mai mare sau egal il inchid direct
                    if suma_grupa + valoare_curent >= group_limit or suma_totala + valoare_curent >= T_UPS1:
                        await switch.set_off()
                        if (suma_grupa + valoare_curent >= group_limit):
                            print(colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de grup", "grey",
                                          attrs=['bold']))
                        elif (suma_grupa + valoare_curent >= T_UPS1):
                            print(colored(f"Deschid canalul {switch.name} Pentru ca depaseste limita de totala", "grey",
                                          attrs=['bold']))
                        else:
                            print(colored("Avem o problema la sincronizare sigurr", 'red', attrs=['bold']))
                        print_sensor_state()
                    else:
                        suma_totala += valoare_curent
                        suma_grupa += valoare_curent
                elif binary_sensor.state == 0:
                    if suma_grupa + curent_estimat_canal < group_limit and suma_totala + curent_estimat_canal < T_UPS1:
                        await switch.set_on()
                        print(colored(f"Inchid canalul {switch.name} Pentru ca e ok", "grey", attrs=['bold']))
                        print_sensor_state()
                        suma_grupa += curent_estimat_canal
                        suma_totala += curent_estimat_canal


sensor_lock = asyncio.Lock()


async def prezenta_tensiune_update1(binary_sensor):
    global T_UPS1
    async with sensor_lock:
        if binary_sensor.state == 0:
            T_UPS1 = GLOBAL_MINIM_UPS1
            print("T UPS1 =", T_UPS1)
        else:
            T_UPS1 = GLOBAL_MAXIM_UPS1
            print("T UPS1 =", T_UPS1)
        await lestare_delestare()


async def prezenta_tensiune_update2(binary_sensor):
    global T_UPS2
    async with sensor_lock:
        if binary_sensor.state == 0:
            T_UPS2 = GLOBAL_MINIM_UPS2
            print("T UPS2 =", T_UPS2)
        else:
            T_UPS2 = GLOBAL_MAXIM_UPS2
            print("T UPS2 =", T_UPS2)
        await lestare_delestare()


print(T_UPS1)


def print_sensor_state():
    total_current_UPS = 0
    suma_grupa_UPS = []  # suma curentilor pe grup UPS
    stare_canale = [None] * 9

    for (grupa, maxGroup) in lista_grupe_totale:
        total_grupa_UPS = 0  # initializare suma curentilor pe grup UPS
        for (sensor, binary_sensor, switch, indexCanal) in grupa:
            if sensor.resolve_state() is not None:
                total_current_UPS += sensor.resolve_state()
                total_grupa_UPS += sensor.resolve_state()

            stare_canale[indexCanal] = binary_sensor.state
        suma_grupa_UPS.append(total_grupa_UPS)
    print()
    for index in range(1, len(stare_canale)):
        print(stare_canale[index], end=' ')
    print()
    print("Total UPS", total_current_UPS)
    print("Grupe UPS", suma_grupa_UPS)


initialized = False


# chemat de fiecare data cand s-a modificat valoarea unui senzor
async def sensor_update(sensor):
    global initialized
    print("Sensor update!!")
    # print(f"The value of the {sensor.name} is {sensor.resolve_state()}")

    # print("AAAAA ",xknx.devices[sensor.name].resolve_state())
    print_sensor_state()

    for s in lista_curenti:
        if s.resolve_state() is None:
            return
    if initialized is False:
        print(colored("All initialized!", 'green', attrs=['bold']))
        initialized = True
    await lestare_delestare()


async def initializare(xknx):
    global lista_grupe_totale, lista_curenti, initialized
    channels = [None]
    for i in range(1, 9):
        sensor = Sensor(
            xknx,
            name=f'Curent {i}',
            group_address_state=f'1/1/{i}',
            value_type='electric_current',
            device_updated_cb=sensor_update,

        )
        binary_sensor = BinarySensor(
            xknx,
            name=f'CH{i}_state',
            group_address_state=f'1/2/{i}',
            device_class='motion',
            device_updated_cb=binary_sensor_update,
        )
        switch = Switch(
            xknx,
            name=f'switch {i}',
            group_address=f'1/3/{i}',
            device_updated_cb=switch_update,
        )
        await switch.sync()
        await binary_sensor.sync()
        await sensor.sync()
        print(sensor.name, " ", sensor.resolve_state())
        xknx.devices.add(switch)
        xknx.devices.add(binary_sensor)
        xknx.devices.add(sensor)
        lista_curenti.append(sensor)
        channels.append((sensor, binary_sensor, switch, i))

    prezenta_tensiune1 = BinarySensor(
        xknx,
        name='Prezenta tensiune UPS 1',
        group_address_state='1/2/0',
        device_class='motion',
        device_updated_cb=prezenta_tensiune_update1,
    )
    prezenta_tensiune2 = BinarySensor(
        xknx,
        name='Prezenta tensiune UPS 2',
        group_address_state='1/2/22',
        device_class='motion',
        device_updated_cb=prezenta_tensiune_update2,
    )
    xknx.devices.add(prezenta_tensiune1)
    # xknx.devices.add(prezenta_tensiune2)

    await prezenta_tensiune1.sync()
    # await prezenta_tensiune2.sync()

    group1_UPS1 = [channels[1], channels[2], channels[3]]
    group2_UPS1 = [channels[4], channels[5], channels[6]]
    group3_UPS1 = [channels[7], channels[8]]
    group_total_UPS1 = channels[1:8]

    # group1_UPS2 = [channels[13], channels[14], channels[15]]
    # group2_UPS2 = [channels[16], channels[17], channels[18]]
    # group3_UPS2 = [channels[19], channels[20]]
    # group_total_UPS2 = channels[13:21]

    lista_grupe_totale = [(group1_UPS1, LIMITA_GRUPA1), (group2_UPS1, LIMITA_GRUPA2), (group3_UPS1, LIMITA_GRUPA3),
                          (group_total_UPS1, T_UPS1),
                          # (group1_UPS2, LIMITA_GRUPA1), (group2_UPS2, LIMITA_GRUPA2), (group3_UPS2, LIMITA_GRUPA3), (group_total_UPS2, T_UPS2)
                          ]


def device_updated_cb(device):
    print("Devide updated".format(device.name))


async def main():
    # device_updated_cb =device_updated_cb,
    xknx = XKNX(daemon_mode=True,

                connection_config=ConnectionConfig(
                    connection_type=ConnectionType.TUNNELING,
                    gateway_ip="192.168.1.52", gateway_port=3671,
                    local_ip="192.168.1.233")
                )
    await initializare(xknx)
    await xknx.start()
    await xknx.stop()


asyncio.run(main())
# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()
