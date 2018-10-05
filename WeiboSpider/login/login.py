# -*- coding: utf-8 -*-
# @File    : cookies.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 10:21
# @Desc    : 新浪微博登录

import base64
import binascii
import math
import os
import random
import re
import time
from urllib.parse import quote_plus

import requests
import rsa
from bs4 import BeautifulSoup

from WeiboSpider.util.yundama import code_verificate
from WeiboSpider.util.log import login
from WeiboSpider.db.redis_db import Cookies
from WeiboSpider.db.dao import AccountsOper

VERIFY_CODE_PATH = './{}{}.png'
YUMDAMA_USERNAME = 'username'
YUMDAMA_PASSWORD = 'password'
log_dir = os.path.dirname(os.path.dirname(__file__)) + '/logs'
log_path = os.path.join(log_dir, 'login.log')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Connection': 'keep-alive'
}


def get_pincode_url(pcid):
    size = 0
    url = "http://login.sina.com.cn/cgi/pin.php"
    pincode_url = '{}?r={}&s={}&p={}'.format(url, math.floor(random.random() * 100000000), size, pcid)
    return pincode_url


def get_img(url, name, retry_count):
    '''
    :param url:
    :param name:
    :param retry_count:
    :return:
    '''
    resp = requests.get(url, headers=headers, stream=True)
    pincode_name = VERIFY_CODE_PATH.format(name, retry_count)
    with open(pincode_name, 'wb') as f:
        f.write(resp.content)
    return pincode_name


def get_encodename(name):
    username_quote = quote_plus(str(name))
    username_base64 = base64.b64encode(username_quote.encode("utf-8"))
    return username_base64.decode("utf-8")


def get_server_data(su, session):
    pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
    pre_url = pre_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
    prelogin_url = pre_url + str(int(time.time() * 1000))
    pre_data_res = session.get(prelogin_url, headers=headers)

    sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))

    return sever_data


def get_password(password, servertime, nonce, pubkey):
    rsa_publickey = int(pubkey, 16)
    key = rsa.PublicKey(rsa_publickey, 65537)
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
    message = message.encode("utf-8")
    passwd = rsa.encrypt(message, key)
    passwd = binascii.b2a_hex(passwd)
    return passwd


def get_redirect(name, data, post_url, session):
    logining_page = session.post(post_url, data=data, headers=headers)
    login_loop = logining_page.content.decode("GBK")

    # 登录名或密码错误
    if 'retcode=101' in login_loop:
        login.error('invalid password for {}, please ensure your account and password'.format(name))
        AccountsOper.freeze_account(name, 2)
        return ''
    # 验证码错误
    if 'retcode=2070' in login_loop:
        login.error('invalid verification code')
        return 'pinerror'
    # 登录需要输入验证码
    if 'retcode=4049' in login_loop:
        login.warning('account {} need verification for login'.format(name))
        return 'login_need_pincode'

    if '正在登录' in login_loop or 'Signing in' in login_loop:
        pa = r'location\.replace\([\'"](.*?)[\'"]\)'
        return re.findall(pa, login_loop)[0]
    else:
        return ''


def login_no_pincode(name, password, session, server_data):
    post_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'

    servertime = server_data["servertime"]
    nonce = server_data['nonce']
    rsakv = server_data["rsakv"]
    pubkey = server_data["pubkey"]
    sp = get_password(password, servertime, nonce, pubkey)

    data = {
        'encoding': 'UTF-8',
        'entry': 'weibo',
        'from': '',
        'gateway': '1',
        'nonce': nonce,
        'pagerefer': "",
        'prelt': 67,
        'pwencode': 'rsa2',
        "returntype": "META",
        'rsakv': rsakv,
        'savestate': '7',
        'servertime': servertime,
        'service': 'miniblog',
        'sp': sp,
        'sr': '1920*1080',
        'su': get_encodename(name),
        'useticket': '1',
        'vsnf': '1',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack'
    }

    rs = get_redirect(name, data, post_url, session)

    return rs, None, '', session


