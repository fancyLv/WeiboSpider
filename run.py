# -*- coding: utf-8 -*-
# @File    : run.py
# @Author  : Fang
# @Time    : 2018/1/5 0005 22:39
# @Desc    :
from scrapy import cmdline

if __name__ == '__main__':
    cmdline.execute('scrapy crawlall'.split())
