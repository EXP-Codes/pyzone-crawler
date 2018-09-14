# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-03-30 22:53'


import os
import src.main.py.config as cfg
import src.main.py.utils.des as des


def load():
    '''
    加载上次登陆信息
    :return: username, password, QQ
    '''
    username = ''
    password = ''
    QQ = ''

    if os.path.exists(cfg.ACCOUNT_PATH) :
        with open(cfg.ACCOUNT_PATH, 'r') as account:
            lines = account.readlines()
            if len(lines) == 3 :
                username = des.decrypt(lines[0].strip())
                password = des.decrypt(lines[1].strip())
                QQ = des.decrypt(lines[2].strip())

    return username, password, QQ


def save(username, password, QQ):
    '''
    保存本次登陆信息
    :param username: 登陆QQ账号
    :param password: 登陆QQ密码
    :param QQ: 爬取数据的目标QQ号
    :return:
    '''
    data = '%s\n%s\n%s\n' % (
        des.encrypt(username),
        des.encrypt(password),
        des.encrypt(QQ)
    )

    with open(cfg.ACCOUNT_PATH, 'w', encoding=cfg.DEFAULT_CHARSET) as account:
        account.write(data)

