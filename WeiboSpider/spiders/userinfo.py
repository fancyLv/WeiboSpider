# -*- coding: utf-8 -*-
import json
import os
import re
import time

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request

from WeiboSpider.db.dao import SeedsOper
from WeiboSpider.items import UserItem, RelationItem


class UserinfoSpider(scrapy.Spider):
    name = 'userinfo'
    allowed_domains = ['weibo.com']

    base_url = 'https://weibo.com/p/{}{}/info?mod=pedit_more'
    fans_url = 'https://weibo.com/p/{}{}/follow?relate=fans&page={}#Pl_Official_HisRelation__60'
    follow_url = 'https://weibo.com/p/{}{}/follow?page={}#Pl_Official_HisRelation__60'

    domain_pattern = re.compile("\$CONFIG\['domain'\]='(\d+)'")
    uid_pattern = re.compile("\$CONFIG\['oid'\]='(\d+)'")
    name_pattern = re.compile("\$CONFIG\['onick'\]='(.+)'")
    info_pattern = re.compile('<script>FM.view\(({"ns":"","domid":"Pl_Official_PersonalInfo__\d+".+?)\)</script>')
    enterprice_info = re.compile('<script>FM.view\(({"ns":".+?","domid":"Pl_Core_UserInfo__6".+?)\)</script>')
    enterprice_desc = re.compile('<script>FM.view\(({"ns":".+?","domid":"Pl_Core_T3Simpletext__30".+?)\)</script>')
    num_pattern = re.compile('<script>FM.view\(({"ns":"","domid":"Pl_Core_T8CustomTriColumn.+?)\)</script>')
    head_pattern = re.compile('<script>FM.view\(({"ns":"pl.header.head.index".+?)\)</script>')
    relation_pattern = re.compile('<script>FM.view\(({"ns":"pl.content.followTab.index".+?)\)</script>')

    seeds = SeedsOper.get_seeds_ids()
    start_urls = ['https://weibo.com/p/{}{}/info?mod=pedit_more'.format('100505', seed.uid) for seed in seeds]
    # start_urls = ['https://weibo.com/p/1005051904178193/info?mod=pedit_more']

    def parse(self, response):
        domain, uid, name = self.get_base_info(response)
        print((domain, uid, name))
        if domain in ('103505', '100306', '100605', '100505'):
            if domain == '100505':
                # 个人主页
                yield self.parse_user_info(response)
            else:
                # 微博页面,需要重新请求个人主页
                home = self.base_url.format(domain, uid)
                yield Request(url=home, callback=self.parse_user)
        else:
            # 100606,100206 官方微博，直接就是微博页面
            item = self.parse_enterprise_info(response)
            yield Request(url=f'https://weibo.com/{uid}/about', meta={'item': item},
                          callback=self.parse_enterprise_desc)
        fans = self.fans_url.format(domain, uid, 1)
        follow = self.follow_url.format(domain, uid, 1)
        yield Request(url=fans, callback=self.parse_relation)
        yield Request(url=follow, callback=self.parse_relation)

    def parse_user(self, response):
        yield self.parse_user_info(response)

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

    def parse_user_info(self, response):
        '''
        解析个人信息
        :param response:
        :return:
        '''
        userItem = self.get_detail_info(response)
        userItem['domain'], userItem['uid'], userItem['name'] = self.get_base_info(response)
        userItem['verify_type'], userItem['verify_info'], userItem['head_img'] = self.get_verify_info(response)
        userItem['follows_num'], userItem['fans_num'], userItem['wb_num'] = self.get_nums(response)
        userItem['level'] = self.get_level(response)
        return userItem

    def get_detail_info(self, response):
        '''
        :param response:
        :return:
        '''
        # TODO 简介有表情，存储失败
        userItem = UserItem()
        data = json.loads(response.selector.re_first(self.info_pattern))
        html = data['html']
        soup = BeautifulSoup(html, 'lxml')
        infos = soup.select('.WB_cardwrap')
        try:
            for info in infos:
                title = info.select_one('.WB_cardtitle_b').text
                li = info.select('.li_1')
                if '基本信息' in title:
                    for i in li:
                        pt_title = i.select_one('.pt_title').text
                        pt_detail = i.select_one('.pt_detail').text if i.select_one('.pt_detail') else None
                        if '所在地' in pt_title:
                            userItem['location'] = pt_detail
                        elif '性别' in pt_title:
                            userItem['gender'] = pt_detail
                        elif '生日' in pt_title:
                            userItem['birthday'] = pt_detail
                        elif '简介' in pt_title:
                            userItem['description'] = pt_detail.strip()
                        elif '注册时间' in pt_title:
                            userItem['register_time'] = pt_detail.strip()
                elif '联系信息' in title:
                    # 联系信息需要登录才能爬取
                    userItem['contact_info'] = '\n'.join([i.text for i in li])
                elif '工作信息' in title:
                    userItem['work_info'] = '\n'.join(
                        [i.text.replace('\t', '').replace('\r\n', '').replace('\n', '').strip() for i in li])
                elif '教育信息' in title:
                    userItem['education_info'] = '\n'.join(
                        [i.text.replace('\t', '').replace('\r\n', '').replace('\n', '').strip() for i in li])
                elif '标签信息' in title:
                    userItem['tags'] = ';'.join(re.split('[\s]+', li[0].select_one('.pt_detail').text.strip()))
        except Exception as e:
            self.logger.error('用户信息解析出错')
            self.logger.exception(e)
            error_dir = self.settings.get('ERROR_DIR', '.')
            with open(os.path.join(error_dir, '{}.html'.format(int(time.time() * 1000))), 'w') as f:
                f.write(html)

        return userItem

    def parse_enterprise_info(self, response):
        '''
        解析官方微博账号的信息
        :param response:
        :return:
        '''
        userItem = UserItem()
        userItem['domain'], userItem['uid'], userItem['name'] = self.get_base_info(response)
        userItem['follows_num'], userItem['fans_num'], userItem['wb_num'] = self.get_nums(response)
        userItem['verify_type'], userItem['verify_info'], userItem['head_img'] = self.get_verify_info(response)
        userItem['level'] = self.get_level(response)

        data = json.loads(response.selector.re_first(self.enterprice_info))
        html = data['html']
        soup = BeautifulSoup(html, 'lxml')
        info = soup.select('.S_line2 > .item_text')
        userItem['register_time'] = re.findall('[\d-]+', info[0].text.strip())[0]
        userItem['industry_category'] = info[1].text.replace('行业类别', '').strip()

        return userItem

    def parse_enterprise_desc(self, response):
        item = response.meta['item']
        data = json.loads(response.selector.re_first(self.enterprice_desc))
        html = data['html']
        soup = BeautifulSoup(html, 'lxml')
        item['description'] = soup.select_one('.p_txt').text.strip()
        yield item

    def get_nums(self, response):
        '''
        获取关注、粉丝、微博数量
        :param response:
        :return:
        '''
        data = json.loads(response.selector.re_first(self.num_pattern))
        html = data['html']
        soup = BeautifulSoup(html, 'lxml')
        nums = soup.select('strong')
        follows_num = nums[0].text if nums and len(nums) > 0 else 0
        fans_num = nums[1].text if nums and len(nums) > 1 else 0
        wb_num = nums[2].text if nums and len(nums) > 2 else 0
        return follows_num, fans_num, wb_num

    def get_verify_info(self, response):
        '''
        获取认证类型,认证信息,头像
        :param response:
        :return: 认证类型(0代表没有认证，1代表个人认证，2代表企业认证),认证信息,头像图片地址
        '''
        data = json.loads(response.selector.re_first(self.head_pattern))
        html = data['html']
        if 'icon_pf_approve_co' in html:
            verify_type = 2
        elif 'icon_pf_approve' in html:
            verify_type = 1
        else:
            verify_type = 0
        soup = BeautifulSoup(html, 'lxml')
        verify_info = soup.select_one('.pf_intro').get('title') if verify_type == 1 or verify_type == 2 else None
        head_img = 'http:' + soup.select_one('.photo_wrap img').get('src')
        return verify_type, verify_info, head_img

    def get_level(self, response):
        html = response.body_as_unicode()
        pattern = '<span>Lv.(.*?)<\\\/span>'
        rs = re.search(pattern, html)
        if rs:
            return rs.group(1)
        else:
            return 0

    def parse_relation(self, response):
        '''
        获取关注id、粉丝id
        :param response:
        :return:
        '''
        url = response.url
        uid = re.findall('/p/\d{6}(\d+)', url)[0]
        relation_type = 2 if 'fans' in url else 1
        data = json.loads(response.selector.re_first(self.relation_pattern))
        html = data['html']
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('.follow_list .S_txt1'):
            # TODO 粉丝信息解析异常
            try:
                follow_id = re.findall('id=(\d+)', item.get('usercard'))[0]
            except Exception as e:
                error_dir = self.settings.get('ERROR_DIR', '.')
                with open(os.path.join(error_dir, '{}.html'.format(int(time.time() * 1000))), 'w') as f:
                    f.write(html)
                self.logger.exception(e)
                continue
            relationItem = RelationItem()
            relationItem['uid'] = uid
            relationItem['type'] = relation_type
            relationItem['follow_or_fans_id'] = follow_id
            yield relationItem
            yield Request(self.base_url.format('100505', follow_id), callback=self.parse)
        next_page = soup.select_one('.next')
        next_url = next_page.get('href')
        if not next_page.get('page-limited') and next_url:
            yield Request('https://weibo.com' + next_url, callback=self.parse_relation)
