import argparse
import os
import sys
import threading
import traceback
from os.path import dirname
from urllib2 import HTTPError

from m3u8.model import SegmentList

import utility
from aria2c import PyAria2
from eventloop import RunLoop

DELAY_LENGTH = 50

parser = argparse.ArgumentParser(description='Aggressive HLS proxy')

parser.add_argument('url', type=bytes,
                    help='Playlist address')

parser.add_argument('--port', type=int, default=8899,
                    help='listening port')

parser.add_argument('--proxy', type=bytes, default="",
                    help='Proxy server')


args = parser.parse_args()


print 'Start listening on http://localhost:' + str(args.port)

if args.proxy is not "":
    utility.setProxy(args.proxy)
    print ("Using Proxy:  "+ str(args.proxy))

directory = 'cache'

delayed_playlist = []

server_address = ('', args.port)
HandlerClass = utility.RootedHTTPRequestHandler
ServerClass = utility.RootedHTTPServer
httpd = ServerClass(directory, server_address, HandlerClass)
thread = threading.Thread(target=httpd.serve_forever)
thread.daemon = True

try:
    thread.start()
except Exception as e:
    print ("Error while stating server:" + str(e))
    sys.exit(0)


class Segments:
    _segment_size = {}
    _segment_gid = {}
    _segment_downloaded = {}
    _aria = None

    def __init__(self):
        self._aria = PyAria2()
        pass

    def add(self, segment):
        url = dirname(args.url) + "/" + segment
        if len(segment) > 0:
            if segment not in self._segment_size:
                self._segment_size[segment] = utility.getSize(url)
                self._segment_gid[segment] = self._aria.addUri([url],
                                                               {"dir": "cache", "file-allocation": "none",
                                                                "max-file-not-found": 10, "split": 5,"all-proxy":args.proxy})
                print ("New segment added:" + str(segment))

    def remove(self, segment):
        try:
            self._aria.forceRemove(self._segment_gid[segment])
        except:
            pass


segments = Segments()


def refreshM3U8():
    global delayed_playlist
    try:
        path = os.path.join('cache', 'stream.m3u8')
        utility.download(args.url, path)
        playlist = utility.parseM3U8(path)
        tmp_delayed_playlist = [d.uri for d in delayed_playlist]
        for f in os.listdir("cache"):
            if f != 'stream.m3u8' and f != 'stream.delay.m3u8' and f[-6:] != ".aria2" and f[-12:] != ".aria2__temp":
                if f not in playlist.segments.uri  and tmp_delayed_playlist and f not in tmp_delayed_playlist:
                    segments.remove(f)
                    os.remove(os.path.join("cache", f))
                    print ("Old segment deleted:" + str(f))
        if not playlist.segments:
            raise Exception("Invalid playlist")
        for item in playlist.segments:
            segments.add(item.uri)
            if item.uri not in tmp_delayed_playlist:
                delayed_playlist.append(item)
        del tmp_delayed_playlist
        if len(delayed_playlist)> DELAY_LENGTH:
            delayed_playlist = delayed_playlist[-1*DELAY_LENGTH:]

        segments_tmp = []
        for item in delayed_playlist[:int(len(playlist.segments)/2)]:
            segments_tmp.append(item)
        playlist.segments = SegmentList(segments_tmp)
        del segments_tmp

        playlist.media_sequence = int(filter(str.isdigit,delayed_playlist[0].uri))
        playlist.dump(os.path.join('cache', 'stream.delay.m3u8'))
        print ("Delayed playlist updated")
        print ("Playlist updated")
    except HTTPError as e:
        print ("Error while refreshing M3U8: " + str(e))
    except Exception as e:
        print ("Error while processing M3U8: " + str(e))
        exc_info = None
        try:
            exc_info = sys.exc_info()
        finally:
            traceback.print_exception(*exc_info)
            del exc_info


def announceTime():
    print("Time")


rl = RunLoop()
rl.every(refreshM3U8, 10)
rl.run()
