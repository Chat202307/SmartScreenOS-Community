#!/usr/bin/env python3
"""Local-only, synthetic demo. Does not connect to household services or Apple."""
import argparse,os,socket,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def guard(event,args):
    if event in ('socket.connect','socket.sendto','socket.getaddrinfo'):
        raise OSError('Demo outbound network is disabled')

def main():
    parser=argparse.ArgumentParser(description='运行不连接真实设备的演示界面')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8080)
    options=parser.parse_args()
    # Avoid inheriting a developer's real integration credentials.
    for name in list(os.environ):
        if name.startswith(('SMARTSCREEN_','HOME_ASSISTANT_','XINGOO_','DNAKE_','MQTT_')):
            os.environ.pop(name,None)
    os.chdir(ROOT);sys.path.insert(0,str(ROOT));sys.addaudithook(guard)
    from src.smartscreen_display.application import run_display_server
    with tempfile.TemporaryDirectory(prefix='smartscreenos-demo-') as temporary:
        data=Path(temporary);(data/'photos').mkdir()
        print('演示模式：不连接真实设备或日历；退出后删除演示数据。',flush=True)
        print('页面地址：http://'+options.host+':'+str(options.port),flush=True)
        return run_display_server(config_path=ROOT/'config/runtime.yaml',bind_host=options.host,port=options.port,
            photo_dir=data/'photos',todo_file=data/'todos.json',home_file=ROOT/'config/demo_home_status.json',
            calendar_config_file=ROOT/'config/calendar.json')

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:pass
