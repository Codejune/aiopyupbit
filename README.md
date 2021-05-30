aiopyupbit
==========

aiopyupbit is python wrapper for upbit API for asyncio and Python 
which is base on [pyupbit](https://github.com/sharebook-kr/pyupbit)


Installation
------------

Installing: `pip install aiopyupbit`

Usage
-----

aiopyupbit syntax strives to be similar to [pyupbit](https://github.com/sharebook-kr/pyupbit).

``` python
import asyncio
import aiopyupbit

async def main():
    print(await aiopyupbit.get_tickers())
    print(await aiopyupbit.get_current_price("KRW-BTC"))
    print(await aiopyupbit.get_current_price(["KRW-BTC", "KRW-XRP"]))
    print(await aiopyupbit.get_ohlcv("KRW-BTC"))
    ...

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main)
```
About
-----

Some features are not currently implemented: 
* WebSocketManager class 

Issues
------
Please report any issues via [github issues](https://github.com/codejune/aiopyupbit/issues)