import requests
import json
import argparse
import os
import preprocessor
import logging

# 使用大模型 分析 input 目录下的文件, 并输出到 output 目录

# 配置日志
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
)

API_KEY = "fDyg397w0FZQoDUTjZ2wCo5v"
SECRET_KEY = "MLqH1pogdiVZKY28Dh4CKlZi066lDB4i"
LLM_BASE_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token="
ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
LLM_HEADERS = {
    'Content-Type': 'application/json'
}
ACCESS_PARAMS = {
    "grant_type": "client_credentials", 
    "client_id": API_KEY, 
    "client_secret": SECRET_KEY
}

def querying(query) -> str:
        
    LLM_URL = LLM_BASE_URL + get_access_token()
    
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
                "role": "user",
                "content": query
            }
        ]
    })
    
    response = requests.request("POST", LLM_URL, headers=LLM_HEADERS, data=payload)
    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            print("响应内容不是有效的 JSON")
    else:
        print(f"请求失败，状态码: {response.status_code}")

    return data.get('result') # default: None
    
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    return str(requests.post(ACCESS_TOKEN_URL, params=ACCESS_PARAMS).json().get("access_token"))

def total(inputDirPath, outputDirPath, instruction):
    for root, _, filenames in os.walk(inputDirPath):
        for filename in filenames:
            try:
                path = os.path.join(root, filename)
                textlist = preprocessor.getPdfTextGrouped(path, 10000)
                seq = 0
                for text in textlist:
                    query = instruction + '\n' + text
                    answer = querying(query)
                    if answer and (not answer.startswith("No related entities and relations")) and (not answer.startswith("Named Entities: (No related entities and relations)")):
                        targetName = preprocessor.genTargetFilename(filename, seq)
                        targetPath = os.path.join(outputDirPath, targetName)
                        with open(targetPath, 'w+', encoding='utf-8') as file:
                            file.write(answer)
                        seq += 1
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")


# # 处理命令行参数
# parser = argparse.ArgumentParser(description="文心一言提取框架")

# parser.add_argument('-i', type=str, help='文本文件路径', required=False, default='input3m/')
# parser.add_argument('-e', type=str, help='指令', required=False, default='default.txt')
# parser.add_argument('-o', type=str, help='大模型输出路径', required=False, default='output/')

# args = parser.parse_args()

# # 从指令文件中提取指令
# with open(args.e, "r+", encoding='utf-8') as f:
#     instruction = '\n'.join(f.readlines())
with open('default.txt', "r+", encoding='utf-8') as f:
    instruction = '\n'.join(f.readlines())

total('PDF3', 'output3', instruction)

# if os.path.isdir(args.i):
#     for root, dirs, files in os.walk(args.i):
#         for file in files:
#             # print(file)
#             full_path = os.path.join(root, file)
#             with open(full_path, "r+", encoding='utf-8') as f:
#                 query = instruction + '\n' + ''.join(f.readlines())
        
#             result = querying(query)

#             file_name_without_extension, _ = os.path.splitext(file)
#             destination_file_path = os.path.join(args.o, f"{file_name_without_extension}_o.txt")
#             with open(destination_file_path,'w+',encoding='utf-8') as f:
#                 f.write(result)
# elif os.path.isfile(args.i):
#     # print(args.i)
#     with open(args.i, "r+", encoding='utf-8') as f:
#         query = instruction + '\n' + ''.join(f.readlines())

#     result = querying(query)

#     file_name_without_extension, _ = os.path.splitext(args.i)
#     destination_file_path = os.path.join(args.o, f"{file_name_without_extension}_o.txt")
#     with open(destination_file_path,'w+',encoding='utf-8') as f:
#         f.write(result)
# else:
#     print(f"{args.i} 不是正确路径")


