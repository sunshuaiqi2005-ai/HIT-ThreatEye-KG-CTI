from flask import Blueprint, render_template, request, jsonify
import logging
from pathlib import Path
from .data_processor import DataProcessor
from .corpus_generator import CorpusGenerator
import os
import PyPDF2
from bs4 import BeautifulSoup
import requests
import json
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 文心一言 API 配置
ERNIE_API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
ERNIE_API_KEY = "kz0xya0zn9ZohnO1cVdxPURx"  # 使用已有的 API 密钥
ERNIE_SECRET_KEY = "KJ7AyaVZnYDekeMEdoycS8K6MkuZGmby"  # 使用已有的密钥

# 默认提示词
DEFAULT_INSTRUCTION = """Please identify the following types of entities and then extract the relationships between these extracted entities:
Entities: (Attack Pattern, Campaign, Identity, Indicator, Infrastructure, Location, Malware, Observed Data, Threat Actor, Tool, Vulnerability, misc)
Relationship: (attributed to, impersonates, indicates, authored by, beacons to, exfiltrate to, located at, based on, targets, uses, delivers, exploits, has, originates from, consists of, communicates with, hosts, owns, downloads, drops, controls, compromises, variant of, else)
In addition to identifying the entities and relationships, please provide a confidence score for each entity and relationship in your output. The confidence score should be a number between 0 and 1, where 1 represents the highest confidence in the prediction and 0 represents the lowest confidence. If there are no entities and relationships pertaining to the specified types, please state 'No related entities and relations'. Make sure to follow the output format shown in the following example.
Input: A hitherto unknown attack group has been observed targeting a materials research organization in Asia. The group, which Symantec calls Clasiopa, is characterized by a distinct toolset, which includes one piece of custom malware (Backdoor.Atharvan). At present, there is no firm evidence on where Clasiopa is based or whom it acts on behalf.
Output: Named Entities: (Clasiopa,Threat Actor,0.95),(custom malware, Tool,0.75),(Backdoor.Atharvan, Malware,0.85)...\nRelationships: (Clasiopa, uses, custom malware,0.88),(custom malware, has, Backdoor.Atharvan,0.91)..."""

def get_access_token():
    """获取文心一言 API 的访问令牌"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": ERNIE_API_KEY,
        "client_secret": ERNIE_SECRET_KEY
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

def process_file_content(content, instruction=DEFAULT_INSTRUCTION):
    """处理文件内容并返回文心一言的原始输出"""
    try:
        # 获取访问令牌
        access_token = get_access_token()
        if not access_token:
            raise Exception("无法获取文心一言 API 访问令牌")

        # 准备请求
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"{instruction}\n\nInput: {content}"
                }
            ]
        }

        # 发送请求到文心一言 API
        response = requests.post(
            f"{ERNIE_API_URL}?access_token={access_token}",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"文心一言 API 请求失败: {response.text}")

        result = response.json()
        return result.get("result", ""), []  # 返回空错误列表以保持接口一致

    except Exception as e:
        logger.error(f"处理文件内容时出错: {str(e)}")
        raise

# 创建蓝图
dp_bp = Blueprint('data_processing', __name__,
                 template_folder='templates',
                 static_folder='static')

# 初始化处理器
data_processor = DataProcessor(
    api_key=ERNIE_API_KEY,
    secret_key=ERNIE_SECRET_KEY
)

corpus_generator = CorpusGenerator(
    api_key=ERNIE_API_KEY,
    secret_key=ERNIE_SECRET_KEY
)

@dp_bp.route('/')
def index():
    """渲染数据处理页面"""
    return render_template('data_processing/index.html')

@dp_bp.route('/corpus')
def corpus():
    """渲染语料生成页面"""
    return render_template('data_processing/corpus.html')

# 数据处理相关路由
@dp_bp.route('/api/process-file', methods=['POST'])
def process_file():
    print("!!! 这是唯二的 process_file 路由 !!!")
    """处理单个文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        # 保存上传的文件
        upload_dir = Path('uploads')
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        file.save(file_path)
        
        # 读取文件内容
        content = ""
        if str(file_path).lower().endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    content += page.extract_text()
        elif str(file_path).lower().endswith(('.html', '.htm')):
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                content = soup.get_text()
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
            
        # 获取提示词
        instruction = DEFAULT_INSTRUCTION
        if 'instruction_file' in request.files and request.files['instruction_file'].filename != '':
            instruction_file = request.files['instruction_file']
            instruction = instruction_file.read().decode('utf-8')
            
        # 处理文件内容
        llm_raw_output, errors = process_file_content(content, instruction)
        
        print("最终返回给前端的 llm_raw_output：", llm_raw_output)
        return jsonify({
            'llm_raw_output': llm_raw_output,
            'errors': errors
        })
        
    except Exception as e:
        print("捕获到异常：", e)
        logger.error(f"处理文件时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dp_bp.route('/api/process-directory', methods=['POST'])
def process_directory():
    """处理整个目录"""
    try:
        data = request.get_json()
        if not data or 'directory' not in data:
            return jsonify({'error': '未提供目录路径'}), 400
            
        directory = data['directory']
        entities, relationships = data_processor.process_directory(directory)
        
        return jsonify({
            'entities': entities,
            'relationships': relationships
        })
        
    except Exception as e:
        print("捕获到异常：", e)
        logger.error(f"处理目录时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 语料生成相关路由
@dp_bp.route('/api/generate-corpus', methods=['POST'])
def generate_corpus():
    """生成语料"""
    print("!!! 这是语料生成路由 !!!")
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        # 创建临时目录
        temp_dir = Path('temp_uploads')
        temp_dir.mkdir(exist_ok=True)
        
        # 保存上传的文件
        file_path = temp_dir / file.filename
        file.save(file_path)
        
        # 创建输出目录
        output_dir = Path('output/corpus')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件路径
        output_filename = f"corpus_{int(time.time())}.json"
        output_path = output_dir / output_filename
        
        # 获取 prompts 目录的绝对路径
        prompts_dir = Path(__file__).parent / 'prompts'
        print("prompts_dir:", prompts_dir)
        
        print("开始生成语料")
        # 调用语料生成器
        corpus_generator.main(str(file_path), str(output_path), str(prompts_dir))
        
        # 读取生成的文件内容
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                output_content = json.load(f)
                print("读取到的内容：", output_content)
        except Exception as e:
            logger.error(f"读取输出文件失败: {str(e)}")
            output_content = []
        
        # 清理临时文件
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': output_content
        })
        
    except Exception as e:
        print("捕获到异常：", e)
        logger.error(f"生成语料时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@dp_bp.route('/api/save-corpus', methods=['POST'])
def save_corpus():
    """保存生成的语料"""
    try:
        data = request.get_json()
        print(data)
        if not data or 'corpus' not in data or 'output_path' not in data:
            return jsonify({'error': '缺少必要参数'}), 400
            
        corpus = data['corpus']
        print(corpus)
        output_path = data['output_path']
        print(output_path)
        corpus_generator.save_corpus(corpus, output_path)
        
        return jsonify({'message': '语料保存成功'})
        
    except Exception as e:
        print("捕获到异常：", e)
        logger.error(f"保存语料时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_file():
    ...
    print("views.py 返回的 llm_raw_output：", llm_raw_output)
    return jsonify({
        'llm_raw_output': llm_raw_output,
        'errors': errors
    }) 