def login_by_pincode(name, password, session, server_data, retry_count):
    post_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'

    servertime = server_data["servertime"]
    nonce = server_data['nonce']
    rsakv = server_data["rsakv"]
    pubkey = server_data["pubkey"]
    pcid = server_data['pcid']

    sp = get_password(password, servertime, nonce, pubkey)

    data = {
        'encoding': 'UTF-8',
        'entry': 'weibo',
        'from': '',
        'gateway': '1',
        'nonce': nonce,
        'pagerefer': "",
        'prelt': 67,
        'pwencode': 'rsa2',
        "returntype": "META",
        'rsakv': rsakv,
        'savestate': '7',
        'servertime': servertime,
        'service': 'miniblog',
        'sp': sp,
        'sr': '1920*1080',
        'su': get_encodename(name),
        'useticket': '1',
        'vsnf': '1',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'pcid': pcid
    }

    img_url = get_pincode_url(pcid)
    pincode_name = get_img(img_url, name, retry_count)
    verify_code, yundama_obj, cid = code_verificate(YUMDAMA_USERNAME, YUMDAMA_PASSWORD, pincode_name)
    # verify_code = input('请输入验证码：')
    data['door'] = verify_code
    rs = get_redirect(name, data, post_url, session)

    os.remove(pincode_name)
    # return rs, yundama_obj, cid, session
    return rs, None, None, session


def login_retry(name, password, session, ydm_obj, cid, rs='pinerror', retry_count=0):
    while rs == 'pinerror':
        ydm_obj.report(cid)
        retry_count += 1
        session = requests.Session()
        su = get_encodename(name)
        server_data = get_server_data(su, session)
        rs, yundama_obj, cid, session = login_by_pincode(name, password, session, server_data, retry_count)
    return rs, ydm_obj, cid, session


def do_login(name, password):
    session = requests.Session()
    su = get_encodename(name)
    server_data = get_server_data(su, session)

    if server_data['showpin']:
        rs, yundama_obj, cid, session = login_by_pincode(name, password, session, server_data, 0)
        if rs == 'pinerror':
            rs, yundama_obj, cid, session = login_retry(name, password, session, yundama_obj, cid)

    else:
        rs, yundama_obj, cid, session = login_no_pincode(name, password, session, server_data)
        if rs == 'login_need_pincode':
            session = requests.Session()
            su = get_encodename(name)
            server_data = get_server_data(su, session)
            rs, yundama_obj, cid, session = login_by_pincode(name, password, session, server_data, 0)

            if rs == 'pinerror':
                rs, yundama_obj, cid, session = login_retry(name, password, session, yundama_obj, cid)

    return rs, yundama_obj, cid, session


def get_session(name, password):
    url, yundama_obj, cid, session = do_login(name, password)

    if url != '':
        rs_cont = session.get(url, headers=headers)
        login_info = rs_cont.text

        u_pattern = r'"uniqueid":"(.*)",'
        m = re.search(u_pattern, login_info)
        if m and m.group(1):
            # check if account is valid
            check_url = 'http://weibo.com/2671109275/about'
            resp = session.get(check_url, headers=headers)

            if is_403(resp.text):
                login.error('account {} has been forbidden'.format(name))
                AccountsOper.freeze_account(name, 1)
                return None
            login.info('Login successful! The login account is {}'.format(name))
            Cookies.store_cookies(name, session.cookies.get_dict())
            return session

    login.info('login failed for {}'.format(name))
    return None


def is_403(html):
    if "['uid']" not in html and "['nick']" not in html and "['islogin']='1'" in html:
        return True

    if 'Sina Visitor System' in html:
        return True

    # verify code for search page
    # todo  solve the problem of verify_code when searching
    if 'yzm_img' in html and 'yzm_input' in html:
        return True

    soup = BeautifulSoup(html, 'html.parser')
    if soup.title:
        if '访问受限' in soup.title.text or '解冻' in soup.title.text:
            return True
        else:
            return False
    else:
        return False


if __name__ == '__main__':
    get_session('user', 'xxxxxx')
