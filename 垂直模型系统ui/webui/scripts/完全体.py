import requests
import json
import os
import re
from tqdm import tqdm

# 文心一言 API 配置
API_KEY = "kz0xya0zn9ZohnO1cVdxPURx"
SECRET_KEY = "KJ7AyaVZnYDekeMEdoycS8K6MkuZGmby"

CATEGORIES = ["Malware", "Threat_Actors", "Campaign", "Reports", "Targets", "Vulnerabilities", "Uncategorized"]

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/uploads"))
OUTPUT1_DIR = os.path.join(BASE_DIR, "output1")
OUTPUT2_DIR = os.path.join(BASE_DIR, "output2")
OUTPUT3_DIR = os.path.join(BASE_DIR, "output3")
OUTPUT4_DIR = os.path.join(BASE_DIR, "output4")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
PDF_LIST_FILE = os.path.abspath(os.path.join(BASE_DIR, "../utils/pdf_files.txt"))
output_path = os.path.join(OUTPUT4_DIR, "alpaca_dataset.json")

def get_access_token():
    """获取 Access Token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception("获取 access_token 失败")


def call_wenxin_api(query):
    """调用文心一言 API 进行分析"""
    access_token = get_access_token()
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
    payload = json.dumps({
        "temperature": 0.95,
        "top_p": 0.8,
        "penalty_score": 1,
        "enable_system_memory": False,
        "disable_search": False,
        "enable_citation": False,
        "response_format": "text",
        "messages": [{"role": "user", "content": query}]
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            return response.json().get('result', '')
        except ValueError:
            return "响应内容不是有效的 JSON"
    else:
        return f"请求失败，状态码: {response.status_code}"


def determine_main_entity_type(file_content):
    """调用文心一言 API 识别文件的主体类型"""
    query = f"请分析以下文本的主体，它主要描述的对象是哪种类别？类别包括：{', '.join(CATEGORIES)}。\n请只返回一个类别名称，不要解释或附加其他内容。\n文本内容如下：\n{file_content[:10000]}..."
    category = call_wenxin_api(query).strip()

    # 确保返回的类别在预定义的列表中
    if category not in CATEGORIES:
        category = "Uncategorized"

    return category


def sanitize_instruction(instruction):
    """去除 instruction 字段开头的 '问题：'"""
    return re.sub(r"^问题[:：]\s*", "", instruction).strip()


import re


def process_output(output):
    """解析 API 返回的问答对，并保留置信度在 output 里"""
    #print(f"原始 API 返回内容:\n{output}\n")

    qa_pairs = []

    # 支持 "问题X："、"问题X:"、"问题："、"问题:"
    question_pattern = re.compile(r"(问题\d*|问题)[:：](.+)")
    answer_pattern = re.compile(r"答案[:：](.+)")

    output_lines = output.strip().split("\n")
    question = None
    answer = []

    for line in output_lines:
        line = line.strip()

        # 匹配问题
        question_match = question_pattern.match(line)
        if question_match:
            # 处理上一个问答对
            if question and answer:
                answer_text = " ".join(answer).strip()
                qa_pairs.append({
                    "instruction": question,
                    "input": "",
                    "output": answer_text
                })

            question = question_match.group(2).strip()
            answer = []
            continue

        # 匹配答案
        answer_match = answer_pattern.match(line)
        if answer_match:
            answer.append(answer_match.group(1).strip())
            continue

        # 处理连续的答案行
        if question and line:
            answer.append(line)

    # 处理最后一个问答对
    if question and answer:
        answer_text = " ".join(answer).strip()
        qa_pairs.append({
            "instruction": question,
            "input": "",
            "output": answer_text
        })

    return qa_pairs


def load_input_files(input_path):
    """加载输入文件"""
    file_paths = []
    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                file_paths.append(os.path.join(root, file))
    elif os.path.isfile(input_path):
        file_paths.append(input_path)
    else:
        raise ValueError(f"{input_path} 不是有效的文件或目录")

    data = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        data.append({"file_path": file_path, "content": content})
    return data


def save_to_json(data, output_path, overwrite=False):
    """保存数据到 JSON 文件，如果 overwrite=True 则覆盖，否则追加"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if overwrite:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        existing_data.extend(data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)


def main(input_path, output_path, prompt_dir):
    """主函数，处理所有输入文件"""
    file_list = load_input_files(input_path)
    first_file = True  # 记录是否是第一个文件

    for item in tqdm(file_list, desc="处理输入文件"):
        file_content = item['content']
        file_name = os.path.basename(item['file_path'])

        # 确定文件的主体类型
        file_entity_type = determine_main_entity_type(file_content)
        print(f"文件 {file_name} 的主体类型是：{file_entity_type}")

        # 读取对应类别的 Prompt 文件
        prompt_file = os.path.join(prompt_dir, f"{file_entity_type}.txt")
        if not os.path.exists(prompt_file):
            prompt_file = os.path.join(prompt_dir, "Uncategorized.txt")

        with open(prompt_file, "r", encoding="utf-8") as f:
            instruction_template = f.read()

        # 生成最终的 query
        query = instruction_template.format(file_name=file_name, content=file_content)

        # 调用 API 获取问答对
        try:
            output = call_wenxin_api(query)
            #print(f"API 返回内容:\n{output}\n")  # 调试用
        except Exception as e:
            print(f"调用 API 失败: {e}")
            output = ""

        # 处理 API 响应并解析问答对
        qa_pairs = process_output(output)
        valid_pairs = [pair for pair in qa_pairs if pair['output']]

        # **第一个文件覆盖，后续文件追加**
        if valid_pairs:
            save_to_json(valid_pairs, output_path, overwrite=first_file)

        first_file = False  # 之后的文件都要追加


if __name__ == "__main__":
    input_path = OUTPUT3_DIR
    output_path = os.path.join(OUTPUT4_DIR, "alpaca_dataset.json")  # 正确拼接文件路径
    prompt_dir = PROMPTS_DIR

    #main(input_path, output_path, prompt_dir)
