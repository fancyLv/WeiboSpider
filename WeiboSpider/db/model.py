# -*- coding: utf-8 -*-
# @File    : model.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 11:42
# @Desc    :

from sqlalchemy import Column, String, Integer, DateTime, SMALLINT, Date, Text, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from WeiboSpider.settings import DATABASE

Base = declarative_base()
engine = create_engine(URL(**DATABASE))

Session = sessionmaker(bind=engine)
session = Session()


def load_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def init_db():
    Base.metadata.create_all(engine)


def drop_db():
    Base.metadata.drop_all(engine)


class Accounts(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, comment='用户名')
    password = Column(String(100), comment='密码')
    status = Column(SMALLINT, server_default='0', comment='0 代表正常,1 代表被禁止,2 用户名或密码错误')


class Seeds(Base):
    __tablename__ = 'seeds'
    # id = Column(Integer, primary_key=True)
    uid = Column(String(20), primary_key=True, comment='用户id')
    is_crawled = Column(SMALLINT, server_default='0', comment='微博是否爬完')
    # home_crawled = Column(SMALLINT, server_default='0', comment='个人主页是否爬完')


class User(Base):
    __tablename__ = 'weibo_user'
    id = Column(Integer, primary_key=True)
    domian = Column(String(6), nullable=False, comment='域名,100505,100605,100306,103505,100606')
    uid = Column(String(20), unique=True, nullable=True, comment='用户id')
    name = Column(String(50), comment='昵称')
    gender = Column(String(2), comment='性别')
    birthday = Column(String(20), comment='生日')
    location = Column(String(50), comment='所在的')
    destription = Column(String(500), comment='简介')
    register_time = Column(Date, comment='注册时间/审核时间')
    verify_type = Column(SMALLINT, server_default='0', comment='认证类型，0代表没有认证，1代表个人认证，2代表企业认证')
    verify_info = Column(String(2500), comment='认证信息')
    follows_num = Column(Integer, server_default='0', comment='关注数量')
    fans_num = Column(Integer, server_default='0', comment='粉丝数量')
    wb_num = Column(Integer, server_default='0', comment='微博数量')
    level = Column(Integer, server_default='0', comment='等级')
    tags = Column(String(500), comment='标签')
    work_info = Column(Text, comment='工作信息')
    contact_info = Column(String(500), comment='联系信息')
    education_info = Column(String(500), comment='教育信息')
    industry_category = Column(String(250), comment='行业类别')
    head_img = Column(String(500), comment='头像url')
    download_time = Column(DateTime, comment='采集时间')


class WeiboData(Base):
    __tablename__ = 'weibo_data'
    id = Column(Integer, primary_key=True)
    weibo_id = Column(String(30), unique=True, nullable=False, comment='微博id')
    uid = Column(String(20), comment='用户id')
    user_name = Column(String(50), comment='昵称')
    weibo_content = Column(Text, comment='微博正文')
    weibo_img = Column(String(1000), comment='微博图片')
    weibo_video = Column(String(1000), comment='微博视频')
    repost_num = Column(Integer, server_default='0', comment='转发数量')
    comment_num = Column(Integer, server_default='0', comment='评论数量')
    praise_num = Column(Integer, server_default='0', comment='点赞数量')
    is_origin = Column(SMALLINT, server_default='1', comment='是否原创微博，默认是')
    create_time = Column(DateTime, comment='发布时间')
    device = Column(String(200), comment='来自')
    weibo_url = Column(String(300), comment='微博链接')
    download_time = Column(DateTime, comment='采集时间')


class Relationship(Base):
    __tablename__ = 'user_relation'
    id = Column(Integer, primary_key=True)
    uid = Column(String(20), comment='用户id')
    follow_or_fans_id = Column(String(20), comment='关系id')
    type = Column(SMALLINT, comment='1代表关注,2代表粉丝')
    __table_args__ = (UniqueConstraint('uid', 'follow_or_fans_id'),)


class WeiboRepost(Base):
    __tablename__ = 'weibo_repost'
    id = Column(Integer, primary_key=True)
    weibo_id = Column(String(30), nullable=False, comment='微博id')
    uid = Column(String(20), comment='用户id')
    user_name = Column(String(50), comment='昵称')
    root_weibo_id = Column(String(30), comment='原微博id')
    parent_uid = Column(String(20), comment='原微博用户id')
    parent_user_name = Column(String(50), comment='原微博用户昵称')
    weibo_url = Column(String(300), comment='微博链接')
    download_time = Column(DateTime, comment='采集时间')


if __name__ == '__main__':
    init_db()

