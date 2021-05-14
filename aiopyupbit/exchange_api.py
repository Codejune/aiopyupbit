# !/usr/bin/python
# -*- coding: utf-8 -*-
import re
import uuid
import hashlib
import jwt
from urllib.parse import urlencode
if __name__ == "__main__":
    from request_api import _send_get_request, _send_post_request, _send_delete_request
    from errors import TooManyRequests, UpbitError
else:
    from .request_api import _send_get_request, _send_post_request, _send_delete_request
    from .errors import TooManyRequests, UpbitError

# 원화 마켓 주문 가격 단위
# https://docs.upbit.com/docs/market-info-trade-price-detail


def get_tick_size(price):
    if price >= 2000000:
        tick_size = round(price / 1000) * 1000
    elif price >= 1000000:
        tick_size = round(price / 500) * 500
    elif price >= 500000:
        tick_size = round(price / 100) * 100
    elif price >= 100000:
        tick_size = round(price / 50) * 50
    elif price >= 10000:
        tick_size = round(price / 10) * 10
    elif price >= 1000:
        tick_size = round(price / 5) * 5
    elif price >= 100:
        tick_size = round(price / 1) * 1
    elif price >= 10:
        tick_size = round(price / 0.1) / 10
    else:
        tick_size = round(price / 0.01) / 100
    return tick_size


