# !/usr/bin/python
# -*- coding: utf-8 -*-
# UPbit Quatation (시세 조회) API
import datetime
import pandas as pd
from .request_api import _call_public_api
if __name__ == "__main__":
    from request_api import _call_public_api
    from errors import TooManyRequests, UpbitError
else:
    from .request_api import _call_public_api
    from .errors import TooManyRequests, UpbitError


async def get_tickers(fiat: str = "ALL",
                      contain_name: bool = False,
                      contain_req: bool = False):
    """
    마켓 코드 조회 (업비트에서 거래 가능한 마켓 목록 조회)
    :param fiat: "ALL", "KRW", "BTC", "USDT"
    :param limit_info: 요청수 제한 리턴
    :return:
    """
    url = "https://api.upbit.com/v1/market/all"
    contents, limits = await _call_public_api(url)
    tickers = None
    if isinstance(contents, list):
        tickers = [x for x in contents if x['market'].startswith(
            fiat)] if fiat != 'ALL' else contents
        tickers = [x['market']
                    for x in tickers] if not contain_name else tickers
    return (tickers, limits) if contain_req else tickers



async def get_url_ohlcv(interval: str):
    """
    candle에 대한 요청 주소를 얻는 함수
    :param interval: day(일봉), minute(분봉), week(주봉), 월봉(month)
    :return: candle 조회에 사용되는 url
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
                    contain_req: bool = False):
    """
    캔들 조회
    :return:
    """
    url = await get_url_ohlcv(interval=interval)
    if to == None:
        to = datetime.datetime.now()
    elif isinstance(to, str):
        to = pd.to_datetime(to).to_pydatetime()
    elif isinstance(to, pd._libs.tslibs.timestamps.Timestamp):
        to = to.to_pydatetime()

    to = to.astimezone() if to.tzinfo is None else to
    to = to.astimezone(datetime.timezone.utc)
    to = to.strftime("%Y-%m-%d %H:%M:%S")
    contents, limits = await _call_public_api(url, market=ticker, count=count, to=to)

    df = pd.DataFrame(contents,
                        columns=['candle_date_time_kst',
                                'opening_price',
                                'high_price',
                                'low_price',
                                'trade_price',
                                'candle_acc_trade_volume'])
    df = df.rename(columns={"candle_date_time_kst": "time",
                            "opening_price": "open",
                            "high_price": "high",
                            "low_price": "low",
                            "trade_price": "close",
                            "candle_acc_trade_volume": "volume"})
    df = df.sort_index(ascending=False)
    return (df, limits) if contain_req else df



async def get_daily_ohlcv_from_base(ticker: str = "KRW-BTC", base: int = 0, contain_req: bool = False):
    """

    :param ticker:
    :param base:
    :return:
    """
    df, limits = await get_ohlcv(ticker, interval="minute60", contain_req=contain_req)
    df = df.resample('24H', base=base).agg({'open': 'first',
                                            'high': 'max',
                                            'low': 'min',
                                            'close': 'last',
                                            'volume': 'sum'})
    return (df, limits) if contain_req else df



async def get_current_price(ticker: str = "KRW-BTC", contain_req: bool = False):
    """
    최종 체결 가격 조회 (현재가)
    :param ticker:
    :return:
    """
    url = "https://api.upbit.com/v1/ticker"
    contents, limits = await _call_public_api(url, markets=ticker)
    ret = None
    if isinstance(ticker, list):
        ret = {}
        for content in contents:
            market = content['market']
            price = content['trade_price']
            ret[market] = price
    else:
        ret = contents[0]['trade_price']
    return (ret, limits) if contain_req else ret
 

async def get_orderbook(tickers: str = "KRW-BTC", contain_req: bool = False):
    '''
    호가 정보 조회
    :param tickers: 티커 목록을 문자열
    :return:
    '''
    url = "https://api.upbit.com/v1/orderbook"
    contents, limits = await _call_public_api(url, markets=tickers)
    return (contents, limits) if contain_req else contents
