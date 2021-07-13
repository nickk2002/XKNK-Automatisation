import asyncio
import json

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType

from core.ups import UPS


async def telegram_received_cb(telegram):
    print("Telegram received: {0}".format(telegram))


async def main():
    xknx = XKNX(
        daemon_mode=True,
        connection_config=ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip="192.168.100.71", gateway_port=3671,
            local_ip="192.168.100.73")
    )
    with open("configuration/config.json") as f:
        json_configuration = json.load(f)
    ups1 = UPS(xknx=xknx, name='UPS1', config_json=json_configuration)
    # # ups2 = UPS(xknx=xknx, name='UPS2', config_json=json_configuration['UPS2'])
    # # ups3 = UPS(xknx=xknx, name='UPS3', config_json=json_configuration['UPS3'])
    #
    await ups1.initialize()
    # # await ups2.initialize()
    # # await ups3.initialize()

    await xknx.start()
    await xknx.stop()


asyncio.run(main())

# cd "/home/pi/Desktop/Calugareni/XKNK-Automatisation" && python manager.py &
