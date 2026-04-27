import logging
from typing import List, Dict
import requests
import json
from pathlib import Path
import os
import re
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 文心一言 API 配置
API_KEY = "kz0xya0zn9ZohnO1cVdxPURx"
SECRET_KEY = "KJ7AyaVZnYDekeMEdoycS8K6MkuZGmby"

CATEGORIES = ["Malware", "Threat_Actors", "Campaign", "Reports", "Targets", "Vulnerabilities", "Uncategorized"]

class CorpusGenerator:
    """语料生成器类，用于生成训练语料"""
    
    def __init__(self, api_key=None, secret_key=None):
        """初始化语料生成器"""
        self.api_key = api_key or API_KEY
        self.secret_key = secret_key or SECRET_KEY
        # 获取当前文件所在目录的绝对路径
        self.base_dir = Path(__file__).parent.absolute()

    def get_access_token(self):
        """获取 Access Token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception("获取 access_token 失败")

    def call_wenxin_api(self, query):
        """调用文心一言 API 进行分析"""
        access_token = self.get_access_token()
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

    def generate_corpus(self, entities: List[Dict], relationships: List[Dict]) -> str:
        """生成训练语料
        
        Args:
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            str: 生成的语料文本
        """
        try:
            # 构建提示词
            prompt = self._build_generation_prompt(entities, relationships)
            
            # 调用API生成语料
            return self.call_wenxin_api(prompt)
            
        except Exception as e:
            logging.error(f"生成语料时出错: {str(e)}")
            return ""
            
    def save_corpus(self, corpus: str, output_path: str):
        """保存生成的语料
        
        Args:
            corpus: 语料文本
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存语料
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(corpus)
                
            logging.info(f"语料已保存到: {output_path}")
            
        except Exception as e:
            logging.error(f"保存语料时出错: {str(e)}")
            
    def _build_generation_prompt(self, entities: List[Dict], relationships: List[Dict]) -> str:
        """构建生成提示词
        
        Args:
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            str: 提示词
        """
        # 格式化实体和关系
        entities_str = "\n".join([
            f"- {e['name']} ({e['type']})"
            for e in entities
        ])
        
        relationships_str = "\n".join([
            f"- {r['source']} {r['type']} {r['target']}"
            for r in relationships
        ])
        
        return f"""请根据以下实体和关系生成一段自然语言描述：

实体：
{entities_str}

关系：
{relationships_str}

要求：
1. 使用流畅的自然语言描述这些实体和关系
2. 保持专业性和准确性
3. 适当添加上下文信息
4. 使用合适的连接词和过渡语
5. 确保所有实体和关系都被包含在描述中
"""

    def determine_main_entity_type(self, file_content):
        """调用文心一言 API 识别文件的主体类型"""
        query = f"请分析以下文本的主体，它主要描述的对象是哪种类别？类别包括：{', '.join(CATEGORIES)}。\n请只返回一个类别名称，不要解释或附加其他内容。\n文本内容如下：\n{file_content[:10000]}..."
        category = self.call_wenxin_api(query).strip()

        # 确保返回的类别在预定义的列表中
        if category not in CATEGORIES:
            category = "Uncategorized"

        return category

    def sanitize_instruction(self, instruction):
        """去除 instruction 字段开头的 '问题：'"""
        return re.sub(r"^问题[:：]\s*", "", instruction).strip()

    def process_output(self, output):
        """解析 API 返回的问答对，并保留置信度在 output 里"""
        print(f"原始 API 返回内容:\n{output}\n")

        qa_pairs = []
        current_question = None
        current_answer = []

        # 按行处理输出
        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # 检查是否是新的问题
            if line.startswith('问题') and '：' in line:
                # 如果已经有问题和答案，保存当前的问答对
                if current_question and current_answer:
                    qa_pairs.append({
                        "instruction": current_question,
                        "input": "",
                        "output": " ".join(current_answer).strip()
                    })
                    current_answer = []

                # 提取新问题
                current_question = line.split('：', 1)[1].strip()
                # 如果问题以 "- 问题："开头，去掉这个前缀
                if current_question.startswith('- 问题：'):
                    current_question = current_question[6:].strip()

            # 检查是否是答案
            elif line.startswith('- 答案：'):
                current_answer.append(line[6:].strip())
            # 如果已经有问题，且当前行不是新问题，则认为是答案的继续
            elif current_question and line:
                current_answer.append(line)

        # 处理最后一个问答对
        if current_question and current_answer:
            qa_pairs.append({
                "instruction": current_question,
                "input": "",
                "output": " ".join(current_answer).strip()
            })

        print(f"解析出的问答对数量: {len(qa_pairs)}")
        return qa_pairs

    def load_input_files(self, input_path):
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

    def save_to_json(self, data, output_path, overwrite=False):
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

    def main(self, input_path, output_path, prompt_dir):
        """主函数，处理所有输入文件"""
        print("开始处理文件")
        file_list = self.load_input_files(input_path)
        first_file = True  # 记录是否是第一个文件

        for item in tqdm(file_list, desc="处理输入文件"):
            file_content = item['content']
            file_name = os.path.basename(item['file_path'])

            # 确定文件的主体类型
            file_entity_type = self.determine_main_entity_type(file_content)
            logger.info(f"文件 {file_name} 的主体类型是：{file_entity_type}")

            # 读取对应类别的 Prompt 文件
            prompt_file = Path(prompt_dir) / f"{file_entity_type}.txt"
            print(f"尝试读取提示词文件: {prompt_file}")
            if not prompt_file.exists():
                prompt_file = Path(prompt_dir) / "Uncategorized.txt"
                print(f"提示词文件不存在，使用默认文件: {prompt_file}")
                if not prompt_file.exists():
                    raise FileNotFoundError(f"找不到提示词模板文件: {prompt_file}")

            with open(prompt_file, "r", encoding="utf-8") as f:
                instruction_template = f.read()

            # 生成最终的 query
            query = instruction_template.format(file_name=file_name, content=file_content)

            # 调用 API 获取问答对
            try:
                output = self.call_wenxin_api(query)
                print("API 返回结果:", output)
            except Exception as e:
                logger.error(f"调用 API 失败: {e}")
                output = ""

            # 处理 API 响应并解析问答对
            qa_pairs = self.process_output(output)
            valid_pairs = [pair for pair in qa_pairs if pair['output']]
            print("解析后的问答对:", valid_pairs)

            # 第一个文件覆盖，后续文件追加
            if valid_pairs:
                self.save_to_json(valid_pairs, output_path, overwrite=first_file)
                print(f"保存到文件: {output_path}")

            first_file = False  # 之后的文件都要追加

        return True 