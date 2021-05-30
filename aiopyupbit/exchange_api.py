# !/usr/bin/python
# -*- coding: utf-8 -*-
import math
import re
import uuid
import hashlib
import jwt
from urllib.parse import urlencode
if __name__ == "__main__":
    from request_api import _send_get_request, _send_post_request, _send_delete_request
else:
    from .request_api import _send_get_request, _send_post_request, _send_delete_request


def get_tick_size(price: float or int,
                  method="floor") -> float:
    """KRW Market order price unit 

    Args:
        price (float or int): Price
        method (str, optional): Order price calculate method. Defaults to "floor".

    Returns:
        float: Price adjusted in units of KRW market order price 
    """
    if method == "floor":
        func = math.floor
    elif method == "round":
        func = round
    else:
        func = math.ceil

    if price >= 2000000:
        return func(price / 1000) * 1000
    elif price >= 1000000:
        return func(price / 500) * 500
    elif price >= 500000:
        return func(price / 100) * 100
    elif price >= 100000:
        return func(price / 50) * 50
    elif price >= 10000:
        return func(price / 10) * 10
    elif price >= 1000:
        return func(price / 5) * 5
    elif price >= 100:
        return func(price / 1) * 1
    elif price >= 10:
        return func(price / 0.1) / 10
    else:
        return func(price / 0.01) / 100


