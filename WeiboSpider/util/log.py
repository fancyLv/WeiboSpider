#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : log.py
# @Author  : Fang
# @Time    : 2018/1/2 0002 11:11
# @Desc    :
import os
import logging
import logging.config as log_conf

log_dir = os.path.dirname(os.path.dirname(__file__)) + '/logs'
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

log_path = os.path.join(log_dir, 'weibo.log')

log_config = {
    'version': 1.0,
    'formatters': {
        'detail': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '%(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detail'
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            # 'maxBytes': 1024 * 1024 * 5,
            'when' : 'D',
            'interval' : 1,
            'backupCount': 10,
            'filename': log_path,
            'level': 'INFO',
            'formatter': 'detail',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'crawler': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'parser': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'other': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'storage': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'login': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        }
    }
}

log_conf.dictConfig(log_config)

crawler = logging.getLogger('crawler')
parser = logging.getLogger('parser')
other = logging.getLogger('other')
storage = logging.getLogger('storage')
login = logging.getLogger('login')
