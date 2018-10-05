# -*- coding: utf-8 -*-
# @File    : cookies.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 16:21
# @Desc    :
import os
import time

from WeiboSpider.db.dao import AccountsOper
from WeiboSpider.db.redis_db import Cookies
from WeiboSpider.login.login import get_session
from WeiboSpider.util.log import login


def init_cookies():
    accounts = AccountsOper.get_account_info()
    for account in accounts:
        if not Cookies.get_cookies(account.name):
            get_session(account.name, account.password)
            time.sleep(3)
    cookieNum = Cookies.get_cookies_num()
    login.info("The num of the cookies is %s" % cookieNum)
    if not cookieNum:
        login.warning('Stopping...')
        os.system('pause')


def update_cookies(name):
    account = AccountsOper.get_account_info_by_name(name)
    if account:
        session = get_session(account.name, account.password)
        if session:
            login.warning("The cookie of %s has been updated successfully!" % name)
        else:
            login.warning("The cookie of %s updated failed! Remove it!" % name)


def remove_cookies(name):
    Cookies.delete_cookies(name)
    AccountsOper.freeze_account(name, 1)
    cookieNum = Cookies.get_cookies_num()
    login.info("The num of the cookies is %s" % cookieNum)
    if not cookieNum:
        login.warning('Stopping...')
        os.system('pause')


if __name__ == '__main__':
    # init_cookies()
    # res = Cookies.fetch_cookies()
    # print(res)
    accounts = AccountsOper.get_account_info()
    for account in accounts:
        a = Cookies.get_cookies(account.name)
        if not a:
            print(True)