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
from src.main.py.bean.album import Album
from src.main.py.bean.photo import Photo


class AlbumAnalyzer(object):
    '''
    【空间相册】解析器
    '''

    ALBUM_INFO_NAME = 'AlbumInfo-[相册信息].txt' # 相册信息保存文件名
    request_cnt  = 0    # 累计发起请求次数
    cookie = None       # 已登陆的QQCookie
    QQ = ''             # 被爬取数据的目标QQ
    ALBUM_DIR = ''      # 相册保存目录

    def __init__(self, cookie, QQ):
        '''
        构造函数
        :param cookie: 已登陆的QQCookie
        :param QQ: 被爬取数据的目标QQ
        :return:None
        '''
        self.request_cnt = 0
        self.cookie = QQCookie() if not cookie else cookie
        self.QQ = '0' if not QQ else QQ.strip()
        self.ALBUM_DIR = '%s%s/album/' % (cfg.DATA_DIR, self.QQ)


    def execute(self):
        '''
        执行空间相册解析, 并下载所有相册及其内的照片
        :return:None
        '''
        try:

            # 清除上次下载的数据
            if os.path.exists(self.ALBUM_DIR):
                shutil.rmtree(self.ALBUM_DIR)
            os.makedirs(self.ALBUM_DIR)

            # 下载相册
            albums = self.get_albums()
            self.download_albums(albums)
            print('任务完成: QQ [%s] 的空间相册已保存到 [%s]' % (self.QQ, self.ALBUM_DIR))

        except:
            print('任务失败: 下载 QQ [%s] 的空间相册时发生异常' % self.QQ)
            traceback.print_exc()


    def get_albums(self):
        '''
        提取所有相册及其内的照片信息
        :return: 相册列表（含照片信息）
        '''
        albums = self.get_album_list()
        for album in albums:
            self.open(album)
        return albums


    def get_album_list(self):
        '''
        获取相册列表
        :return: 相册列表(仅相册信息, 不含内部照片信息)
        '''
        print('正在提取QQ [%s] 的相册列表...' % self.QQ)
        response = requests.get(url=cfg.ALBUM_LIST_URL,
                                headers=xhr.get_headers(self.cookie.to_nv()),
                                params=self._get_album_parmas())
        albums = []
        try:
            root = json.loads(xhr.to_json(response.text))
            data = root['data']
            album_list = data['albumListModeSort']
            for album in album_list :
                name = album.get('name', '')
                question = album.get('question', '')

                if not question :
                    total = album.get('total', 0)
                    id = album.get('id', 'unknow')
                    url = cfg.ALBUM_URL(self.QQ, id)
                    albums.append(Album(id, name, url, total))
                    print('获得相册 [%s] (照片x%d), 地址: %s' % (name, total, url))

                else:
                    print('相册 [%s] 被加密, 无法读取' % name)
        except:
            print('提取QQ [%s] 的相册列表异常' % self.QQ)
            traceback.print_exc()

        return albums


    def _get_album_parmas(self):
        '''
        获取相册请求参数
        :return:
        '''
        params = self._get_parmas()
        params['handset'] = '4'
        params['filter'] = '1'
        params['needUserInfo'] = '1'
        params['pageNumModeSort'] = '40'
        params['pageNumModeClass'] = '15'
        return params


    def open(self, album):
        '''
        打开相册, 提取其中的所有照片信息
        :param album: 相册信息
        :return: None
        '''
        print('正在读取相册 [%s] (共%d页, 照片x%d)' % (album.name, album.page_num, album.total_pic_num))
        for page in range(album.page_num) :
            page += 1
            print(' -> 正在提取第 [%d] 页的照片信息...' % page)
            page_photos = self.get_page_photos(album, page)
            album.adds(page_photos)
            print(' ->  -> 第 [%d] 页照片提取完成, 当前进度: %d/%d' % (page, album.pic_num(), album.total_pic_num))
            time.sleep(cfg.SLEEP_TIME)


    def get_page_photos(self, album, page):
        '''
        获取相册的分页照片信息
        :param album: 相册信息
        :param page: 页数
        :return: 分页照片信息
        '''
        response = requests.get(url=cfg.PHOTO_LIST_URL,
                                headers=xhr.get_headers(self.cookie.to_nv()),
                                params=self._get_photo_parmas(album.id, page))
        photos = []
        try:
            root = json.loads(xhr.to_json(response.text))
            data = root['data']
            photo_list = data['photoList']
            for photo in photo_list :
                desc = photo.get('desc', '')
                time = photo.get('uploadtime', '')
                url = pic.convert(photo.get('url', ''))
                photos.append(Photo(desc, time, url))

        except:
            print('提取相册 [%s] 第%d页的照片信息异常' % (album.name, page))
            traceback.print_exc()

        return photos


    def _get_photo_parmas(self, album_id, page):
        '''
        获取照片请求参数
        :param album_id: 相册ID
        :param page: 页码
        :return:
        '''
        params = self._get_parmas()
        params['topicId'] = album_id
        params['pageStart'] = '%d' % ((page - 1) * cfg.BATCH_LIMT)
        params['pageNum'] = '%d' % cfg.BATCH_LIMT
        params['mode'] = '0'
        params['noTopic'] = '0'
        params['skipCmtCount'] = '0'
        params['singleurl'] = '1'
        params['outstyle'] = 'json'
        params['json_esc'] = '1'
        params['batchId'] = ''
        return params


    def _get_parmas(self):
        '''
        获取相册/照片请求参数
        :return:
        '''
        params = {
            'g_tk' : self.cookie.gtk,
            'callback' : 'shine%d_Callback' % self.request_cnt,
            'callbackFun' : 'shine%d' % self.request_cnt,
            '_' : '%d' % int(time.time()),
            'uin' : self.cookie.uin,
            'hostUin' : self.QQ,
            'inCharset' : cfg.DEFAULT_CHARSET,
            'outCharset' : cfg.DEFAULT_CHARSET,
            'source' : 'qzone',
            'plat' : 'qzone',
            'format' : 'jsonp',
            'notice' : '0',
            'appid' : '4',
            'idcNum' : '4'
        }
        self.request_cnt += 1
        return params


    def download_albums(self, albums):
        '''
        下载所有相册及其内的照片
        :param albums: 相册集（含照片信息）
        :return: None
        '''
        if len(albums) <= 0 :
            return

        print('提取QQ [%s] 的相册及照片完成, 开始下载...' % self.QQ)
        for album in albums :
            os.makedirs('%s%s' % (self.ALBUM_DIR, album.name))
            album_infos = album.to_str()

            print('正在下载相册 [%s] 的照片...' % album.name)
            cnt = 0
            for photo in album.photos :
                is_ok = self.download_photo(album, photo)
                cnt += (1 if is_ok else 0)
                album_infos = '%s%s' % (album_infos, photo.to_str(is_ok))
                print(' -> 下载照片进度(%s): %d/%d' % ('成功' if is_ok else '失败', cnt, album.pic_num()))
                time.sleep(cfg.SLEEP_TIME)

            print(' -> 相册 [%s] 下载完成, 成功率: %d/%d' % (album.name, cnt, album.pic_num()))

            # 保存下载信息
            save_path = '%s%s/%s' % (self.ALBUM_DIR, album.name, self.ALBUM_INFO_NAME)
            with open(save_path, 'w', encoding=cfg.DEFAULT_CHARSET) as file :
                file.write(album_infos)


    def download_photo(self, album, photo):
        '''
        下载单张照片
        :param album: 照片所属的相册信息
        :param photo: 照片信息
        :return: 是否下载成功
        '''
        headers = xhr.get_headers(self.cookie.to_nv())
        headers['Host'] = xhr.to_host(photo.url)
        headers['Referer'] = album.url
        save_path = '%s%s/%s' % (self.ALBUM_DIR, album.name, photo.name)

        is_ok = False
        for retry in range(cfg.RETRY) :
            is_ok, set_cookie = xhr.download_pic(photo.url, headers, '{}', save_path)
            if is_ok == True :
                break

            elif os.path.exists(save_path) :
                os.remove(save_path)

        return is_ok