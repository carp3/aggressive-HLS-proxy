import os
import posixpath
import urllib
import urllib2
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from os.path import dirname

import m3u8


def setProxy(proxy):
    proxy = urllib2.ProxyHandler({
                        'http': proxy,
                        'https': proxy
    })
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)



def download(url, dest=None):
    response = _get_url(url)
    data = response.read()
    if dest is None:
        return data
    else:
        f = open(dest, "w")
        f.write(data)
        f.close()


def _get_url(url):
    req = urllib2.Request(url)
    req.add_header('Referer', dirname(url))
    req.add_header('User-Agent',
                   'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36')
    response = urllib2.urlopen(req)
    return response


def getSize(url):
    response = _get_url(url)
    return response.headers["Content-Length"]


def parseM3U8(input):
    input = os.path.join(os.getcwd(), input)
    m3u8_obj = m3u8.load(input)
    return m3u8_obj


class RootedHTTPServer(HTTPServer):

    def __init__(self, base_path, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.RequestHandlerClass.base_path = base_path


class RootedHTTPRequestHandler(SimpleHTTPRequestHandler):

    def translate_path(self, path):
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.base_path
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path



