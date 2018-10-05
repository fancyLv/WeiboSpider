# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from WeiboSpider.items import WeiboDataItem, RepostItem, UserItem, RelationItem
from WeiboSpider.db.dao import CommonOper, SeedsOper
from WeiboSpider.db.model import Seeds, WeiboData, WeiboRepost, User, Relationship
import datetime


class WeibospiderPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, WeiboDataItem):
            weiboData = WeiboData(weibo_id=item.get('weibo_id'),
                                  uid=item.get('uid'),
                                  user_name=item.get('user_name'),
                                  weibo_content=item.get('weibo_content'),
                                  weibo_img=item.get('weibo_img'),
                                  weibo_video=item.get('weibo_vedio'),
                                  repost_num=item.get('repost_num'),
                                  comment_num=item.get('comment_num'),
                                  praise_num=item.get('praise_num'),
                                  is_origin=item.get('is_origin'),
                                  create_time=item.get('create_time'),
                                  device=item.get('device'),
                                  weibo_url=item.get('weibo_url'),
                                  download_time=datetime.datetime.now())
            CommonOper.add_or_update(weiboData)
        elif isinstance(item, RepostItem):
            weiboRepost = WeiboRepost(weibo_id=item.get('weibo_id'),
                                      uid=item.get('uid'),
                                      user_name=item.get('user_name'),
                                      root_weibo_id=item.get('root_weibo_id'),
                                      parent_uid=item.get('parent_uid'),
                                      parent_user_name=item.get('parent_user_name'),
                                      weibo_url=item.get('weibo_url'),
                                      download_time=datetime.datetime.now())
            CommonOper.add_or_update(weiboRepost)
        elif isinstance(item, UserItem):
            user = User(domian=item.get('domain'),
                        uid=item.get('uid'),
                        name=item.get('name'),
                        gender=item.get('gender'),
                        birthday=item.get('birthday'),
                        location=item.get('location'),
                        destription=item.get('description'),
                        register_time=item.get('register_time'),
                        verify_type=item.get('verify_type'),
                        verify_info=item.get('verify_info'),
                        follows_num=item.get('follows_num'),
                        fans_num=item.get('fans_num'),
                        wb_num=item.get('wb_num'),
                        level=item.get('level'),
                        tags=item.get('tags'),
                        work_info=item.get('work_info'),
                        contact_info=item.get('contact_info'),
                        education_info=item.get('education_info'),
                        industry_category=item.get('industry_category'),
                        head_img=item.get('head_img'),
                        download_time=datetime.datetime.now())
            CommonOper.add_or_update(user)
        elif isinstance(item, RelationItem):
            seed = Seeds(uid=item['follow_or_fans_id'])
            SeedsOper.add_or_update(seed)
            relationship = Relationship(uid=item.get('uid'),
                                        follow_or_fans_id=item.get('follow_or_fans_id'),
                                        type=item.get('type'))
            CommonOper.add_or_update(relationship)
        return item
