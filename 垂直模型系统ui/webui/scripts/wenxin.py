import requests
import json
import os
import pdfprocessor # PDF 解析模块
import argparse
import logging
from tqdm import tqdm  # 进度条库

# 配置日志
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API 相关配置
API_KEY = "kz0xya0zn9ZohnO1cVdxPURx"
SECRET_KEY = "KJ7AyaVZnYDekeMEdoycS8K6MkuZGmby"
LLM_BASE_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token="
ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
LLM_HEADERS = {'Content-Type': 'application/json'}
ACCESS_PARAMS = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": SECRET_KEY
}

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/uploads"))
OUTPUT1_DIR = os.path.join(BASE_DIR, "output1")
OUTPUT2_DIR = os.path.join(BASE_DIR, "output2")
OUTPUT3_DIR = os.path.join(BASE_DIR, "output3")
PDF_LIST_FILE = os.path.abspath(os.path.join(BASE_DIR, "../utils/pdf_files.txt"))

# 确保目录存在
for dir_path in [OUTPUT1_DIR, OUTPUT2_DIR, OUTPUT3_DIR]:
    os.makedirs(dir_path, exist_ok=True)
def get_access_token():
    """
    获取访问令牌（Access Token）
    """
    try:
        response = requests.post(ACCESS_TOKEN_URL, params=ACCESS_PARAMS)
        response.raise_for_status()  # 如果请求失败会抛出异常
        token = response.json().get("access_token")
        return str(token) if token else None
    except requests.RequestException as e:
        logging.error(f"获取 Access Token 失败: {str(e)}")
        return None


