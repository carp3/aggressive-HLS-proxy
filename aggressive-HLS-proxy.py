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

parser = argparse.ArgumentParser(description='Aggressive HLS proxy')

parser.add_argument('url', type=bytes,
                    help='Playlist address')

parser.add_argument('--port', type=int, default=8899,
                    help='listening port')

parser.add_argument('--proxy', type=bytes, default="",
                    help='Proxy server')

parser.add_argument('--delay', type=int, default=30,
                    help='delay in second')

args = parser.parse_args()

delay_segments = None

print 'Start listening on http://localhost:' + str(args.port)

if args.proxy is not "":
    utility.setProxy(args.proxy)
    print ("Using Proxy:  " + str(args.proxy))

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
                self._segment_size[segment] = 1
                self._segment_gid[segment] = self._aria.addUri([url],
                                                               {"dir": directory, "file-allocation": "none",
                                                                "max-file-not-found": 10, "split": 5,
                                                                "all-proxy": args.proxy})
                print ("New segment added:" + str(segment))

    def remove(self, segment):
        try:
            self._aria.forceRemove(self._segment_gid[segment])
        except:
            pass


segments = Segments()


def refreshM3U8():
    global delayed_playlist,delay_segments
    try:
        path = os.path.join(directory, 'stream.m3u8')
        utility.download(args.url, path)
        playlist = utility.parseM3U8(path)
        tmp_delayed_playlist = [d.uri for d in delayed_playlist]
        listdir = os.listdir(directory)
        for f in listdir:
            if f != 'stream.m3u8' and f != 'stream.delay.m3u8' and f[-6:] != ".aria2" and f[-12:] != ".aria2__temp":
                if f not in playlist.segments.uri and tmp_delayed_playlist and f not in tmp_delayed_playlist:
                    segments.remove(f)
                    os.remove(os.path.join(directory, f))
                    print ("Old segment deleted:" + str(f))
        if not playlist.segments:
            raise Exception("Invalid playlist")
        if playlist.target_duration is not None:
            delay_segments = int(args.delay / playlist.target_duration) + len(playlist.segments)
        for item in playlist.segments:
            segments.add(item.uri)
            if item.uri not in tmp_delayed_playlist:
                delayed_playlist.append(item)
        if len(delayed_playlist) > delay_segments:
            delayed_playlist = delayed_playlist[-1 * delay_segments:]

        segments_tmp = []
        for item in delayed_playlist[:int(len(playlist.segments) / 2) + 1]:
            segments_tmp.append(item)
        playlist.segments = SegmentList(segments_tmp)
        del segments_tmp

        playlist.media_sequence = int(filter(str.isdigit, delayed_playlist[0].uri))
        playlist.dump(os.path.join(directory, 'stream.delay.m3u8'))
        print ("Delayed playlist updated")
        print ("Playlist updated")

        aria_list = segments._aria.tellWaiting(0, 1000)
        listdir = os.listdir(directory)
        tmp_delayed_playlist = [d.uri for d in delayed_playlist]
        uncomplete_segments = utility.listDiff(tmp_delayed_playlist, listdir)
        waiting_list = []
        for item in aria_list:
            waiting_list.append(os.path.basename(item['files'][0]['uris'][0]['uri']))
        failed_segments = utility.listDiff(uncomplete_segments, waiting_list)
        for item in failed_segments:
            segments.add(item)
        if failed_segments:
            print (str(len(failed_segments)) + " failed segments added to aria")
        del tmp_delayed_playlist, aria_list, waiting_list

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


rl = RunLoop()
rl.every(refreshM3U8, 10)
rl.run()
