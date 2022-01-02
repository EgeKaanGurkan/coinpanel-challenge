import json
import os
import sys
import websockets
import asyncio


def get_unique_id():
    num = 0
    while True:
        yield num
        num += 1


async def subscribe_to_channels(ws, channel_names):
    msg = {
        "method": "SUBSCRIBE",
        "params": channel_names,
        "id": next(get_unique_id())
    }
    msg = json.dumps(msg)
    await ws.send(msg)


async def ws_listen(symbols_and_thresholds: list, ws_queue: asyncio.Queue):
    base_url = "wss://stream.binance.com:9443/ws"
    async with websockets.connect(base_url) as ws:
        channel_names = [i[0] for i in symbols_and_thresholds]
        await subscribe_to_channels(ws, channel_names)
        while 1:
            socket_response = json.loads(await ws.recv())
            await ws_queue.put(socket_response)


async def worker(symbols_and_thresholds: list, ws_queue: asyncio.Queue):
    while 1:
        next_response = await ws_queue.get()
        try:
            price = float(next_response["p"])
            symbol = next_response["s"].lower()
        except KeyError:
            continue

        for item in symbols_and_thresholds:
            if item[0].split("@")[0] == symbol and price > float(item[1]):
                print(f"Threshold exceeded for {symbol.upper()} [Price: {price}, Threshold: {item[1]}]")


async def async_main():
    ws_queue = asyncio.Queue()

    tasks = [asyncio.create_task(ws_listen(symbols_and_thresholds, ws_queue))]
    [tasks.append(asyncio.create_task(worker(symbols_and_thresholds, ws_queue))) for _ in range(3)]

    await asyncio.gather(*tasks)


if __name__ == '__main__':

    symbols = os.getenv("SYMBOLS")
    if symbols is None:
        print("Please set the SYMBOLS environment variable. (ex: btcusdt,ltcusdt)")
        sys.exit(1)

    thresholds = os.getenv("THRESHOLDS")
    if thresholds is None:
        print("Please set the THRESHOLDS environment variable. (ex: 4000,3000)")
        sys.exit(1)

    symbols = [symbol.strip() + "@trade" for symbol in symbols.split(",")]
    thresholds = [threshold.strip() for threshold in thresholds.split(",")]

    if len(symbols) != len(thresholds):
        print(f"The number of symbols ({len(symbols)}) and thresholds {len(thresholds)} need to be the same")

    symbols_and_thresholds = list(zip(symbols, thresholds))

    print("Listening with symbols and thresholds:")
    [print(f"{i[0]}: {i[1]}$") for i in symbols_and_thresholds]

    asyncio.run(async_main())
