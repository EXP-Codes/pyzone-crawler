# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-03-29 20:17'


import src.main.py.utils.account as account
from src.main.py.core.lander import Lander
from src.main.py.core.album import AlbumAnalyzer
from src.main.py.core.mood import MoodAnalyzer


def crawler():
    '''
    执行QQ空间爬虫
    :return: None
    '''
    username, password, QQ = account.load()
    if not username or not password or not QQ :
        username = input('请输入 [登陆QQ账号] : ').strip()
        password = input('请输入 [登陆QQ密码] : ').strip()
        QQ = input('请输入 [爬取数据的目标QQ号] : ').strip()

    print('登陆QQ账号: %s' % username)
    print('登陆QQ密码: %s' % password)
    print('爬取数据的目标QQ号: %s' % QQ)

    # 登陆
    lander = Lander(username, password)
    if lander.execute() == True:

        # 保存登陆信息
        account.save(username, password, QQ)

        if input('爬取相册 ? [y/n] : ').strip() == 'y' :
            album = AlbumAnalyzer(lander.cookie, QQ)
            album.execute()
        else:
            print('跳过爬取相册')

        if input('爬取说说 ? [y/n] : ').strip() == 'y' :
            mood = MoodAnalyzer(lander.cookie,QQ)
            mood.execute()
        else:
            print('跳过爬取说说')



if __name__ == '__main__':
    crawler()

