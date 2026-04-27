import _thread as thread
import os
import time
import base64
import threading
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import argparse


class Ws_Param(object):
    # 初始�?
    def __init__(self, APPID, APIKey, APISecret, gpt_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符�?
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字�?
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.gpt_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一�?
        return url


# 收到websocket错误的处�?
def on_error(ws,error):
    print("### error:", error)


# 收到websocket关闭的处�?
def on_close(ws,close_status_code,close_msg):
    print(f'### 结束会话+{close_status_code}+{close_msg}')


# 收到websocket连接建立的处�?
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, query=ws.query, domain=ws.domain))
    ws.send(data)


# 收到websocket消息的处�?
def on_message(ws, message):
    # print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        content = content.replace('\n','')
        contents.append(content)
        result = ''.join(contents)
        file_name = os.path.basename(file_path)
        file_name_without_extension, file_extension = os.path.splitext(file_name)
        destination_file_name = f"{file_name_without_extension}_o{file_extension}"
        destination_file_path = os.path.join(args.o,destination_file_name)
        with open(destination_file_path,'w+',encoding='utf-8') as f:
            f.write(result)
        if status == 2:
            print("")
            contents.clear()

def gen_params(appid, query, domain):
    """
    通过appid和用户的提问来生成请参数
    """

    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",           
            # "patch_id": []    #接入微调模型，对应服务发布后的resourceid          
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.5,
                "max_tokens": 4096,
                "auditing": "default",
            }
        },
        "payload": {
            "message": {
                "text": [{"role": "user", "content": query}]
            }
        }
    }
    return data


def main(appid, api_secret, api_key, Spark_url, domain , query ):
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()

    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    ws.query = query
    ws.domain = domain

    ws.run_forever()

parser = argparse.ArgumentParser(description="星火大模型提取框�?)

parser.add_argument('-i',type=str,help='文本文件路径',required=False,default='input/')
parser.add_argument('-e',type=str,help='指令',required=False,default='default.txt')
parser.add_argument('-o',type=str,help='大模型输出路�?,required=False,default='sparkai_output/')

args = parser.parse_args()

file_paths = []
contents = []

if os.path.isdir(args.i):
    for root,dirs,files in os.walk(args.i):
        for file in files:
            full_path = os.path.join(root,file)
            file_paths.append(full_path)
elif os.path.isfile(args.i):
    file_paths.append(args.i)
else:
    print(f"{args.i} 非正常输�?)


with open(args.e,"r+",encoding='utf-8') as f:
    instruction = ''.join(f.readlines())

if __name__ == "__main__":

    for file_path in file_paths:
        with open(file_path,"r+",encoding='utf-8') as f:
            file = ''.join(f.readlines())
        query = file + '\n' + instruction
        print(query)
        main(
            appid="xxxxxxxx",
            api_secret="xxxxxxxx",
            api_key="xxxxxxxx",
            #appid、api_secret、api_key三个服务认证信息请前往开放平台控制台查看（https://console.xfyun.cn/services/bm35�?
            # Spark_url="wss://spark-api.xf-yun.com/v3.5/chat",      # Max环境的地址   
            Spark_url = "wss://spark-api.xf-yun.com/v4.0/chat",  # 4.0Ultra环境的地址
            # Spark_url = "wss://spark-api.xf-yun.com/v3.1/chat"  # Pro环境的地址
            # Spark_url = "wss://spark-api.xf-yun.com/v1.1/chat",  # Lite环境的地址
            # domain="generalv3.5",     # Max版本
            domain = "4.0Ultra",     # 4.0Ultra 版本
            # domain = "generalv3"    # Pro版本
            # domain = "lite",      # Lite版本
            query = query
        )
