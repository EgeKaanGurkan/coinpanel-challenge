import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import os

import websockets

subscribed_channels = []

conn: websockets


def get_unique_id():
    num = 0
    while True:
        yield num
        num += 1


def build_sub_msg(channel_names):
    msg = {
        "method": "SUBSCRIBE",
        "params": channel_names,
        "id": next(get_unique_id())
    }
    return json.dumps(msg)


def build_unsub_msg(channel_names):
    msg = {
        "method": "UNSUBSCRIBE",
        "params": channel_names,
        "id": next(get_unique_id())
    }
    return json.dumps(msg)


def build_subbed_dict(subbed_chan, price_threshold=None):
    return {
        "chan": subbed_chan,
        "price_threshold": price_threshold,
        "alert": {
            "alerted": False,
            "alerted_price": 0
        },
        "max_price": 0,
        "last_price": 0
    }


async def check_alerts(subscribed_channels, price, symbol):
    for chan in subscribed_channels:
        if float(price) > chan["price_threshold"] and f"{symbol.lower()}@trade" == chan["chan"]:
            chan["alert"]["alerted"] = True
            chan["last_price"] = float(price)
            if float(price) > chan["max_price"]:
                chan["max_price"] = float(price)


async def print_alerted(subscribed_channels):
    if len(subscribed_channels) == 0:
        return
    else:
        print("Price threshold exceeded: ")
        for chan in subscribed_channels:
            if chan["alert"]["alerted"]:
                print(
                    f"- {chan['chan']}\n\tThreshold: {chan['price_threshold']}\n\tLast Price: {chan['last_price']}\n\tMax Price: {chan['max_price']}")
    print()


async def print_subbed(subscribed_channels):
    if len(subscribed_channels) == 0:
        return
    else:
        print("Subscribed channels: ")
        for chan in subscribed_channels:
            print(
                f"- {chan['chan']}\n\tThreshold: {chan['price_threshold']}")
    print()


async def remove_from_subbed_list(subscribed_channels: list, channel_names: list):
    for i, chan in enumerate(subscribed_channels):
        if len(channel_names) == 1:
            if chan["chan"] == channel_names[0]:
                del subscribed_channels[i]
                continue
        if chan["chan"] in channel_names:
            del subscribed_channels[i]


async def ainput(subscribed_channels: list, prompt: str = ''):
    with ThreadPoolExecutor(1, 'ainput') as executor:
        while 1:
            os.system("clear")
            await asyncio.gather(print_alerted(subscribed_channels))
            operation = int(await asyncio.get_event_loop().run_in_executor(executor, input, prompt))
            if operation not in range(1, 4):
                os.system("clear")
                print("Please pick a valid command.")

            elif operation == 1:
                os.system("clear")
                await asyncio.gather(print_alerted(subscribed_channels))
                channel_names = await asyncio.get_event_loop().run_in_executor(executor, input,
                                                                               "Please enter the channel name(s) to subscribe to (comma separated): ")
                channel_names = [i for i in channel_names.split(",") if i != ""]
                sub_msg = build_sub_msg(channel_names)
                for chan in channel_names:
                    price_threshold = float(await asyncio.get_event_loop().run_in_executor(executor, input,
                                                                                           f"Price threshold to watch for {chan}: "))
                    subscribed_channels.append(build_subbed_dict(chan, price_threshold))
                await conn.send(sub_msg)

            elif operation == 2:
                os.system("clear")
                await print_subbed(subscribed_channels)
                channel_names = await asyncio.get_event_loop().run_in_executor(executor, input,
                                                                               "Please enter the channel name to "
                                                                               "unsubscribe from: ")
                channel_names = [i for i in channel_names.split(",") if i != ""]
                unsub_msg = build_unsub_msg(channel_names)
                await conn.send(unsub_msg)
                await asyncio.gather(remove_from_subbed_list(subscribed_channels, channel_names))

            elif operation == 3:
                continue


async def listen_ws(stream_queue: asyncio.Queue, subscribed_channels):
    url = "wss://stream.binance.com:9443/ws"
    async with websockets.connect(url) as ws:
        global conn
        conn = ws
        # await conn.send(build_sub_msg(["ltcusdt@trade"]))
        # subscribed_channels.append(build_subbed_dict("ltcusdt@trade", 0))
        while 1:
            socket_response = json.loads(await ws.recv())
            await stream_queue.put(socket_response)


async def send(message):
    global conn
    await conn.send(message)


async def handle_queue(stream_queue: asyncio.Queue, subscribed_channels: list):
    while 1:
        next_response = await stream_queue.get()
        try:
            price = next_response["p"]
            symbol = next_response["s"]
        except KeyError as e:
            continue
        await asyncio.gather(check_alerts(subscribed_channels, price, symbol))
        stream_queue.task_done()


async def main():
    stream_queue = asyncio.Queue(maxsize=100000)
    tasks = [asyncio.create_task(ainput(subscribed_channels,
                                        "1. Subscribe to symbols\n2. Unsubscribe from symbols\n3. "
                                        "Refresh\nChoose operation: ")),
             asyncio.create_task(listen_ws(stream_queue, subscribed_channels))]

    num_workers = 3
    for _ in range(num_workers):
        tasks.append(asyncio.create_task(handle_queue(stream_queue, subscribed_channels)))

    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    os.system("clear")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        exit(0)
    except RuntimeWarning:
        pass
