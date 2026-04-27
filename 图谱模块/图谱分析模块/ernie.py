import requests
import json
import argparse
import os

API_KEY = "xxxxxxxx"
SECRET_KEY = "xxxxxxxx"

def main(query):
        
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=" + get_access_token()
    
    payload = json.dumps({
        "temperature": 0.95,
        "top_p": 0.8,
        "penalty_score": 1,
        "enable_system_memory": False,
        "disable_search": False,
        "enable_citation": False,
        "response_format": "text",
        "messages":[
            {
                "role":"user",
                "content":query
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            # 获取 JSON 数据
            data = response.json()
        except ValueError:
            print("响应内容不是有效�?JSON")
    else:
        print(f"请求失败，状态码: {response.status_code}")

    return data.get('result','No message found')
    

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token�?
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

parser = argparse.ArgumentParser(description="文心一言提取框架")

parser.add_argument('-i',type=str,help='文本文件路径',required=False,default='input/')
parser.add_argument('-e',type=str,help='指令',required=False,default='default.txt')
parser.add_argument('-o',type=str,help='大模型输出路�?,required=False,default='ernie_output/')

args = parser.parse_args()

file_paths = []

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
    instruction = '\n'.join(f.readlines())

if __name__ == '__main__':
     for file_path in file_paths:
        with open(file_path,"r+",encoding='utf-8') as f:
            file = ''.join(f.readlines())
        query = file + '\n' + instruction
        print(query)
        result = main(query)
        print(result)
        file_name = os.path.basename(file_path)
        file_name_without_extension, file_extension = os.path.splitext(file_name)
        destination_file_name = f"{file_name_without_extension}_o{file_extension}"
        destination_file_path = os.path.join(args.o,destination_file_name)
        with open(destination_file_path,'w+',encoding='utf-8') as f:
            f.write(result)
