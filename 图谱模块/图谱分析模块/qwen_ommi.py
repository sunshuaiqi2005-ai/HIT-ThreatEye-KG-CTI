import os
from openai import OpenAI
import json
import argparse

def main(query):
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="xxxxxxxx",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        model="qwen-max-0125", # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[
            {'role': 'user', 'content': query}],
        )
        
    data = json.loads(completion.model_dump_json())
    content = data['choices'][0]['message']['content']
    
    return content
    
parser = argparse.ArgumentParser(description="通义千问提取框架")

parser.add_argument('-i',type=str,help='文本文件路径',required=False,default='input/')
parser.add_argument('-e',type=str,help='指令',required=False,default='default.txt')
parser.add_argument('-o',type=str,help='大模型输出路�?,required=False,default='qwen_output/')

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
