# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-03-29 20:17'

import os
import shutil
import requests
import time
import json
import traceback
import src.main.py.config as cfg
import src.main.py.utils.xhr as xhr
import src.main.py.utils.pic as pic
from src.main.py.bean.cookie import QQCookie
from src.main.py.bean.mood import Mood


class MoodAnalyzer(object):
    '''
    【空间说说】解析器
    '''

    MOOD_INFO_NAME = 'MoodInfo-[说说信息].txt'  # 说说分页信息保存文件名
    cookie = None           # 已登陆的QQCookie
    QQ = ''                 # 被爬取数据的目标QQ
    MOOD_DIR = ''           # 说说保存目录
    PAGE_DIR_PREFIX = ''    # 说说每页图文信息的保存路径前缀
    PHOTO_DIR = ''          # 说说所有照片的保存目录


    def __init__(self, cookie, QQ):
        '''
        构造函数
        :param cookie: 已登陆的QQCookie
        :param QQ: 被爬取数据的目标QQ
        :return:None
        '''
        self.cookie = QQCookie() if not cookie else cookie
        self.QQ = '0' if not QQ else QQ.strip()
        self.MOOD_DIR = '%s%s/mood/' % (cfg.DATA_DIR, self.QQ)
        self.PAGE_DIR_PREFIX = '%scontent/page-' % self.MOOD_DIR
        self.PHOTO_DIR = '%sphotos/' % self.MOOD_DIR


    def execute(self):
        '''
        执行空间说说解析, 并下载所有说说及相关照片
        :return:
        '''
        try:

            # 清除上次下载的数据
            if os.path.exists(self.MOOD_DIR):
                shutil.rmtree(self.MOOD_DIR)
            os.makedirs(self.MOOD_DIR)

            # 下载说说及照片
            moods = self.get_moods()
            self.download_moods(moods)

            print('任务完成: QQ [%s] 的空间说说已保存到 [%s]' % (self.QQ, self.MOOD_DIR))

        except:
            print('任务失败: 下载 QQ [%s] 的空间说说时发生异常' % self.QQ)
            traceback.print_exc()


    def get_moods(self):
        '''
        提取所有说说及相关的照片信息
        :return: 说说列表（含相关照片信息）
        '''
        print('正在提取QQ [%s] 的说说动态...' % self.QQ)
        moods = []
        PAGE_NUM = self.get_page_num()
        for page in range(PAGE_NUM) :
            page += 1
            print(' -> 正在提取第 [%d/%d] 页的说说信息...' % (page, PAGE_NUM))
            moods.extend(self.get_page_moods(page))

            print(' -> 第 [%d/%d] 页说说提取完成, 累计说说数量: %d' % (page, PAGE_NUM, len(moods)))
            time.sleep(cfg.SLEEP_TIME)

        return moods


    def get_page_num(self):
        '''
        获取说说总页数
        :return: 说说总页数
        '''
        print('正在提取QQ [%s] 的说说页数...' % self.QQ)
        total = 0
        try:
            root = json.loads(self.get_page_moods_json(1))
            total = root.get('total', 0)

        except:
            print('提取QQ [%s] 的说说页数失败' % self.QQ)
            traceback.print_exc()

        return pic.get_page_num(total, cfg.BATCH_LIMT)


    def get_page_moods(self, page):
        '''
        获取分页的说说内容
        :param page: 页码
        :return: 分页说说列表（含相关照片信息）
        '''
        moods = []
        try:
            root = json.loads(self.get_page_moods_json(page))
            msg_list = root['msglist']
            for msg in msg_list :
                content = msg.get('content', '')
                create_time = msg.get('created_time', 0)

                mood = Mood(page, content, create_time)
                pics = msg.get('pic', None)
                if pics :
                    for p in pics :
                        url = pic.convert(p.get('url3', ''))
                        mood.add_pic_url(url)

                moods.append(mood)

        except:
            print('提取第 [%d] 页的说说信息异常' % page)
            traceback.print_exc()

        return moods


    def get_page_moods_json(self, page):
        '''
        获取分页的说说Json
        :param page: 页码
        :return: 分页的说说Json
        '''
        headers = xhr.get_headers(self.cookie.to_nv())
        headers['Referer'] = cfg.MOOD_REFERER
        params = {
            'g_tk' : self.cookie.gtk,
            'qzonetoken' : self.cookie.qzone_token,
            'uin' : self.QQ,
            'hostUin' : self.QQ,
            'pos' : str((page - 1) * cfg.BATCH_LIMT),
            'num' : str(cfg.BATCH_LIMT),
            'cgi_host' : cfg.MOOD_DOMAIN,
            'inCharset' : cfg.DEFAULT_CHARSET,
            'outCharset' : cfg.DEFAULT_CHARSET,
            'notice' : '0',
            'sort' : '0',
            'code_version' : '1',
            'format' : 'jsonp',
            'need_private_comment' : '1',
        }
        response = requests.get(cfg.MOOD_URL, headers=headers, params=params)
        return xhr.to_json(response.text)


    def download_moods(self, moods):
        '''
        下载所有说说及相关的照片
        :param moods: 说说集（含照片信息）
        :return: None
        '''
        MOOD_NUM = len(moods)
        if MOOD_NUM <= 0 :
            return

        print('提取QQ [%s] 的说说及照片完成, 开始下载...' % self.QQ)
        os.makedirs(self.PHOTO_DIR)

        for idx, mood in enumerate(moods) :
            page_dir = '%s%s' % (self.PAGE_DIR_PREFIX, mood.page)
            if not os.path.exists(page_dir) :
                os.makedirs(page_dir)

            print('正在下载第 [%d/%d] 条说说: ' % (idx + 1, MOOD_NUM))
            cnt = self.download_mood(mood)
            is_ok = (cnt == mood.pic_num())
            print(' -> 说说照片下载完成, 成功率: %d/%d' % (cnt, mood.pic_num()))
            time.sleep(cfg.SLEEP_TIME)

            # 保存下载信息
            save_path = '%s/%s' % (page_dir, self.MOOD_INFO_NAME)
            with open(save_path, 'a', encoding=cfg.DEFAULT_CHARSET) as file :
                file.write(mood.to_str(is_ok))


    def download_mood(self, mood):
        '''
        下载单条说说及相关的照片
        :param mood: 说说信息
        :return: 成功下载的照片数
        '''
        headers = xhr.get_headers(self.cookie.to_nv())
        headers['Referer'] = cfg.MOOD_REFERER

        cnt = 0
        for idx, pic_url in enumerate(mood.pic_urls) :
            pic_name = pic.get_pic_name(str(idx + 1), mood.content)
            is_ok = self.download_photo(headers, mood.page, pic_name, pic_url)
            cnt += (1 if is_ok else 0)
            print(' -> 下载照片进度(%s): %d/%d' % ('成功' if is_ok else '失败', cnt, mood.pic_num()))

        return cnt


    def download_photo(self, headers, page, pic_name, pic_url):
        '''
        下载单张图片到说说的分页目录，并复制到图片合集目录
        :param headers: 用于下载图片的HTTP请求头
        :param page: 页码索引
        :param pic_name: 图片名称
        :param pic_url: 图片地址
        :return: True:下载成功; False: 下载失败
        '''
        save_path = '%s%s/%s' % (self.PAGE_DIR_PREFIX, page, pic_name)

        is_ok = False
        for retry in range(cfg.RETRY) :
            is_ok, set_cookie = xhr.download_pic(pic_url, headers, '{}', save_path)
            if is_ok == True :
                shutil.copyfile(save_path, '%s%s' % (self.PHOTO_DIR, pic_name))
                break

            elif os.path.exists(save_path) :
                os.remove(save_path)

        return is_ok