class Upbit:
    def __init__(self, access: str, secret: str):
        self.access = access
        self.secret = secret

    async def _request_headers(self, query: dict = None) -> dict:
        """Get request header

        Args:
            query (dict, optional): Header query. Defaults to None.

        Returns:
            dict: Included authorization request header
        """
        payload = {"access_key": self.access,
                   "nonce": str(uuid.uuid4())}
        if query:
            m = hashlib.sha512()
            m.update(urlencode(query, doseq=True).replace(
                "%5B%5D=", "[]=").encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = "SHA512"

        jwt_token = jwt.encode(payload=payload,
                               key=self.secret,
                               algorithm="HS256")
        return {"Authorization": f'Bearer {jwt_token}'}

    async def check_authentication(self) -> tuple or bool:
        """Check account's access/secret key authentication

        Returns:
            tuple or bool: bool if auth_success else tuple
        """
        url = 'https://api.upbit.com/v1/accounts'
        headers = await self._request_headers()
        body, _ = await _send_get_request(url, headers=headers)
        return (False, body['error']['message']) if 'error' in body else (True, None)

    async def get_balances(self, contain_req: bool = False) -> tuple or list:
        """Get account's all possession 

        Args:
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or list: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/accounts"
        headers = await self._request_headers()
        body, remain = await _send_get_request(url, headers=headers)
        return (body, remain) if contain_req else body

    async def get_balance(self, ticker: str = "KRW", contain_req: bool = False) -> tuple or float:
        """Check the balance of a specific coin/won 

        Args:
            ticker (str, optional): Coin's ticker. Defaults to "KRW".
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or float: tuple if contain_req else float
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        body, remain = await self.get_balances(contain_req=True)
        for x in body:
            if x['currency'] == ticker:
                balance = float(x['balance'])
                return (balance, remain) if contain_req else balance

    async def get_balance_t(self, ticker: str = 'KRW', contain_req: bool = False) -> tuple or float:
        """Check the balance of a specific coin/won(balance + locked)

        Args:
            ticker (str, optional): Coin's ticker. Defaults to 'KRW'.
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or float: tuple if contain_req else float
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        body, remain = await self.get_balances(contain_req=True)
        for x in body:
            if x['currency'] == ticker:
                balance = float(x['balance'])
                locked = float(x['locked'])
                return (balance + locked, remain) if contain_req else (balance + locked)

    async def get_avg_buy_price(self, ticker: str = 'KRW', contain_req: bool = False) -> tuple or float:
        """Average buying price of a specific coin/won 

        Args:
            ticker (str, optional): Coin's ticker. Defaults to 'KRW'.
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or float: tuple if contain_req else float
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        body, remain = await self.get_balances(contain_req=True)
        for x in body:
            if x['currency'] == ticker:
                avg_buy_price = float(x['avg_buy_price'])
                return (avg_buy_price, remain) if contain_req else avg_buy_price

    async def get_amount(self, ticker: str, contain_req: bool = False) -> tuple or float:
        """The purchase amount of a specific coin/won 

        Args:
            ticker (str): Coin's ticker
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or float: tuple if contain_req else float
        """
        ticker = (lambda x: x.split('-')[1] if '-' in x else x)(ticker)
        body, remain = await self.get_balances(contain_req=True)
        amount = 0
        for x in body:
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
        return (amount, remain) if contain_req else amount

    async def get_chance(self, ticker: str, contain_req: bool = False) -> tuple or list:
        """Check the availability information for each market

        Args:
            ticker (str): Coin's ticker.
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or list: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders/chance"
        data = {"market": ticker}
        headers = await self._request_headers(data)
        body, remain = await _send_get_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def get_order(self,
                        ticker_or_uuid: str,
                        state: str = 'wait',
                        kind: str = 'normal',
                        contain_req: bool = False) -> tuple or list:
        """Get order information list

        Args:
            ticker_or_uuid (str): Coin's ticker or UUID
            state (str, optional): Order status (wait, done, cancel). Defaults to 'wait'.
            kind (str, optional): Order type (normal, watch). Defaults to 'normal'.
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or list: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders"
        # TODO : states, identifiers 관련 기능 추가 필요
        p = re.compile(r"^\w+-\w+-\w+-\w+-\w+$")
        # 정확히는 입력을 대문자로 변환 후 다음 정규식을 적용해야 함
        # - r"^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$"
        if len(p.findall(ticker_or_uuid)) > 0:
            data = {'uuid': ticker_or_uuid}
        else:
            data = {'market': ticker_or_uuid,
                    'state': state,
                    'kind': kind,
                    'order_by': 'desc'}
        headers = await self._request_headers(data)
        body, remain = await _send_get_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def get_individual_order(self,
                                   uuid: str,
                                   contain_req: bool = False) -> tuple or dict:
        """Get individual order information

        Args:
            uuid (str): Order UUID
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        # TODO : states, uuids, identifiers 관련 기능 추가 필요
        url = "https://api.upbit.com/v1/order"
        data = {'uuid': uuid}
        headers = await self._request_headers(data)
        body, remain = await _send_get_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def cancel_order(self,
                           uuid: str,
                           contain_req: bool = False) -> tuple or dict:
        """Order cancellation

        Args:
            uuid (str): UUID of the return value of the order function
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/order"
        data = {"uuid": uuid}
        headers = await self._request_headers(data)
        body, remain = await _send_delete_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def buy_limit_order(self,
                              ticker: str,
                              price: float,
                              volume: float,
                              contain_req: bool = False) -> tuple or dict:
        """Limitation buy order

        Args:
            ticker (str): Coin's ticker
            price (float): The order price
            volume (float): The order quantity
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "bid",
                "volume": str(volume),
                "price": str(price),
                "ord_type": "limit"}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def buy_market_order(self,
                               ticker: str,
                               price: float,
                               contain_req: bool = False) -> tuple or dict:
        """Market buy order

        Args:
            ticker (str): Coin's ticker
            price (float): The order price
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "bid",
                "price": str(price),
                "ord_type": "price"}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def sell_limit_order(self,
                               ticker: str,
                               price: float,
                               volume: float,
                               contain_req: bool = False) -> tuple or dict:
        """Limitation sell order

        Args:
            ticker (str): Coin's ticker
            price (float): The order price
            volume (float): The order quantity
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "ask",
                "volume": str(volume),
                "price": str(price),
                "ord_type": "limit"}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def sell_market_order(self,
                                ticker: str,
                                volume: float,
                                contain_req: bool = False) -> tuple or dict:
        """Market sell order

        Args:
            ticker (str): Coin's ticker
            volume (float): The order quantity
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else list
        """
        url = "https://api.upbit.com/v1/orders"
        data = {"market": ticker,
                "side": "ask",
                "volume": str(volume),
                "ord_type": "market"}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def get_individual_withdraw_order(self, uuid: str, currency: str, contain_req: bool = False) -> tuple or dict:
        """Cash withdrawal

        Args:
            uuid (str): Withdrawal UUID
            currency (str): Currency code
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        url = "https://api.upbit.com/v1/withdraw"
        data = {"uuid": uuid,
                "currency": currency}
        headers = await self._request_headers(data)
        body, remain = await _send_get_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def withdraw_coin(self,
                            currency: float,
                            amount: float,
                            address: str,
                            secondary_address: str = 'None',
                            transaction_type: str = 'default',
                            contain_req: bool = False) -> tuple or dict:
        """Coin withdrawal

        Args:
            currency (float): Currency code
            amount (float): Order price
            address (str): Withdrawal wallet address
            secondary_address (str, optional): Secondary withdrawal address (only for required coins). Defaults to 'None'.
            transaction_type (str, optional): Withdrawal type. Defaults to 'default'.
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        url = "https://api.upbit.com/v1/withdraws/coin"
        data = {"currency": currency,
                "amount": amount,
                "address": address,
                "secondary_address": secondary_address,
                "transaction_type": transaction_type}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def withdraw_cash(self, amount: str, contain_req: bool = False) -> tuple or dict:
        """Cash withdrawal

        Args:
            amount (str): Withdrawal amount
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        url = "https://api.upbit.com/v1/withdraws/krw"
        data = {"amount": amount}
        headers = await self._request_headers(data)
        body, remain = await _send_post_request(url, headers=headers, data=data)
        return (body, remain) if contain_req else body

    async def get_deposit_withdraw_status(self, contain_req: bool = False) -> tuple or dict:
        """Deposit and withdrawal status 

        Args:
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        url = "https://api.upbit.com/v1/status/wallet"
        headers = await self._request_headers()
        body, remain = await _send_get_request(url, headers=headers)
        return (body, remain) if contain_req else body

    async def get_api_key_list(self, contain_req: bool = False) -> tuple or dict:
        """API key list lookup 

        Args:
            contain_req (bool, optional): Contain send request limitation information to return. Defaults to False.

        Returns:
            tuple or dict: tuple if contain_req else dict
        """
        url = "https://api.upbit.com/v1/api_keys"
        headers = await self._request_headers()
        body, remain = await _send_get_request(url, headers=headers)
        return (body, remain) if contain_req else body
