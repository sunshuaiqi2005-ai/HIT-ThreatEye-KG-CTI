import requests
import json
import os
import logging
from tqdm import tqdm
from . import pdfprocessor  # 修改为相对导入
from typing import List, Dict, Optional, Tuple
import PyPDF2 # type: ignore
from bs4 import BeautifulSoup
from pathlib import Path

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

def get_access_token():
    """获取访问令牌（Access Token）"""
    try:
        response = requests.post(ACCESS_TOKEN_URL, params=ACCESS_PARAMS)
        response.raise_for_status()
        token = response.json().get("access_token")
        return str(token) if token else None
    except requests.RequestException as e:
        logging.error(f"获取 Access Token 失败: {str(e)}")
        return None

def querying(query) -> str:
    """调用文心一言 API 进行文本分析"""
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
        llm_output = data.get('result', '')
        print(f"LLM原始输出: {llm_output}")  # 新增调试输出
        return llm_output
    except requests.RequestException as e:
        logging.error(f"API 请求失败: {str(e)}")
        return ""

def split_text(text, max_length=4000):
    """将文本拆分成小块，确保每块不会超过 max_length"""
    chunks = []
    current_chunk = ""

    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def process_file_content(content, instruction, output_path, filename):
    """只返回 LLM 原始输出字符串，不加任何前缀，也不返回列表。"""
    print("!!! 这是唯一的 process_file_content !!!")
    llm_raw_output = ""
    errors = []
    try:
        file_folder_name = os.path.splitext(filename)[0]
        file_folder_path = os.path.join(output_path, file_folder_name)
        os.makedirs(file_folder_path, exist_ok=True)
        with open(os.path.join(file_folder_path, "text.txt"), 'w', encoding='utf-8') as f:
            f.write(content)
        text_chunks = split_text(content, max_length=4000)
        for idx, chunk in enumerate(text_chunks):
            query = f"{instruction}\n\n{chunk}"
            answer = querying(query)
            llm_raw_output += f"{answer}\n\n"
            target_name = pdfprocessor.genTargetFilename(filename, idx)
            target_path = os.path.join(file_folder_path, target_name)
            with open(target_path, 'w+', encoding='utf-8') as file:
                file.write(answer)
        print("最终返回给前端的 llm_raw_output：", llm_raw_output)
        return llm_raw_output, errors
    except Exception as e:
        print("捕获到异常：", e)
        error_msg = f"处理文件 {filename} 失败: {str(e)}"
        logging.error(error_msg)
        errors.append(error_msg)
        return llm_raw_output, errors

class DataProcessor:
    """数据处理类，用于处理各种格式的文件并提取实体关系"""
    
    def __init__(self, api_key: str, secret_key: str):
        """初始化数据处理器
        
        Args:
            api_key: 文心一言API密钥
            secret_key: 文心一言密钥
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        
    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        try:
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
            response = requests.post(self.token_url, params=params)
            response.raise_for_status()
            token = response.json().get("access_token")
            return str(token) if token else None
        except Exception as e:
            logging.error(f"获取访问令牌失败: {str(e)}")
            return None
            
    def _query_llm(self, text: str) -> str:
        """调用文心一言API进行文本分析"""
        access_token = self._get_access_token()
        if not access_token:
            return ""
            
        url = f"{self.base_url}?access_token={access_token}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "temperature": 0.95,
            "top_p": 0.8,
            "penalty_score": 1,
            "enable_system_memory": False,
            "disable_search": False,
            "enable_citation": False,
            "response_format": "text",
            "messages": [{
                "role": "user",
                "content": self._build_prompt(text)
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            llm_output = data.get('result', '')
            print(f"LLM原始输出: {llm_output}")  # 新增调试输出
            return llm_output
        except Exception as e:
            logging.error(f"API请求失败: {str(e)}")
            return ""
            
    def _build_prompt(self, text: str) -> str:
        """构建提示词"""
        return f"""Please identify the following types of entities and then extract the relationships between these extracted entities:
Entities: (Attack Pattern, Campaign, Identity, Indicator, Infrastructure, Location, Malware, Observed Data, Threat Actor, Tool, Vulnerability, misc)
Relationship: (attributed to, impersonates, indicates, authored by, beacons to, exfiltrate to, located at, based on, targets, uses, delivers, exploits, has, originates from, consists of, communicates with, hosts, owns, downloads, drops, controls, compromises, variant of, else)

Please output in the following format:

Entities:
(entity_name, entity_type, confidence)

Relationships:
(source_entity, relationship_type, target_entity, confidence)

Note:
1. Confidence score should be between 0 and 1
2. If no entities or relationships are found, please state 'No related entities and relations'

