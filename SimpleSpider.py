# -*- coding: utf-8 -*-

import requests
import http.cookiejar as cookielib
from bs4 import BeautifulSoup
import json
import re

# 变量
_loginUrl = "http://hdhome.org/login.php"
_takeloginUrl = "http://hdhome.org/takelogin.php"
_torrentUrl = "http://hdhome.org/torrents.php"
_userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"
_headers = {
    "User-Agent": _userAgent,
    "Referer": _loginUrl
}
_se = requests.session()
_se.cookies = cookielib.LWPCookieJar(filename="Cookies.txt")


def isLoginStatus():
    _userUrl = "http://hdhome.org/userdetails.php"
    _re = _se.get(_userUrl, headers=_headers, allow_redirects=False)
    if _re.status_code != 200:
        return False
    else:
        return True


def newLogin():
    # 请求验证码Hash
    print("请求新的验证码")
    _re = _se.get(url=_loginUrl, headers=_headers)
    _soup = BeautifulSoup(_re.content, "html.parser")
    _MD5Hash = _soup.find("input", type="hidden").get("value")
    _MD5Code = decodeMD5(_MD5Hash)
    print("哈希值：" + _MD5Hash)
    print("验证码：" + _MD5Code)

    # 登录
    try:
        with open("UserData.json", "r", encoding='utf-8') as _file:
            _file.seek(0)
            _jsonData = json.load(_file)
            _username = _jsonData["username"]
            _password = _jsonData["password"]
            _file.close()
    except IOError:
        _username = input("请输入用户名：")
        _password = input("请输入密码：")
        _jsonData = {"username": _username, "password": _password}
        with open("UserData.json", "w", encoding='utf-8') as _file:
            json.dump(_jsonData, _file, indent=4)
            _file.close()

    _postData = {
        "imagehash": _MD5Hash,
        "imagestring": _MD5Code,
        "password": _password,
        "username": _username
    }
    _po = _se.post(url=_takeloginUrl, data=_postData, headers=_headers)
    isLogin = isLoginStatus()
    if isLogin:
        _se.cookies.save()
        print("登陆成功，状态：" + str(_re.status_code))
        return True
    else:
        return False


def decodeMD5(_md5hash):
    _postUrl = "https://www.somd5.com/search.php"
    _postData = {
        "captcha": 0,
        "hash": _md5hash
    }
    _post = requests.post(url=_postUrl, data=_postData, headers=_headers)
    _json = _post.text
    _md5Code = json.loads(_json)["data"]
    return _md5Code


def getList():
    # 变量
    _startStr = "http://hdhome.org/download.php?id="
    _endStr = "&passkey="
    _passKey = getKey()

    # 获取种子列表
    print("获取种子列表")
    _re = _se.get(url=_torrentUrl, headers=_headers)
    _soup = BeautifulSoup(_re.content, "html.parser")
    _sourceList = _soup.find_all("table", class_="torrentname")

    for each in _sourceList:
        _a = each.find("a", title=re.compile(r"(.|\n)*[^添加评论]"))
        _id = re.sub(r"[details.php?id=, $&hit=1]", "", _a.get("href"))
        _aStr = "标题：" + _a.get("title") + "\n链接：" + _startStr + _id + _endStr + _passKey
        _type = each.find("img", class_=re.compile("pro_"))
        try:
            _type = _type.get("class")[0]
            if _type == "pro_free":
                _span = each.find("span", title=re.compile(r"(.|\n)*"))
                _timeout = _span.get("title")
                _countdown = _span.string
                _type = "类型：免费\n到期时间：" + _timeout + "\n剩余时间：" + _countdown
            elif _type == "pro_2up":
                _type = "类型：双倍上传"
            elif _type == "pro_50pctdown":
                _type = "类型：50%下载"
            elif _type == "pro_30pctdown":
                _type = "类型：30%下载"
        except AttributeError:
            _type = "类型：正常"

        print("------------------------------------")
        print(_aStr)
        print(_type)


def getKey():
    _passKeyUrl = "http://hdhome.org/usercp.php"
    _re = _se.get(_passKeyUrl)
    _soup = BeautifulSoup(_re.content, "html.parser")
    _passKeyList = _soup.find_all("td")
    for each in _passKeyList:
        _passKey = re.match(r"[a-zA-Z0-9]{32}", each.text)
        if _passKey is not None:
            return _passKey.string


if __name__ == "__main__":
    try:
        _se.cookies.load()
        isLogin = isLoginStatus()
    except FileNotFoundError:
        isLogin = False
    if isLogin == False:
        newLogin()
    getList()
