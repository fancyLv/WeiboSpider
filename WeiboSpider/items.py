# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class WeiboDataItem(Item):
    weibo_id = Field()
    uid = Field()
    user_name = Field()
    weibo_content = Field()
    weibo_img = Field()
    weibo_video = Field()
    repost_num = Field()
    comment_num = Field()
    praise_num = Field()
    is_origin = Field()
    create_time = Field()
    device = Field()
    weibo_url = Field()
    download_time = Field()

# 微博用户
class UserItem(Item):
    domain = Field() # 域名，100505,100605,100306,103505,100606,100206
    uid = Field() # 用户id
    name = Field() # 昵称
    gender = Field() # 性别
    birthday = Field() # 生日
    location = Field() # 所在地
    description = Field() # 简介
    register_time = Field() # 注册时间/审核时间
    verify_type = Field() # 认证类型，0:没有认证，1:个人认证，2:企业认证
    verify_info = Field() # 认证信息
    follows_num = Field() # 关注数量
    fans_num = Field() # 粉丝数量
    wb_num = Field() # 微博数量
    level = Field() # 等级
    tags = Field() # 标签
    work_info = Field() # 工作信息
    contact_info = Field() # 联系信息
    education_info = Field() # 教育信息
    industry_category = Field() # 行业类别
    head_img = Field() # 头像url
    download_time = Field() # 采集时间


class SeedsItem(Item):
    uid = Field()
    is_crawled = Field()

# 用户关系
class RelationItem(Item):
    uid = Field() # 用户id
    follow_or_fans_id = Field() # 关系id
    type = Field() #关系类型，1:关注，2:粉丝


class RepostItem(Item):
    weibo_id = Field()
    uid = Field()
    user_name = Field()
    root_weibo_id = Field()
    parent_uid = Field()
    parent_user_name = Field()
    weibo_url = Field()
    download_time = Field()
