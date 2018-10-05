# -*- coding: utf-8 -*-
# @File    : redis_db.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 17:19
# @Desc    :
import redis
import json
import datetime

from WeiboSpider.util.log import storage, login
from WeiboSpider.settings import REDIS_HOST, REDIS_PORT, REDIS_PARAMS

cookies_con = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PARAMS['password'])
cookie_expire_time = 23


class Cookies:
    @classmethod
    def store_cookies(cls, name, cookies):
        pickled_cookies = json.dumps(
            {'cookies': cookies, 'loginTime': datetime.datetime.now().timestamp()})
        cookies_con.hset('account', name, pickled_cookies)
        cls.push_in_queue(name)

    @classmethod
    def push_in_queue(cls, name):
        for i in range(cookies_con.llen('account_queue')):
            lname = cookies_con.lindex('account_queue', i).decode('utf-8')
            if lname and lname == name:
                return
        cookies_con.rpush('account_queue', name)

    @classmethod
    def fetch_cookies(cls):
        for i in range(cookies_con.llen('account_queue')):
            name = cookies_con.lpop(('account_queue')).decode('utf-8')
            cookies_str = cls.get_cookies(name)
            if not cookies_str:
                continue
            else:
                if cls.check_cookies_timeout(cookies_str):
                    cls.delete_cookies(name)
                    continue
                cookies_con.rpush('account_queue', name)
                account_cookies = {}
                account_cookies['cookies'] = json.loads(cookies_str)['cookies']
                account_cookies['name'] = name
                return account_cookies
        return None

    @classmethod
    def check_cookies_timeout(cls, cookies):
        if not cookies:
            return True
        if isinstance(cookies, bytes):
            cookies = cookies.decode('utf-8')
        cookies = json.loads(cookies)
        login_time = datetime.datetime.fromtimestamp(cookies['loginTime'])
        if datetime.datetime.now() - login_time > datetime.timedelta(hours=cookie_expire_time):
            login.warning('The account has been expired')
            return True
        return False

    @classmethod
    def delete_cookies(cls, name):
        cookies_con.hdel('account', name)
        return True

    @classmethod
    def get_cookies(cls, name):
        result = cookies_con.hget('account', name)
        return result.decode('utf-8') if result else result

    @classmethod
    def get_cookies_num(cls):
        return cookies_con.hlen('account')