Text to analyze:
{text}"""
        
    def _split_text(self, text: str, max_length: int = 4000) -> List[str]:
        """将文本拆分成小块"""
        chunks = []
        current_chunk = ""
        
        for line in text.split("\n"):
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += "\n" + line
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def _parse_llm_response(self, response: str) -> Tuple[List[Dict], List[Dict]]:
        """解析LLM响应"""
        entities = []
        relationships = []
        
        # 分割响应文本
        sections = response.split('\n\n')
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if section.startswith('Entities:'):
                current_section = 'entities'
                continue
            elif section.startswith('Relationships:'):
                current_section = 'relations'
                continue
            elif section.startswith('Note:'):  # 跳过注释部分
                break
                
            # 解析实体
            if current_section == 'entities':
                # 处理可能的多行实体
                lines = section.split('\n')
                current_entity = ""
                for line in lines:
                    line = line.strip()
                    # 跳过注释行
                    if line.startswith('#') or line.startswith('Note:'):
                        continue
                        
                    # 如果行以括号开始，说明是新实体
                    if line.startswith('('):
                        # 如果已经有未处理的实体，先处理它
                        if current_entity:
                            try:
                                # 移除括号和末尾的逗号，并清理说明部分
                                content = current_entity[1:-1].rstrip(',').split(',')
                                # 只取前三个字段，忽略说明部分
                                if len(content) >= 3:
                                    name = content[0].strip()
                                    entity_type = content[1].strip()
                                    try:
                                        confidence = float(content[2].strip())
                                    except ValueError:
                                        confidence = 1.0
                                        
                                    entity = {
                                        'name': name,
                                        'type': entity_type,
                                        'confidence': confidence
                                    }
                                    entities.append(entity)
                                    print(f"成功解析实体: {entity}")
                            except Exception as e:
                                logging.error(f"解析实体失败: {current_entity}, 错误: {str(e)}")
                        # 开始新的实体
                        current_entity = line
                    # 如果行不是以括号开始，说明是当前实体的继续
                    elif current_entity:
                        current_entity += " " + line
                        
                # 处理最后一个实体
                if current_entity:
                    try:
                        content = current_entity[1:-1].rstrip(',').split(',')
                        if len(content) >= 3:
                            name = content[0].strip()
                            entity_type = content[1].strip()
                            try:
                                confidence = float(content[2].strip())
                            except ValueError:
                                confidence = 1.0
                                
                            entity = {
                                'name': name,
                                'type': entity_type,
                                'confidence': confidence
                            }
                            entities.append(entity)
                            print(f"成功解析实体: {entity}")
                    except Exception as e:
                        logging.error(f"解析实体失败: {current_entity}, 错误: {str(e)}")
                        
            # 解析关系
            elif current_section == 'relations':
                # 处理可能的多行关系
                lines = section.split('\n')
                current_relation = ""
                for line in lines:
                    line = line.strip()
                    # 跳过注释行
                    if line.startswith('#') or line.startswith('Note:'):
                        continue
                        
                    # 如果行以括号开始，说明是新关系
                    if line.startswith('('):
                        # 如果已经有未处理的关系，先处理它
                        if current_relation:
                            try:
                                # 移除括号和末尾的逗号，并清理说明部分
                                content = current_relation[1:-1].rstrip(',').split(',')
                                # 只取前四个字段，忽略说明部分
                                if len(content) >= 4:
                                    source = content[0].strip()
                                    relation_type = content[1].strip()
                                    target = content[2].strip()
                                    try:
                                        confidence = float(content[3].strip())
                                    except ValueError:
                                        confidence = 1.0
                                        
                                    relation = {
                                        'source': source,
                                        'type': relation_type,
                                        'target': target,
                                        'confidence': confidence
                                    }
                                    relationships.append(relation)
                                    print(f"成功解析关系: {relation}")
                            except Exception as e:
                                logging.error(f"解析关系失败: {current_relation}, 错误: {str(e)}")
                        # 开始新的关系
                        current_relation = line
                    # 如果行不是以括号开始，说明是当前关系的继续
                    elif current_relation:
                        current_relation += " " + line
                        
                # 处理最后一个关系
                if current_relation:
                    try:
                        content = current_relation[1:-1].rstrip(',').split(',')
                        if len(content) >= 4:
                            source = content[0].strip()
                            relation_type = content[1].strip()
                            target = content[2].strip()
                            try:
                                confidence = float(content[3].strip())
                            except ValueError:
                                confidence = 1.0
                                
                            relation = {
                                'source': source,
                                'type': relation_type,
                                'target': target,
                                'confidence': confidence
                            }
                            relationships.append(relation)
                            print(f"成功解析关系: {relation}")
                    except Exception as e:
                        logging.error(f"解析关系失败: {current_relation}, 错误: {str(e)}")
                        
        print(f"解析结果：找到 {len(entities)} 个实体和 {len(relationships)} 个关系")
        return entities, relationships

    def process_file(self, file_path: str) -> Tuple[List[Dict], List[Dict]]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[List[Dict], List[Dict]]: 实体列表和关系列表
        """
        print("process_file 路由被调用")
        # 获取文件内容
        content = self._read_file(file_path)
        print("读取到的文件内容：", content[:200] if content else "None")  # 打印前200个字符
        if not content:
            return [], []
            
        # 拆分文本
        chunks = self._split_text(content)
        print(f"文本被分成了 {len(chunks)} 个块")
        
        all_output = []
        
        # 处理每个文本块
        for idx, chunk in enumerate(chunks):
            print(f"正在处理第 {idx+1} 个文本块")
            # 调用API提取实体和关系
            result = self._query_llm(chunk)
            print(f"LLM返回结果：{result[:200] if result else 'None'}")  # 打印前200个字符
            if result:
                all_output.append(result)
                
        # 将所有输出合并
        combined_output = "\n\n".join(all_output)
        print("最终返回给前端的输出：", combined_output)
        
        # 返回空列表，因为我们现在只关注原始输出
        return [], []
        
    def process_directory(self, dir_path: str) -> Tuple[List[Dict], List[Dict]]:
        """处理整个目录下的文件
        
        Args:
            dir_path: 目录路径
            
        Returns:
            Tuple[List[Dict], List[Dict]]: 实体列表和关系列表
        """
        all_entities = []
        all_relationships = []
        
        for file_path in Path(dir_path).rglob('*'):
            if file_path.is_file() and self._is_supported_file(file_path):
                try:
                    entities, relationships = self.process_file(str(file_path))
                    all_entities.extend(entities)
                    all_relationships.extend(relationships)
                except Exception as e:
                    logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
                    
        return all_entities, all_relationships
        
    def _read_file(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            print(f"正在读取文件：{file_path}，文件类型：{file_ext}")
            
            if file_ext == '.pdf':
                return self._read_pdf(file_path)
            elif file_ext == '.html':
                return self._read_html(file_path)
            elif file_ext == '.txt':
                return self._read_txt(file_path)
            else:
                logging.warning(f"不支持的文件类型: {file_ext}")
                return None
                
        except Exception as e:
            logging.error(f"读取文件 {file_path} 时出错: {str(e)}")
            return None
            
    def _read_pdf(self, file_path: str) -> str:
        """读取PDF文件"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"PDF文件共有 {len(pdf_reader.pages)} 页")
                for page in pdf_reader.pages:
                    text += page.extract_text()
            print(f"PDF文件读取完成，文本长度：{len(text)}")
            return text
        except Exception as e:
            print(f"PDF读取错误：{str(e)}")
            raise
        
    def _read_html(self, file_path: str) -> str:
        """读取HTML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                text = soup.get_text()
                print(f"HTML文件读取完成，文本长度：{len(text)}")
                return text
        except Exception as e:
            print(f"HTML读取错误：{str(e)}")
            raise
            
    def _read_txt(self, file_path: str) -> str:
        """读取TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                print(f"TXT文件读取完成，文本长度：{len(text)}")
                return text
        except Exception as e:
            print(f"TXT读取错误：{str(e)}")
            raise
            
    def _is_supported_file(self, file_path: Path) -> bool:
        """检查文件是否支持"""
        return file_path.suffix.lower() in ['.pdf', '.html', '.txt']
        
    # def _parse_llm_response(self, response: str) -> Tuple[List[Dict], List[Dict]]:
    #     """解析LLM响应"""
    #     entities = []
    #     relationships = []
    #     # ... 解析逻辑 ...
    #     return entities, relationships

    # def parse_entity_line(line):
    #     """解析实体行"""
    #     try:
    #         # ... 解析逻辑 ...
    #     except Exception as e:
    #         logging.error(f"解析实体行失败: {line}, 错误: {str(e)}")
    #     return None

    # def parse_relation_line(line):
    #     """解析关系行"""
    #     try:
    #         # ... 解析逻辑 ...
    #     except Exception as e:
    #         logging.error(f"解析关系行失败: {line}, 错误: {str(e)}")
    #     return None

    # def _parse_llm_response(self, response: str) -> Tuple[List[Dict], List[Dict]]:
    #     """解析LLM响应"""
    #     entities = []
    #     relationships = []
    #     # ... 解析逻辑 ...
    #     return entities, relationships 