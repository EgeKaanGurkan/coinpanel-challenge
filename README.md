## CoinPanel Backend Challenge

This repository contains 2 clients:
* `basic_cli`: is put into the Docker image and it is a simple listener that
connects to the Binance trade websocket stream and prints out a warning if the price exceeds
the specified threshold. To run this client;
  1. Specify the symbols and thresholds you want to listen to within the `.env` file in the directory
  2. Either build and run the Dockerfile or use the [docker-compose](https://docs.docker.com/compose/) command.
     1. To build and run manually:
        ```bash
        docker build . -t coinpanel-challenge && \
        dokcker run --env-file=.env coinpanel-challenge
        ```
     2. To run using `docker-compose` \
        ```bash
        docker-compose up
        ```
* `async_cli`: is a more advanced version of the `basic_cli` that demonstrates how `asyncio` can be used to 
create a more efficient and real-time updatable client that listens to the websocket. This could be extended to an asynchronous
Flask application to create a real-time websocket listener. 
To run it;
    ```bash
    pip install websockets && \
    python3 async_cli.py
    ```