class Upbit:
    def __init__(self, access, secret):
        self.access = access
        self.secret = secret

    async def _request_headers(self, query=None):
        payload = {"access_key": self.access,
                   "nonce": str(uuid.uuid4())}
        if query != None:
            m = hashlib.sha512()
            m.update(urlencode(query).encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = "SHA512"

        jwt_token = jwt.encode(payload=payload,
                               key=self.secret,
                               algorithm="HS256")
        authorization_token = f'Bearer {jwt_token}'
        headers = {"Authorization": authorization_token}
        return headers

    async def check_authentication(self):
        url = 'https://api.upbit.com/v1/accounts'
        headers = await self._request_headers()
        result = await _send_get_request(url, headers=headers)
        result = result[0]
        return (False, result['error']['message']) if 'error' in result else (True, None)


    async def get_balances(self, contain_req: bool = False):
        """
        전체 계좌 조회
        :param contain_req: Remaining-Req 포함여부
        :return: 내가 보유한 자산 리스트
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        url = "https://api.upbit.com/v1/accounts"
        headers = await self._request_headers()
        result, limits = await _send_get_request(url, headers=headers)
        return (result, limits) if contain_req else result


    async def get_balance(self, ticker: str = "KRW", contain_req: bool = False):
        """
        특정 코인/원화의 잔고를 조회하는 메소드
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 제외)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        balances, limits = await self.get_balances(contain_req=True)
        balance = 0
        for x in balances:
            if x['currency'] == ticker:
                balance = float(x['balance'])
                break
        return (balance, limits) if contain_req else balance


    async def get_balance_t(self, ticker: str = 'KRW', contain_req: bool = False):
        """
        특정 코인/원화의 잔고 조회(balance + locked)
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 포함)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        balances, limits = await self.get_balances(contain_req=True)
        balance = 0
        locked = 0
        for x in balances:
            if x['currency'] == ticker:
                balance = float(x['balance'])
                locked = float(x['locked'])
                break
        return (balance + locked, limits) if contain_req else (balance + locked)


    async def get_avg_buy_price(self, ticker: str = 'KRW', contain_req: bool = False):
        """
        특정 코인/원화의 매수평균가 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 매수평균가
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        balances, limits = await self.get_balances(contain_req=True)
        avg_buy_price = 0
        for x in balances:
            if x['currency'] == ticker:
                avg_buy_price = float(x['avg_buy_price'])
                break
        return (avg_buy_price, limits) if contain_req else avg_buy_price


    async def get_amount(self, ticker: str, contain_req: bool = False):
        """
        특정 코인/원화의 매수금액 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드 (ALL 입력시 총 매수금액 조회)
        :param contain_req: Remaining-Req 포함여부
        :return: 매수금액
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        balances, limits = await self.get_balances(contain_req=True)
        amount = 0
        for x in balances:
            if x['currency'] == 'KRW':
                continue
            avg_buy_price = float(x['avg_buy_price'])
            balance = float(x['balance'])
            locked = float(x['locked'])
            if ticker == 'ALL':
                amount += avg_buy_price * (balance + locked)
            elif x['currency'] == ticker:
                amount = avg_buy_price * (balance + locked)
                break
        return (amount, limits) if contain_req else amount


    async def get_chance(self, ticker: str, contain_req: bool = False):
        """
        마켓별 주문 가능 정보를 확인.
        :param ticker:
        :param contain_req: Remaining-Req 포함여부
        :return: 마켓별 주문 가능 정보를 확인
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        url = "https://api.upbit.com/v1/orders/chance"
        data = {"market": ticker}
        headers = await self._request_headers(data)
        result, limits = await _send_get_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def buy_limit_order(self,
                              ticker: str,
                              price: float,
                              volume: float,
                              contain_req: bool = False):
        """
        지정가 매수
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "bid",
                "volume": str(volume),
                "price": str(price),
                "ord_type": "limit"}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def buy_market_order(self,
                               ticker: str,
                               price: float,
                               contain_req: bool = False):
        """
        시장가 매수
        :param ticker: ticker for cryptocurrency
        :param price: KRW
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,  # market ID
                "side": "bid",  # buy
                "price": str(price),
                "ord_type": "price"}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def sell_market_order(self,
                                ticker: str,
                                volume: float,
                                contain_req: bool = False):
        """
        시장가 매도 메서드
        :param ticker: 가상화폐 티커
        :param volume: 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,  # ticker
                "side": "ask",  # sell
                "volume": str(volume),
                "ord_type": "market"}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def sell_limit_order(self,
                               ticker: str,
                               price: float,
                               volume: float,
                               contain_req: bool = False):
        """
        지정가 매도
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "ask",
                "volume": str(volume),
                "price": str(price),
                "ord_type": "limit"}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def cancel_order(self,
                           uuid: str,
                           contain_req: bool = False):
        """
        주문 취소
        :param uuid: 주문 함수의 리턴 값중 uuid
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/order"
        data = {"uuid": uuid}
        headers = await self._request_headers(data)
        result, limits = await _send_delete_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def get_order(self,
                        ticker_or_uuid: str,
                        state: str = 'wait',
                        kind: str = 'normal',
                        contain_req: bool = False):
        """
        주문 리스트 조회
        :param ticker: market
        :param state: 주문 상태(wait, done, cancel)
        :param kind: 주문 유형(normal, watch)
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, identifiers 관련 기능 추가 필요
        p = re.compile(r"^\w+-\w+-\w+-\w+-\w+$")
        # 정확히는 입력을 대문자로 변환 후 다음 정규식을 적용해야 함
        # - r"^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$"
        is_uuid = len(p.findall(ticker_or_uuid)) > 0
        url = "https://api.upbit.com/v1/orders"
        if is_uuid:
            data = {'uuid': ticker_or_uuid}
        else:
            data = {'market': ticker_or_uuid,
                    'state': state,
                    'kind': kind,
                    'order_by': 'desc'}
        headers = await self._request_headers(data)
        result, limits = await _send_get_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def get_individual_order(self,
                                   uuid: str,
                                   contain_req: bool = False):
        """
        주문 리스트 조회
        :param uuid: 주문 id
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, uuids, identifiers 관련 기능 추가 필요
        url = "https://api.upbit.com/v1/order"
        data = {'uuid': uuid}
        headers = await self._request_headers(data)
        result, limits = await _send_get_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def withdraw_coin(self,
                            currency: float,
                            amount: float,
                            address: str,
                            secondary_address: str = 'None',
                            transaction_type: str = 'default',
                            contain_req: bool = False):
        """
        코인 출금
        :param currency: Currency symbol
        :param amount: 주문 가격
        :param address: 출금 지갑 주소
        :param secondary_address: 2차 출금주소 (필요한 코인에 한해서)
        :param transaction_type: 출금 유형
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/withdraws/coin"
        data = {"currency": currency,
                "amount": amount,
                "address": address,
                "secondary_address": secondary_address,
                "transaction_type": transaction_type}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def withdraw_cash(self, amount: str, contain_req: bool = False):
        """
        현금 출금
        :param amount: 출금 액수
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/withdraws/krw"
        data = {"amount": amount}
        headers = await self._request_headers(data)
        result, limits = await _send_post_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result


    async def get_individual_withdraw_order(self, uuid: str, currency: str, contain_req: bool = False):
        """
        현금 출금
        :param uuid: 출금 UUID
        :param txid: 출금 TXID
        :param currency: Currency 코드
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        url = "https://api.upbit.com/v1/withdraw"
        data = {"uuid": uuid,
                "currency": currency}
        headers = await self._request_headers(data)
        result, limits = await _send_get_request(url, headers=headers, data=data)
        return (result, limits) if contain_req else result
