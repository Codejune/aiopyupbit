# !/usr/bin/python
# -*- coding: utf-8 -*-
import re
import aiohttp
if __name__ == "__main__":
    from errors import (raise_error, RemainingReqParsingError)
else:
    from .errors import (raise_error, RemainingReqParsingError)


async def is_request_success(code: int):
    if 200 <= code < 400:
        return True
    else:
        return False


async def _parse_remaining_req(remaining_req: str):
    """Parse the request limit data of the API

    Args:
        remaining_req (str): "group=market; min=573; sec=9" 

    Returns:
        dict: {'group': 'market', 'min': 573, 'sec': 2}
    """
    try:
        p = re.compile(r"group=([a-z\-]+); min=([0-9]+); sec=([0-9]+)")
        m = p.search(remaining_req)
        return {'group': m.group(1), 'min': int(m.group(2)), 'sec': int(m.group(3))}
    except:
        raise RemainingReqParsingError()


async def _call_public_api(url: str, **kwargs):
    """Call get type api

    Args:
        url (str): REST API url

    Returns:
        tuple: (data, req_limit_info) 
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=kwargs) as response:
            if await is_request_success(response.status):
                remain = await _parse_remaining_req(response.headers.get('Remaining-Req'))
                body = await response.json()
                return body, remain
            else:
                await raise_error(response)


async def _send_post_request(url, headers=None, data=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if await is_request_success(response.status):
                remain = await _parse_remaining_req(response.headers.get('Remaining-Req'))
                body = await response.json()
                return body, remain
            else:
                await raise_error(response)


async def _send_get_request(url, headers=None, data=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, data=data) as response:
            if await is_request_success(response.status):
                remain = await _parse_remaining_req(response.headers.get('Remaining-Req'))
                body = await response.json()
                return body, remain
            else:
                await raise_error(response)


async def _send_delete_request(url, headers=None, data=None):
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers, data=data) as response:
            if await is_request_success(response.status):
                remain = await _parse_remaining_req(response.headers.get('Remaining-Req'))
                body = await response.json()
                return body, remain
            else:
                await raise_error(response)
