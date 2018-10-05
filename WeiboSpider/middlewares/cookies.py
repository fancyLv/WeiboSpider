# -*- coding: utf-8 -*-
# @File    : cookies.py
# @Author  : LVFANGFANG
# @Time    : 2018/10/3 0003 23:00
# @Desc    :

import os

import redis
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message

from WeiboSpider.db.redis_db import Cookies
from WeiboSpider.login.cookies import init_cookies, update_cookies, remove_cookies


class CookiesMiddleware(RetryMiddleware):
    def __init__(self, settings, crawler):
        RetryMiddleware.__init__(self, settings)
        self.rconn = redis.Redis(host=crawler.settings.get('REDIS_HOST', 'localhost'),
                                 port=crawler.settings.get('REDIS_PORT', 6379))
        init_cookies()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings, crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        res = Cookies.fetch_cookies()
        while not res:
            init_cookies()
            res = Cookies.fetch_cookies()
        if res:
            request.cookies = res['cookies']
            request.meta['account_name'] = res['name']

    def process_response(self, request, response, spider):
        # TODO 重定向链接各种状态解析
        if response.status in [300, 301, 302, 303]:
            try:
                redirect_url = response.headers["location"]
                print(redirect_url)
                spider.logger.debug('redirect_url:' + redirect_url)
                if "login.weibo" in redirect_url or "login.sina" in redirect_url:  # Cookie失效
                    spider.logger.warning("One Cookie need to be updating...")
                    update_cookies(request.meta['account_name'])
                elif "weibo.cn/security" in redirect_url:  # 账号被限
                    spider.logger.warning("One Account is locked! Remove it!")
                    remove_cookies(request.meta['account_name'])
                # elif "weibo.cn/pub" in redirect_url:
                #     spider.logger.warning(
                #         "Redirect to 'http://weibo.cn/pub'!( Account:%s )" % request.meta["accountText"].split("--")[0])
                reason = response_status_message(response.status)
                return self._retry(request, reason, spider) or response  # 重试
            except Exception as e:
                raise IgnoreRequest
        elif response.status in [403, 414]:
            spider.logger.error("%s! Stopping..." % response.status)
            os.system("pause")
        else:
            return response

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
