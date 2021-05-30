# !/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import pandas as pd
from pandas._libs.tslibs import Timestamp
from pandas.core.frame import DataFrame
if __name__ == "__main__":
    from request_api import _call_public_api
else:
    from .request_api import _call_public_api


def convert_time_format(to: None or str or Timestamp) -> datetime.datetime:
    """Convert time to datetime format

    Args:
        to (None or str or Timestamp): Target time

    Returns:
        datetime.datetime: Converted time
    """
    if not to:
        to = datetime.datetime.now()
    elif isinstance(to, str):
        to = pd.to_datetime(to).to_pydatetime()
    elif isinstance(to, pd._libs.tslibs.timestamps.Timestamp):
        to = to.to_pydatetime()

    if not to.tzinfo:
        to = to.astimezone()
    else:
        to = to.astimezone(datetime.timezone.utc)
    return to.strftime("%Y-%m-%d %H:%M:%S")


async def get_tickers(fiat: str = "ALL",
                      contain_name: bool = False,
                      contain_req: bool = False) -> tuple or list:
    """Upbit ticker lookup

    Args:
        fiat (str, optional): Fiat (KRW, BTC, USDT). Defaults to "ALL".
        contain_name (bool, optional): Contain ticker's korean, english name to return. Defaults to False.
        contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

    Returns:
        tuple or list: tuple if contain_req else list
    """
    url = "https://api.upbit.com/v1/market/all"
    body, remain = await _call_public_api(url)
    if fiat != 'ALL':
        tickers = [x for x in body if x['market'].startswith(fiat)]
    if not contain_name:
        tickers = [x['market'] for x in tickers]
    return (tickers, remain) if contain_req else tickers


async def get_url_ohlcv(interval: str) -> str:
    """A function that returns the url for an ohlcv request 

    Args:
        interval (str): "day", "minute1", "minute3", "minute5", "week", "month"
    Returns:
        str: API url 
    """
    if interval in ["day", "days"]:
        return "https://api.upbit.com/v1/candles/days"
    elif interval in ["minute1", "minutes1"]:
        return "https://api.upbit.com/v1/candles/minutes/1"
    elif interval in ["minute3", "minutes3"]:
        return "https://api.upbit.com/v1/candles/minutes/3"
    elif interval in ["minute5", "minutes5"]:
        return "https://api.upbit.com/v1/candles/minutes/5"
    elif interval in ["minute10", "minutes10"]:
        return "https://api.upbit.com/v1/candles/minutes/10"
    elif interval in ["minute15", "minutes15"]:
        return "https://api.upbit.com/v1/candles/minutes/15"
    elif interval in ["minute30", "minutes30"]:
        return "https://api.upbit.com/v1/candles/minutes/30"
    elif interval in ["minute60", "minutes60"]:
        return "https://api.upbit.com/v1/candles/minutes/60"
    elif interval in ["minute240", "minutes240"]:
        return "https://api.upbit.com/v1/candles/minutes/240"
    elif interval in ["week",  "weeks"]:
        return "https://api.upbit.com/v1/candles/weeks"
    elif interval in ["month", "months"]:
        return "https://api.upbit.com/v1/candles/months"
    else:
        return "https://api.upbit.com/v1/candles/days"


async def get_ohlcv(ticker: str = "KRW-BTC",
                    interval: str = "day",
                    count: int = 200,
                    to: str = None,
                    contain_req: bool = False) -> tuple or DataFrame:
    """Candle data request 

    Args:
        ticker (str, optional): Coin's ticker. Defaults to "KRW-BTC".
        interval (str, optional): Candle data interval. Defaults to "day".
        count (int, optional): Candle data count. Defaults to 200.
        to (str, optional): End time to candle data. Defaults to None.
        contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

    Returns:
        tuple or DataFrame: tuple if contain_req else DataFrame
    """
    url = await get_url_ohlcv(interval=interval)
    time = convert_time_format(to)
    body, remain = await _call_public_api(url,
                                          market=ticker,
                                          count=count,
                                          to=time)
    df = pd.DataFrame(body,
                      columns=['candle_date_time_kst',
                               'opening_price',
                               'high_price',
                               'low_price',
                               'trade_price',
                               'candle_acc_trade_volume',
                               'candle_acc_trade_price'])
    df = df.rename(columns={"candle_date_time_kst": "time",
                            "opening_price": "open",
                            "high_price": "high",
                            "low_price": "low",
                            "trade_price": "close",
                            "candle_acc_trade_volume": "volume",
                            "candle_acc_trade_price": "value"})
    df = df.sort_index(ascending=False)
    return (df, remain) if contain_req else df


async def get_daily_ohlcv_from_base(ticker: str = "KRW-BTC",
                                    base: int = 0,
                                    contain_req: bool = False) -> tuple or DataFrame:
    """Daily candle data request

    Args:
        ticker (str, optional): Coin's ticker. Defaults to "KRW-BTC".
        base (int, optional): Resampling start index. Defaults to 0.
        contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

    Returns:
        tuple or DataFrame: tuple if contain_req else DataFrame
    """
    if contain_req:
        df, remain = await get_ohlcv(ticker,
                                     interval="minute60",
                                     contain_req=contain_req)
    else:
        df = await get_ohlcv(ticker,
                             interval="minute60",
                             contain_req=contain_req)
    df = df.resample('24H', base=base).agg({'open': 'first',
                                            'high': 'max',
                                            'low': 'min',
                                            'close': 'last',
                                            'volume': 'sum'})
    return (df, remain) if contain_req else df


async def get_current_price(ticker: str = "KRW-BTC",
                            contain_etc: bool = False,
                            contain_req: bool = False) -> float or dict or tuple:
    """Current price information request

    Args:
        ticker (str, optional): Coin's ticker. Defaults to "KRW-BTC".
        contain_etc (bool, optional): Contain other information to return. Defaults to False.
        contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

    Returns:
        float or dict or tuple: tuple if contain_req else float or dict
    """
    url = "https://api.upbit.com/v1/ticker"
    body, remain = await _call_public_api(url, markets=ticker)
    if isinstance(ticker, str) or (isinstance(ticker, list) and len(ticker) == 1):
        ret = body[0] if contain_etc else body[0]['trade_price']
    else:
        ret = body if contain_etc else {
            x['market']: x['trade_price'] for x in body}
    return (ret, remain) if contain_req else ret


async def get_orderbook(tickers: str = "KRW-BTC",
                        contain_req: bool = False) -> tuple or list:
    """Orderbook information request

    Args:
        tickers (str, optional): Coin's ticker. Defaults to "KRW-BTC".
        contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

    Returns:
        tuple or list: tuple if contain_req else list
    """
    url = "https://api.upbit.com/v1/orderbook"
    body, remain = await _call_public_api(url, markets=tickers)
    return (body, remain) if contain_req else body
