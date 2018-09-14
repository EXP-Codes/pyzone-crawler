# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-03-29 20:17'

import requests
import re
import execjs
import traceback
import src.main.py.config as cfg
import src.main.py.utils.xhr as xhr
from src.main.py.bean.cookie import QQCookie
from PIL import Image


class Lander(object):
    '''
    QQ空间登陆器.
    ========================================================
    QQ空间XHR登陆分析参考(原文所说的方法已失效, 此处做过修正)：
        登陆流程拆解：https://blog.csdn.net/M_S_W/article/details/70193899
        登陆参数分析：https://blog.csdn.net/zhujunxxxxx/article/details/29412297
        登陆参数分析：http://www.vuln.cn/6454
        加密脚本抓取： https://baijiahao.baidu.com/s?id=1570118073573921&wfr=spider&for=pc
        重定向BUG修正: http://jingpin.jikexueyuan.com/article/13992.html
    '''

    QQ = ''         # 所登陆的QQ
    password = ''   # 所登陆的QQ密码
    cookie = None   # 登陆成功后保存的cookie

    def __init__(self, QQ, password):
        '''
        构造函数
        :param QQ: 所登陆的QQ
        :param password: 所登陆的QQ密码
        :return:
        '''
        self.QQ = '0' if not QQ else QQ.strip()
        self.password = '' if not password else password
        self.cookie = QQCookie()


    def execute(self):
        '''
        执行登陆操作
        :return: True:登陆成功; False:登陆失败
        '''
        is_ok = False
        try:
            self.init_cookie_env()
            vcode, verify = self.take_vcode()
            rsa_pwd = self.encrypt_password(vcode)
            callback = self.login(rsa_pwd, vcode, verify)

            is_ok = not not re.search('(?i)^http', callback)
            if is_ok == True :
                is_ok = self.take_gtk_and_token(callback)
                if is_ok == True :
                    print('登陆QQ [%s] 成功: %s' % (self.QQ, self.cookie.nickName))

                else:
                    print('登陆QQ [%s] 失败: 无法提取GTK或QzoneToken' % self.QQ)

            else:
                print('登陆QQ [%s] 失败: %s' % (self.QQ, callback))

        except:
            print('登陆QQ [%s] 失败: XHR协议异常' % self.QQ)
            traceback.print_exc()

        return is_ok


    def init_cookie_env(self):
        '''
        初始化登陆用的cookie环境参数.
        主要提取SIG值（cookie属性名为:pt_login_sig）
        :return:
        '''
        params = {
            'proxy_url' : 'https://qzs.qq.com/qzone/v6/portal/proxy.html',
            's_url' : 'https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone&from=iqq',
            'pt_qr_link' : 'http://z.qzone.com/download.html',
            'self_regurl' : 'https://qzs.qq.com/qzone/v6/reg/index.html',
            'pt_qr_help_link' : 'http://z.qzone.com/download.html',
            'qlogin_auto_login' : '1',
            'low_login' : '0',
            'no_verifyimg' : '1',
            'daid' : '5',
            'appid' : '549000912',
            'hide_title_bar' : '1',
            'style' : '22',
            'target' : 'self',
            'pt_no_auth' : '0',
            'link_target' : 'blank'
        }
        response = requests.get(url=cfg.SIG_URL, headers=xhr.get_headers(), params=params)
        xhr.take_response_cookies(response, self.cookie)

        print('已获得本次登陆的SIG码: %s' % self.cookie.sig)


    def take_vcode(self):
        '''
        提取登陆用的验证码.
        -----------------------------
        一般情况下, 不需要输入图片验证, 此时服务器的回调函数是：
            ptui_checkVC('0','!VAB','\x00\x00\x00\x00\x10\x3f\xff\xdc','cefb41782ce53f614e7665b5519f9858c80ab8925b8060d7a790802212da7205be1916ac4d45a77618c926c6a5fb330520b741d749519f33','2')

        其中: 0 表示不需要验证码
             !VAB 为伪验证码
             cefb41782ce53f614e7665b5519f9858c80ab8925b8060d7a790802212da7205be1916ac4d45a77618c926c6a5fb330520b741d749519f33
                则为验证码的校验码

        -----------------------------
        但有时需要输入图片验证码(一般是输入了无效的QQ号导致的), 此时服务器的回调函数是：
         ptui_checkVC('1','FLQ8ymCigFmw30P7YaLP6iVCZHuyzjJWN2lH4M_OMFBndsUiMY9idQ**','\x00\x00\x00\x00\x00\x12\xd6\x87','','2')

        其中: 1 表示需要验证码
             FLQ8ymCigFmw30P7YaLP6iVCZHuyzjJWN2lH4M_OMFBndsUiMY9idQ** 是用于获取验证码图片的参数（随机生成）

             然后代入参数访问以下地址得到验证码图片：
                https://ssl.captcha.qq.com/getimage?uin={QQ号}&cap_cd=FLQ8ymCigFmw30P7YaLP6iVCZHuyzjJWN2lH4M_OMFBndsUiMY9idQ**

             同时该地址的Response Header中带有了该验证码的校验码：
                Set-Cookie:verifysession=h02iEMnHmjdBoYn7eDlj7AX37Lk7ORMFwJnJSlMufnESimC64Uqa2jz4gHI3ws5jlmiGq5Hg5lfs-2aMkVQ_Gu-vyR7aflns97t

        :return: 验证码:vcode, 校验码:verify
        '''
        params = {
            'u1' : 'https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone&from=iqq&r=0.7018623383003015&pt_uistyle=40',
            'uin' : self.QQ,
            'login_sig' : self.cookie.sig,
            'pt_vcode' : '1',
            'regmaster' : '',
            'pt_tea' : '2',
            'appid' : '549000912',
            'js_ver' : '10215',
            'js_type' : '1'
        }
        response = requests.get(url=cfg.VCODE_URL, headers=xhr.get_headers(), params=params)
        rc = re.compile("'([^']*)'")
        groups = rc.findall(response.text)

        if groups[0] == '0' :
            vcode = groups[1]
            verify = groups[3]

        else:
            vcode, verify = self.take_vcode_by_image(groups[1])

        print('已获得本次登陆的验证码: %s' % vcode)
        print('已获得本次登陆的校验码: %s' % verify)
        return vcode, verify


    def take_vcode_by_image(self, vcode_id):
        '''
        下载验证码图片及其校验码, 同时返回人工输入的验证码
        :param vcode_id: 用于下载验证码图片的ID
        :return: 验证码:vcode, 校验码:verify
        '''
        params = {
            'uin' : self.QQ,
            'cap_cd' : vcode_id
        }
        is_ok, set_cookie = xhr.download_pic(cfg.VCODE_IMG_URL, xhr.get_headers(), params, cfg.VCODE_PATH)
        if is_ok == True :
            self.cookie.add(set_cookie)
            verify = self.cookie.verifysession

            with Image.open(cfg.VCODE_PATH) as image:
                image.show()
                vcode = input('请输入验证码: ').strip()
        else:
            vcode = ''
            verify = ''

        return vcode, verify


    def encrypt_password(self, vcode):
        '''
        对QQ密码做RSA加密
        :param vcode: 本次登陆的验证码
        :return: RSA加密后的密码
        '''
        try:
            with open(cfg.RSA_JS_PATH, encoding=cfg.DEFAULT_CHARSET) as script :
                js = execjs.compile(script.read())
                rsa_pwd = js.call(cfg.RSA_METHOD, self.password, self.QQ, vcode, '')
        except:
            rsa_pwd = 'ERROR'

        print('已加密登陆密码: %s' % rsa_pwd)
        return rsa_pwd


    def login(self, rsa_pwd, vcode, verify):
        '''
        登陆.
        -----------------
            登陆成功, 服务器响应：
                ptuiCB('0','0','https://ptlogin2.qzone.qq.com/check_sig?pttype=1&uin=272629724&service=login&nodirect=0&ptsigx=be9afd54dc7c9b05caf879056d01bff9520c147e19953b9577bf32a4a15b19f1cdfd7ceb17a27939d7596593032d4bcebfb57a4f58ae3ac6d9f078797ad04cd3&s_url=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&f_url=&ptlang=2052&ptredirect=100&aid=549000912&daid=5&j_later=0&low_login_hour=0&regmaster=0&pt_login_type=1&pt_aid=0&pt_aaid=0&pt_light=0&pt_3rd_aid=0','0','登录成功！', 'EXP')

            登陆失败, 服务器响应：
                ptuiCB('3','0','','0','你输入的帐号或密码不正确，请重新输入。', '')
                ptuiCB('4','0','','0','你输入的验证码不正确，请重新输入。', '')
                ptuiCB('7','0','','0','提交参数错误，请检查。(1552982056)', '')
                ptuiCB('24','0','','0','很遗憾，网络连接出现异常，请你检查是否禁用cookies。(1479543040)', '')

        :param rsa_pwd: RSA加密后的密码
        :param vcode: 本次登陆的验证码
        :param verify: 本次登陆的验证码的校验码
        :return: 若登陆成功, 则返回可提取p_skey的回调地址
                 若登陆失败， 则返回失败原因(或回调函数)
        '''
        print('正在登陆QQ [%s] ...' % self.QQ)
        params = {
            'login_sig' : self.cookie.sig,
            'u' : self.QQ,
            'p' : rsa_pwd,
            'verifycode' : vcode,
            'pt_verifysession_v1' : verify,
            'pt_vcode_v1' : '0' if self.is_falsu_vcode(vcode) else '1',
            'from_ui' : '1',    # 重要参数
            'pt_uistyle' : '40',    # 重要参数
            'u1' : 'https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone',
            'pt_randsalt' : '2',
            'aid' : '549000912',
            'daid' : '5',
            'ptredirect' : '0',
            'h' : '1',
            't' : '1',
            'g' : '1',
            'ptlang' : '2052',
            'js_ver' : '10270',
            'js_type' : '1'
        }
        response = requests.get(url=cfg.XHR_LOGIN_URL, headers=xhr.get_headers(), params=params)
        rc = re.compile("'([^']*)'")
        groups = rc.findall(response.text)
        if len(groups) >= 6 :
            if groups[0] == '0' :
                xhr.take_response_cookies(response, self.cookie)
                self.cookie.nickName = groups[5]
                callback = groups[2]    # 登陆成功: 提取p_skey的回调地址
            else:
                callback = groups[4]    # 登陆失败原因
        else:
            callback = response.text    # 登陆失败的回调函数

        return callback


    def is_falsu_vcode(self, vcode):
        '''
        判定验证码是否为伪验证码.
        ----------------------------
            伪验证码以感叹号开头，如  !QWE
            真实验证码则为字符+数字组合，如 Q2R5
        :return: True:是伪验证码; False:是真实验证码
        '''
        return True if (not vcode) or (vcode[0] == '!') else False


    def take_gtk_and_token(self, callback_url):
        '''
        提取本次登陆的GTK与QzoneToken
        :param callback_url: 用于提取p_skey的回调地址(p_skey用于计算GTK, GTK用于获取QzoneToken)
        :return: True:提取成功; False:提取失败
        '''
        print('正在提取本次登陆的 GTK 与 QzoneToken ...')

        # 从登陆回调页面中提取p_skey, 并用之计算GTK（注意callbackURL是一个存在重定向页面, 且p_skey只存在于重定向前的页面）
        response = requests.get(callback_url, headers=xhr.get_headers(self.cookie.to_nv()), allow_redirects=False)  # 关闭重定向
        xhr.take_response_cookies(response, self.cookie)
        print('本次登陆的 GTK: %s' % self.cookie.gtk)

        # 从QQ空间首页的页面源码中提取QzoneToken
        response = requests.get(cfg.QZONE_HOMR_URL(self.QQ), headers=xhr.get_headers(self.cookie.to_nv()))
        self.cookie.qzone_token = self.get_qzone_token(response.text)
        print('本次登陆的 QzoneToken: %s' % self.cookie.qzone_token)

        return (not not self.cookie.gtk) and (not not self.cookie.qzone_token)


    def get_qzone_token(self, page_source):
        '''
        从QQ空间首页的页面源码中提取QzoneToken.
        --------------------------------------
            类似于GTK, 这个 QzoneToken 也是在每次登陆时自动生成的一个固定值, 但是生成算法相对复杂（需要jother解码）,
            因此此处取巧, 直接在页面源码中提取QzoneToken码
        :param page_source: QQ空间首页的页面源码
        :return: QzoneToken
        '''
        match = re.search('window\.g_qzonetoken[^"]+"([^"]+)"', page_source)
        return '' if not match else match.group(1)


