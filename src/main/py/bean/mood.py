# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-04-09 22:23'


import re
import time


class Mood(object):
    '''
    说说对象
    '''

    page = ''       # 此条说说所在的页码 (QQ空间的说说每页最多20条, 但是数量不是固定的20)
    content = ''    # 说说内容
    create_time = 0 # 说说的创建时间
    pic_urls = []   # 说说中的相关图片地址 (包括说说自身的 或 转发的)


    def __init__(self, page, content, create_time):
        '''
        构造函数
        ==========================
            注意必须在此初始化类成员变量.
            python的类其实就是[原始实例对象], 实例化新的对象, 就相当于从这个实例对象上拷贝一个副本,
            而所有实例对象的操作，都会影响[原始实例对象]的成员变量值
            因此在新建实例时（即在拷贝副本时），为了避免把既有实例对[原始实例对象]的操作结果也拷贝过来,
            则必须在 __init__ 里面重新对类成员对象初始化
        :param page: 此条说说所在的页码
        :param content: 说说内容
        :param create_time: 说说的创建时间
        :return: None
        '''
        self.page = str(page).rjust(4, '0') # 右对齐字符串(宽度为4左边补'0')
        self.create_time = 0 if create_time < 0 else create_time
        self.pic_urls = []

        self.content = '' if not content else re.sub('[\r\n]', '', content)
        self.content = re.sub('@\{.*?nick:(.*?),who.*?\}', '@\g<1>', self.content)  # \g<1>表示取匹配到的group(1)
        self.content = self.time() if not self.content else self.content


    def time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.create_time))


    def pic_num(self):
        return len(self.pic_urls)


    def add_pic_url(self, url):
        if url :
            self.pic_urls.append(url)


    def to_str(self, is_download):
        '''
        打印说说信息
        :param is_download: 是否下载成功
        :return: 照片信息
        '''
        return '[下载状态] : %s\r\n' \
               '[说说页码] : %s\r\n' \
               '[说说内容] : %s\r\n' \
               '[图片数量] : %s\r\n' \
               '[图片列表] : \r\n%s\r\n' \
               '======================================================\r\n' % (
            'true' if is_download else 'false',
            self.page, self.content, self.pic_num(),
            '\r\n'.join(('    %s' % pic_url) for pic_url in self.pic_urls)
        )

