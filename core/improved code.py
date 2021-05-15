import asyncio
import json

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType

from core.ups import UPS


async def main():
    xknx = XKNX(
        daemon_mode=True,
        connection_config=ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip="192.168.1.52", gateway_port=3671,
            local_ip="192.168.1.233")
    )
    with open("configuration/config.json") as f:
        json_configuration = json.load(f)
    ups1 = UPS(xknx=xknx, name='UPS1', config_json=json_configuration['UPS1'])
    await ups1.initialize()

asyncio.run(main())
