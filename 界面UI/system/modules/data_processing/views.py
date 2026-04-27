import os
import logging
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from . import pdfprocessor
from .data_processor import process_file_content
from .corpus_generator import generate_corpus
import json
import time
from flask import current_app

# 配置日志
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

data_processing = Blueprint('data_processing', __name__)

# 设置默认的输出目录
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output')
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

# 默认提示词
DEFAULT_INSTRUCTION = """Please identify the following types of entities and then extract the relationships between these extracted entities:
Entities: (Attack Pattern, Campaign, Identity, Indicator, Infrastructure, Location, Malware, Observed Data, Threat Actor, Tool, Vulnerability, misc)
Relationship: (attributed to, impersonates, indicates, authored by, beacons to, exfiltrate to, located at, based on, targets, uses, delivers, exploits, has, originates from, consists of, communicates with, hosts, owns, downloads, drops, controls, compromises, variant of, else)
In addition to identifying the entities and relationships, please provide a confidence score for each entity and relationship in your output. The confidence score should be a number between 0 and 1, where 1 represents the highest confidence in the prediction and 0 represents the lowest confidence. If there are no entities and relationships pertaining to the specified types, please state 'No related entities and relations'. Make sure to follow the output format shown in the following example.
Input: A hitherto unknown attack group has been observed targeting a materials research organization in Asia. The group, which Symantec calls Clasiopa, is characterized by a distinct toolset, which includes one piece of custom malware (Backdoor.Atharvan). At present, there is no firm evidence on where Clasiopa is based or whom it acts on behalf.
Output: Named Entities: (Clasiopa,Threat Actor,0.95),(custom malware, Tool,0.75),(Backdoor.Atharvan, Malware,0.85)...\nRelationships: (Clasiopa, uses, custom malware,0.88),(custom malware, has, Backdoor.Atharvan,0.91)..."""

def parse_entity_line(line):
    """解析实体行"""
    try:
        # 移除括号和空格
        line = line.strip('()').strip()
        # 分割字段，但保留引号内的逗号
        parts = []
        current_part = []
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current_part.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current_part).strip())
                current_part = []
            else:
                current_part.append(char)
                
        if current_part:
            parts.append(''.join(current_part).strip())
            
        # 清理引号
        parts = [part.strip('"\'') for part in parts]
        
        if len(parts) >= 3:
            # 验证实体类型
            valid_types = {
                'Attack Pattern', 'Campaign', 'Identity', 'Indicator', 
                'Infrastructure', 'Location', 'Malware', 'Observed Data', 
                'Threat Actor', 'Tool', 'Vulnerability', 'misc'
            }
            
            entity_type = parts[1]
            if entity_type not in valid_types:
                logging.warning(f"未知的实体类型: {entity_type}")
                entity_type = 'misc'  # 使用misc作为默认类型
                
            return {
                'name': parts[0],
                'type': entity_type,
                'confidence': float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '').isdigit() else 1.0
            }
    except Exception as e:
        logging.error(f"解析实体行失败: {line}, 错误: {str(e)}")
    return None

def parse_relation_line(line):
    """解析关系行"""
    try:
        # 移除括号和空格
        line = line.strip('()').strip()
        # 分割字段，但保留引号内的逗号
        parts = []
        current_part = []
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current_part.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current_part).strip())
                current_part = []
            else:
                current_part.append(char)
                
        if current_part:
            parts.append(''.join(current_part).strip())
            
        # 清理引号
        parts = [part.strip('"\'') for part in parts]
        
        if len(parts) >= 4:
            # 验证关系类型
            valid_relations = {
                'attributed to', 'impersonates', 'indicates', 'authored by',
                'beacons to', 'exfiltrate to', 'located at', 'based on',
                'targets', 'uses', 'delivers', 'exploits', 'has',
                'originates from', 'consists of', 'communicates with',
                'hosts', 'owns', 'downloads', 'drops', 'controls',
                'compromises', 'variant of', 'else'
            }
            
            relation_type = parts[1]
            if relation_type not in valid_relations:
                logging.warning(f"未知的关系类型: {relation_type}")
                relation_type = 'else'  # 使用else作为默认类型
                
            return {
                'source': parts[0],
                'relation': relation_type,
                'target': parts[2],
                'confidence': float(parts[3]) if len(parts) > 3 and parts[3].replace('.', '').isdigit() else 1.0
            }
    except Exception as e:
        logging.error(f"解析关系行失败: {line}, 错误: {str(e)}")
    return None

