'''Get server online status'''

import os
from datetime import datetime

import psutil

from webapi import app


@app.get("/")
async def ping():
    '''Test the server is online or not

    Returns:
        dict: Server status
            - time: Current time
            - status: Server status
            - load: Server load. [1min, 5min, 15min]
            - memory: Server memory usage. [used, total], in GB
            - disk: Server disk usage. [free, total], in GB

    Defined in: `webapi/routers/ping.py`
    '''

    # Get server load
    load = os.getloadavg()

    # Get memory usage
    memory_info = psutil.virtual_memory()
    memory_used = round(memory_info.used / 1024 / 1024 / 1024, 2)
    memory_total = round(memory_info.total / 1024 / 1024 / 1024, 2)

    # Get disk usage
    disk_info = psutil.disk_usage('/')
    disk_free = round(disk_info.free / 1024 / 1024 / 1024, 2)
    disk_total = round(disk_info.total / 1024 / 1024 / 1024, 2)

    return {
        "time": f"{datetime.now()}",
        "status": "online",
        "load": load,
        "memory": [memory_used, memory_total],
        "disk": [disk_free, disk_total]
    }