def querying(query) -> str:
    """
    调用文心一言 API 进行文本分析
    """
    access_token = get_access_token()
    if not access_token:
        return ""

    LLM_URL = LLM_BASE_URL + access_token

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

    try:
        response = requests.post(LLM_URL, headers=LLM_HEADERS, data=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('result', '')
    except requests.RequestException as e:
        logging.error(f"API 请求失败: {str(e)}")
        return ""


def load_pdf_filenames(pdf_list_file):
    """
    从 txt 文件中读取需要处理的 PDF 文件名。
    """
    try:
        with open(pdf_list_file, "r", encoding="utf-8") as f:
            return {os.path.basename(line.strip()) for line in f.readlines()}
    except Exception as e:
        logging.error(f"无法读取 PDF 列表文件: {str(e)}")
        return set()

def total(inputDirPath, outputDirPath, instruction, pdf_filenames):
    """
    读取 PDF 文件，提取文本并调用 LLM 进行分析，保存输出结果
    """
    file_list = [
        os.path.join(root, filename)
        for root, _, filenames in os.walk(inputDirPath)
        for filename in filenames
        if filename in pdf_filenames  # 只处理 pdf_files.txt 里列出的文件
    ]

    with tqdm(total=len(file_list), desc="Processing Files", unit="file") as pbar:
        for path in file_list:
            try:
                filename = os.path.basename(path)
                textlist = pdfprocessor.getPdfText(path, 10000)  # 解析 PDF 文本
                seq = 0

                for text in textlist:
                    query = instruction + '\n' + text
                    answer = querying(query)

                    # 过滤无效的回答
                    if answer and not answer.startswith("No related entities and relations") and not \
                            answer.startswith("Named Entities: (No related entities and relations)"):
                        targetName = pdfprocessor.genTargetFilename(filename, seq)
                        targetPath = os.path.join(outputDirPath, targetName)

                        with open(targetPath, 'w+', encoding='utf-8') as file:
                            file.write(answer)

                        seq += 1

            except Exception as e:
                logging.error(f"处理 {filename} 失败: {str(e)}")

            pbar.update(1)  # 更新进度条

def main1():
    # 处理命令行参数
    parser = argparse.ArgumentParser(description="文心一言提取框架")
    parser.add_argument('-i', type=str, help='输入文件目录', required=False, default=UPLOADS_DIR)
    parser.add_argument('-e', type=str, help='指令文件路径', required=False, default=os.path.join(BASE_DIR, "default.txt"))  # 默认指令文件路径)
    parser.add_argument('-o', type=str, help='大模型输出路径', required=False, default=OUTPUT1_DIR)
    parser.add_argument('-l', type=str, help='PDF 文件列表路径', required=False, default=PDF_LIST_FILE)

    args = parser.parse_args()

    # 读取指令文件
    try:
        with open(args.e, "r", encoding='utf-8') as f:
            instruction = '\n'.join(f.readlines())
    except Exception as e:
        logging.error(f"无法读取指令文件: {str(e)}")
        exit(1)

    # 读取需要处理的 PDF 文件名
    pdf_filenames = load_pdf_filenames(args.l)
    print(pdf_filenames)

    # 运行
    total(args.i, args.o, instruction, pdf_filenames)



def merge_files_by_prefix(input_dir, output_dir):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 用于存储文件名前缀到文件对象的映射
    prefix_to_file = {}

    # 遍历输入目录中的所有文件
    for filename in sorted(os.listdir(input_dir)):
        # 提取文件名前缀（忽略数字和后缀）
        prefix = '_'.join(filename.split('_')[:-2]) if '_o' in filename else filename

        # 检查是否已经打开了该前缀对应的文件
        if prefix not in prefix_to_file:
            # 打开一个新的输出文件
            output_filename = f"{prefix.replace(' ', '_').replace('#', '')}.txt"
            output_file = open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8')
            prefix_to_file[prefix] = output_file

        # 读取文件内容
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as infile:
            in_entities = False
            in_relationships = False
            for line in infile:
                stripped_line = line.strip()
                if stripped_line == "Named Entities:":
                    in_entities = True
                    in_relationships = False
                    prefix_to_file[prefix].write(line + '\n')
                elif stripped_line == "Relationships:":
                    in_entities = False
                    in_relationships = True
                    prefix_to_file[prefix].write(line + '\n')
                elif in_entities or in_relationships:
                    prefix_to_file[prefix].write(line + '\n')

    # 关闭所有打开的文件
    for file in prefix_to_file.values():
        file.close()


def clear_pdf_list_file(pdf_list_file):
    """
    清空 pdf_files.txt 文件内容
    """
    try:
        with open(pdf_list_file, 'w', encoding='utf-8') as f:
            f.truncate(0)  # 清空文件内容
        print(f"已清空文件：{pdf_list_file}")
    except Exception as e:
        print(f"清空 pdf_files.txt 时发生错误: {str(e)}")

def main2():
    # 使用示例
    input_directory = OUTPUT1_DIR  # 替换为你的输入目录路径
    output_directory = OUTPUT2_DIR  # 替换为你希望保存合并结果的输出目录路径

    # 合并文件
    merge_files_by_prefix(input_directory, output_directory)

    print(f"Files have been merged into {output_directory}")
    clear_pdf_list_file(PDF_LIST_FILE)


def extract_entities_and_relationships(file_path):
    entities = []
    relationships = []
    in_entities = False
    in_relationships = False

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            stripped_line = line.strip()
            if stripped_line.startswith('Named Entities:'):
                in_entities = True
                in_relationships = False
            elif stripped_line.startswith('Relationships:'):
                in_entities = False
                in_relationships = True
            elif in_entities and stripped_line:  # Check if the line is not empty
                entities.append(stripped_line)
            elif in_relationships and stripped_line:  # Check if the line is not empty
                relationships.append(stripped_line)

    return entities, relationships

def write_output_file(input_file_path, output_dir, entities, relationships):
    base_name = os.path.basename(input_file_path)
    output_file_path = os.path.join(output_dir, base_name)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        # Write entities (you can format them as needed)
        if entities:
            file.write('Named Entities:\n')
            for entity in entities:
                file.write(f'{entity}\n')
            file.write('\n')  # Add a newline for separation

        # Write relationships (you can format them as needed)
        if relationships:
            file.write('Relationships:\n')
            for relationship in relationships:
                file.write(f'{relationship}\n')

def process_input_files(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):  # Or whatever file extension you are using
            input_file_path = os.path.join(input_dir, filename)
            entities, relationships = extract_entities_and_relationships(input_file_path)
            write_output_file(input_file_path, output_dir, entities, relationships)


def main3():
    input_directory = OUTPUT2_DIR  # Replace with the actual path
    output_directory = OUTPUT3_DIR  # Replace with the actual path
    process_input_files(input_directory, output_directory)

if __name__ == "__main__":

    #main1()
    #main2()
    main3()