def process_file_content(content, instruction, output_path, filename):
    """处理文件内容"""
    print("!!! 这是唯一的 process_file_content !!!")
    results = []
    errors = []
    
    try:
        # 分割文本块
        text_chunks = pdfprocessor.split_text(content, max_length=4000)
        
        for idx, chunk in enumerate(text_chunks):
            try:
                # 调用文心一言API
                query = f"{instruction}\n\n{chunk}"
                answer = pdfprocessor.querying(query)
                
                if answer and not answer.startswith("No related entities and relations"):
                    # 保存LLM生成结果
                    llm_output_file = os.path.join(output_path, f"{os.path.splitext(filename)[0]}_chunk_{idx}_llm_output.txt")
                    with open(llm_output_file, 'w', encoding='utf-8') as f:
                        f.write(f"Input:\n{chunk}\n\nOutput:\n{answer}")
                    
                    # 解析结果
                    lines = answer.strip().split('\n')
                    entities = []
                    relations = []
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # 检查是否是新的部分
                        if line.startswith('Named Entities:'):
                            current_section = 'entities'
                            continue
                        elif line.startswith('Relationships:'):
                            current_section = 'relations'
                            continue
                            
                        if line.startswith('(') and line.endswith(')'):
                            if current_section == 'entities':
                                entity = parse_entity_line(line)
                                if entity:
                                    entities.append(entity)
                                else:
                                    errors.append({
                                        'type': 'entity_parse_error',
                                        'message': f'无法解析实体行: {line}',
                                        'details': '请检查实体格式是否正确，格式应为：(name, type, confidence)'
                                    })
                            elif current_section == 'relations':
                                relation = parse_relation_line(line)
                                if relation:
                                    relations.append(relation)
                                else:
                                    errors.append({
                                        'type': 'relation_parse_error',
                                        'message': f'无法解析关系行: {line}',
                                        'details': '请检查关系格式是否正确，格式应为：(source, relation, target, confidence)'
                                    })
                    
                    if entities or relations:
                        results.append({
                            'chunk_index': idx,
                            'entities': entities,
                            'relations': relations,
                            'raw_content': answer,
                            'llm_output_file': llm_output_file
                        })
            except Exception as e:
                errors.append({
                    'type': 'chunk_processing_error',
                    'message': f'处理文本块 {idx} 失败',
                    'details': str(e)
                })
                logging.error(f"处理文本块 {idx} 失败: {str(e)}")
                
    except Exception as e:
        errors.append({
            'type': 'content_processing_error',
            'message': '处理文件内容失败',
            'details': str(e)
        })
        logging.error(f"处理文件内容失败: {str(e)}")
    
    print("!!! 这是唯一的 process_file_content !!!", id(results))
    return results, errors, [answer for answer in results if answer['raw_content']]

@data_processing.route('/')
def index():
    return render_template('data_processing/index.html')

@data_processing.route('/corpus')
def corpus():
    return render_template('data_processing/corpus.html')

