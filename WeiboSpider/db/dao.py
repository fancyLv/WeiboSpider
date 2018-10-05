# -*- coding: utf-8 -*-
# @File    : dao.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 16:26
# @Desc    :
from functools import wraps

from sqlalchemy import and_

from WeiboSpider.db.model import session, Accounts, Seeds, User
from WeiboSpider.util.log import storage


def db_commit_decorator(func):
    @wraps(func)
    def session_commit(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            storage.error('DB operation error，here are details:{}'.format(e))
            session.rollback()

    return session_commit


class CommonOper:
    @classmethod
    @db_commit_decorator
    def add(cls, data):
        session.add(data)
        session.commit()

    @classmethod
    @db_commit_decorator
    def add_or_update(cls, data):
        session.merge(data)
        session.commit()


class AccountsOper(CommonOper):
    @classmethod
    def get_account_info(cls):
        return session.query(Accounts.name, Accounts.password, Accounts.status).filter(Accounts.status == 0).all()

    @classmethod
    def get_account_info_by_name(cls, name):
        return session.query(Accounts.name, Accounts.password).filter(
            and_(Accounts.status == 0, Accounts.name == name)).first()

    @classmethod
    @db_commit_decorator
    def freeze_account(cls, name, status):
        '''
        :param name: login account
        :param status: 0 stands for normal,1 stands for banned,2 stands for name or password is invalid
        :return:
        '''
        account = session.query(Accounts).filter(Accounts.name == name).first()
        account.status = status
        session.commit()


class SeedsOper(CommonOper):
    @classmethod
    def get_seeds_ids(cls):
        return session.query(Seeds.uid).filter(Seeds.is_crawled == 0).all()

    # @classmethod
    # def get_home_ids(cls):
    #     return session.query(Seeds.uid).filter(Seeds.home_crawled == 0).all()

    @classmethod
    @db_commit_decorator
    def set_seed_crawled(cls, uid, result):
        '''
        :param uid:
        :param result: crawling result, 1 stands for succeed, 2 stands for fail
        :return:
        '''
        seed = session.query(Seeds).filter(Seeds.uid == uid).first()
        if seed and not seed.is_crawled:
            seed.is_crawled = result
        else:
            seed = Seeds(uid=uid, is_crawled=result)
            session.add(seed)
        session.commit()

    @classmethod
    @db_commit_decorator
    def insert_seed(cls, ids):
        session.execute(Seeds.__table__.insert().prefix_with('IGNORE'), [{'uid': i} for i in ids])
        session.commit()


class UserOper(CommonOper):
    @classmethod
    def get_user_ids(cls):
        return session.query(User.domian,User.uid).all()
