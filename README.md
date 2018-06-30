# aggressive-HLS-proxy
An aggressive HLS proxy for slow networks

I wrote this program just to watch Worldcup on the internet over unstable connection. therefore it's unpolished and might not work for you out of the box.
If you have fast connection i recommend using [this](http://www.hls-proxy.com/) or [this](https://github.com/Viblast/hls-proxy)

## Install

##### Download or clone latest files:

`git clone https://github.com/carp3/aggressive-HLS-proxy.git`

`cd aggressive-HLS-proxy`

##### Install dependencies:

`pip install m3u8
`

##### Create cache dir and give write permission:

`mkdir cache && chmod +w cache
`

##### Run aria2c:

`aria2c --enable-rpc --rpc-listen-all --max-concurrent-downloads=5 --max-connection-per-server=10 --min-split-size=1M
`

##### Run proxy:

`python2 aggressive-HLS-proxy http://domain.com/path/to/livetv.hls --port=8899 --proxy=proxyserver.com:3128 --delay=30
`

Wait around 30 seconds for cache to build-up

Open http://localhost:8899/stream.delay.m3u8 in VLC


## Todo
* Compatibility with python3 ( it's easily doable with 2to3 )
* Ditching aria2 and download segments with python
* Create delayed playlist immediately and gradually increase delay (How? _without resampling_. perhaps by inserting short blank gaps between segments )
* Support for encrypted playlists 