@data_processing.route('/api/process-file', methods=['POST'])
def process_file():
    print("!!! 这是唯一的 process_file 路由 !!!")
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        output_path = request.form.get('output_path', DEFAULT_OUTPUT_DIR)
        if not output_path:
            output_path = DEFAULT_OUTPUT_DIR
        os.makedirs(output_path, exist_ok=True)
        instruction = DEFAULT_INSTRUCTION
        if 'instruction_file' in request.files and request.files['instruction_file'].filename != '':
            instruction_file = request.files['instruction_file']
            instruction = instruction_file.read().decode('utf-8')
        filename = secure_filename(file.filename)
        file_path = os.path.join(output_path, filename)
        file.save(file_path)
        if filename.lower().endswith('.pdf'):
            content = '\n'.join(pdfprocessor.getPdfText(file_path))
        elif filename.lower().endswith(('.html', '.htm')):
            textlist, _ = pdfprocessor.getHtmlText(file_path)
            content = '\n'.join(textlist)
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
        llm_raw_output, errors = process_file_content(content, instruction, output_path, filename)
        print("views.py 返回的 llm_raw_output：", llm_raw_output)
        return jsonify({
            'llm_raw_output': llm_raw_output,
            'errors': errors
        })
    except Exception as e:
        print("捕获到异常：", e)
        logging.error(f"处理文件失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_processing.route('/api/process-directory', methods=['POST'])
def process_directory():
    try:
        directory = request.form.get('directory')
        if not directory:
            return jsonify({'error': '没有指定目录路径'}), 400
            
        if 'instruction_file' not in request.files:
            return jsonify({'error': '没有上传提示词文件'}), 400
            
        instruction_file = request.files['instruction_file']
        if instruction_file.filename == '':
            return jsonify({'error': '没有选择提示词文件'}), 400
            
        # 获取输出路径，如果没有指定则使用默认路径
        output_path = request.form.get('output_path', DEFAULT_OUTPUT_DIR)
        if not output_path:
            output_path = DEFAULT_OUTPUT_DIR
            
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 读取提示词文件
        instruction = instruction_file.read().decode('utf-8')
        
        # 获取目录中的所有文件
        file_list = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.pdf', '.html', '.htm')):
                    file_list.append(os.path.join(root, file))
                    
        if not file_list:
            return jsonify({'error': '目录中没有找到支持的文件'}), 400
            
        all_results = []
        all_errors = []
        
        # 处理每个文件
        for file_path in file_list:
            try:
                filename = os.path.basename(file_path)
                
                # 根据文件类型处理
                if filename.lower().endswith('.pdf'):
                    content = '\n'.join(pdfprocessor.getPdfText(file_path))
                elif filename.lower().endswith(('.html', '.htm')):
                    textlist, _ = pdfprocessor.getHtmlText(file_path)
                    content = '\n'.join(textlist)
                else:
                    continue
                    
                # 处理内容
                results, errors = process_file_content(content, instruction, output_path, filename)
                
                # 添加文件名到结果中
                for result in results:
                    result['filename'] = filename
                    
                all_results.extend(results)
                all_errors.extend(errors)
                
                # 保存单个文件的结果
                output_file = os.path.join(output_path, f"{os.path.splitext(filename)[0]}_result.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'results': results,
                        'errors': errors
                    }, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                all_errors.append({
                    'type': 'file_processing_error',
                    'message': f'处理文件 {filename} 失败',
                    'details': str(e)
                })
                logging.error(f"处理文件 {filename} 失败: {str(e)}")
                
        return jsonify({
            'message': '批量处理完成',
            'results': all_results,
            'errors': all_errors
        })
        
    except Exception as e:
        logging.error(f"批量处理失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_processing.route('/api/generate-corpus', methods=['POST'])
def generate_corpus():
    """生成语料的API接口"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未上传文件'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'})
            
        # 保存上传的文件
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_path)
        
        # 生成输出文件路径
        output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'corpus')
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"corpus_{int(time.time())}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # 初始化语料生成器
        generator = CorpusGenerator()
        
        # 生成语料
        generator.main(temp_path, output_path, os.path.join(current_app.root_path, 'prompts'))
        
        # 读取生成的文件内容
        with open(output_path, 'r', encoding='utf-8') as f:
            output_content = json.load(f)
        
        # 清理临时文件
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'data': output_content
        })
        
    except Exception as e:
        current_app.logger.error(f"生成语料时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@data_processing.route('/api/download/<path:filename>')
def download_file(filename):
    try:
        return send_from_directory(DEFAULT_OUTPUT_DIR, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"下载文件失败: {str(e)}")
        return jsonify({'error': str(e)}), 500 