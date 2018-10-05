# -*- coding: utf-8 -*-
import json
import os
import re
import time
import urllib

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request

from WeiboSpider.items import WeiboDataItem, RepostItem
from WeiboSpider.db.dao import UserOper


class WeiboSpider(scrapy.Spider):
    name = 'weibo'
    allowed_domains = ['weibo.com']

    domain_pattern = re.compile("\$CONFIG\['domain'\]='(\d+)'")
    uid_pattern = re.compile("\$CONFIG\['oid'\]='(\d+)'")
    name_pattern = re.compile("\$CONFIG\['onick'\]='(.+)'")
    page_pattern = re.compile(
        '<script>FM.view\({"ns":"pl.content.homeFeed.index","domid":"(Pl_Official_MyProfileFeed.+?)",".+?"html":(.+?)}\)</script>')

    weibo_url = 'https://weibo.com/p/{}{}/home?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page={}#feedtop'
    ajax_url = 'https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain={}&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page={}&pagebar={}&pl_name={}&id={}{}&script_uri=/p/{}{}/home&feed_type=0&pre_page={}&domain_op={}&__rnd={}'

    def start_requests(self):
        users = UserOper.get_user_ids()
        start_urls = (self.weibo_url.format(user.domian, user.uid, 1) for user in users)
        for url in start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        '''
        解析微博页面
        :param response:
        :return:
        '''
        # TODO 移除最外层捕获异常
        try:
            # json解析出错,字符串里面的"没有转义
            pl_name, html = response.selector.re(self.page_pattern)
            domain, uid, name = self.get_base_info(response)
            cur_time = int(time.time() * 1000)
            try:
                page = re.findall('&page=(\d+)', response.url)[0]
            except:
                page = 1

            yield from self.get_weibo_data(domain, uid, html, response)

            'https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100306&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=3&pagebar=0&pl_name=Pl_Official_MyProfileFeed__24&id=1003061192329374&script_uri=/p/1003061192329374/home&feed_type=0&pre_page=3&domain_op=100306&__rnd=1515074319033'
            'https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain={}&is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page={}&pagebar={}&pl_name={}&id={}{}&script_uri=/p/{}{}/home&feed_type=0&pre_page={}&domain_op={}&__rnd={}'
            url1 = self.ajax_url.format(domain, page, 0, pl_name, domain, uid, domain, uid, page, domain, cur_time)
            url2 = self.ajax_url.format(domain, page, 1, pl_name, domain, uid, domain, uid, page, domain,
                                        cur_time + 1000)
            yield Request(url1, meta={'domain': domain, 'uid': uid}, callback=self.parse_ajax_page)
            yield Request(url2, meta={'domain': domain, 'uid': uid}, callback=self.parse_ajax_page)
        except Exception as e:
            self.logger.exception(e)

    def parse_ajax_page(self, response):
        data = json.loads(response.body_as_unicode())
        html = data['data']
        domain = response.meta['domain']
        uid = response.meta['uid']
        yield from self.get_weibo_data(domain, uid, html, response)

    def get_weibo_data(self, domian, uid, html, response):
        # 需要登录才能爬取下一页链接，直接用domain和uid拼接出下一页链接，避免因cookies过期获取不到下一页链接
        soup = BeautifulSoup(html, 'html.parser')
        wb_list = soup.select('.WB_feed_type')
        print('*********************')
        try:
            for wb in wb_list:
                weibodataItem = WeiboDataItem()
                isforward = wb.get('isforward')
                weibodataItem['is_origin'] = 0 if isforward else 1
                mid = wb.get('mid')
                wb_info = wb.select_one('.WB_detail > .WB_info > .W_fb')
                user_id = re.findall('id=(\d+)', wb_info.get('usercard'))[0]
                user_name = wb_info.text
                weibodataItem['weibo_id'] = mid
                weibodataItem['uid'] = user_id
                weibodataItem['user_name'] = user_name

                wb_from = wb.select_one('.WB_detail > .WB_from')
                time_str = wb_from.select_one('a[node-type="feed_list_item_date"]')
                weibodataItem['create_time'] = time_str.get('title')
                weibo_url = 'https://weibo.com' + time_str.get('href')
                weibodataItem['weibo_url'] = weibo_url
                links = wb_from.select('a')
                weibodataItem['device'] = links[1].text if links and len(links) > 1 else None

                imgs = ['https:' + img.get('src').replace('thumb150', 'mw690').replace('wx1', 'wx3') for img in
                        wb.select('.WB_detail > .WB_media_wrap .media_box ul > li img') if img.get('src')]
                weibodataItem['weibo_img'] = '\n'.join(imgs) if imgs else None
                # TODO 视频链接无数据
                video = wb.select_one('.WB_detail > .WB_media_wrap .media_box .WB_video')
                video_sources = video.get('video-sources') if video else None
                try:
                    if video_sources:
                        video_src = urllib.parse.unquote(re.findall('fluency=(.+)=http', video_sources)[0])
                        weibodataItem['weibo_video'] = urllib.parse.unquote(video_src)
                except Exception as e:
                    self.logger.exception(e)
                    pass
                repost_num = wb.select_one('.WB_feed_handle .WB_handle .ficon_forward + em').text
                comment_num = wb.select_one('.WB_feed_handle .WB_handle .ficon_repeat + em').text
                praise_num = wb.select_one('.WB_feed_handle .WB_handle .ficon_praised + em').text
                weibodataItem['repost_num'] = re.findall('\d+', repost_num)[0] if re.findall('\d+', repost_num) else 0
                weibodataItem['comment_num'] = re.findall('\d+', comment_num)[0] if re.findall('\d+',
                                                                                               comment_num) else 0
                weibodataItem['praise_num'] = re.findall('\d+', praise_num)[0] if re.findall('\d+', praise_num) else 0

                wb_text = wb.select_one('.WB_detail > .WB_text')
                # TODO 表情无法存入数据库
                # content = wb_text.text.strip()
                content = self.get_text(str(wb_text))
                extend = 1 if '展开全文' in content else 0
                if extend:
                    # headers = response.request.headers
                    # full_content = self.get_full_content(mid, headers)
                    # content = full_content if full_content else content
                    url = 'https://weibo.com/p/aj/mblog/getlongtext?ajwvr=6&mid={}&__rnd={}'.format(mid, int(
                        time.time() * 1000))
                    yield Request(url, meta={'item': weibodataItem}, callback=self.parse_full_content)
                else:
                    weibodataItem['weibo_content'] = content

                    print(weibodataItem)
                    yield weibodataItem

                if isforward:
                    repostItem = RepostItem()
                    repostItem['weibo_id'] = mid
                    repostItem['root_weibo_id'] = wb.get('omid')
                    repostItem['uid'] = user_id
                    repostItem['user_name'] = user_name
                    repostItem['weibo_url'] = weibo_url

                    parent_info = wb.select_one('.WB_detail > .WB_feed_expand .WB_info .W_fb')
                    if parent_info:  # 判断原微博是否被删除
                        repostItem['parent_uid'] = re.findall('id=(\d+)', parent_info.get('usercard'))[0]
                        repostItem['parent_user_name'] = parent_info.text

                        yield repostItem
        except Exception as e:
            self.logger.error('微博数据解析出错')
            self.logger.exception(e)
            error_dir = self.settings.get('ERROR_DIR', '.')
            with open(os.path.join(error_dir, '{}.html'.format(int(time.time() * 1000))), 'wb') as f:
                f.write(response.body)
        next_page = soup.select_one('.next')
        if next_page:
            cur_page = re.findall('\d+', soup.select_one('a[action-data*=currentPage]').text)[0]
            next_url = self.weibo_url.format(domian, uid, int(cur_page) + 1)
            yield Request(next_url, callback=self.parse)

    def parse_full_content(self, response):
        '''
        # 获取微博展开全文
        :param response:
        :return:
        '''
        weibodataItem = response.meta['item']
        try:
            data = json.loads(response.body_as_unicode())
            html = data['data']['html']
            soup = BeautifulSoup(self.get_text(html), 'lxml')
            weibodataItem['weibo_content'] = soup.text
        except Exception as e:
            self.logger.exception(e)
        yield weibodataItem

    def get_text(self, html):
        text = re.sub(r'<img.+?alt="(.+?)".+?>', r'\1', html)
        soup1 = BeautifulSoup(text, 'lxml')
        return soup1.text.strip()

    def get_base_info(self, response):
        '''
        获取域名、用户id、昵称
        :param response:
        :return:
        '''
        domain = response.selector.re_first(self.domain_pattern)
        uid = response.selector.re_first(self.uid_pattern)
        name = response.selector.re_first(self.name_pattern)
        return domain, uid, name
