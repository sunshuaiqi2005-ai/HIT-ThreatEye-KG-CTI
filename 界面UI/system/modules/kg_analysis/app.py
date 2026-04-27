from flask import Blueprint, render_template, request, jsonify
from .utils import create_graph_connection, find_activities, analyze_attack_chain, analyze_attacker, analyze_locations
from .graph_operations import GraphOperations
import re
import json

# 创建蓝图，指定模板文件夹
kg_bp = Blueprint('kg_analysis', __name__, template_folder='templates')

# 创建图数据库连接
graph = create_graph_connection()
graph_ops = GraphOperations(graph)

@kg_bp.route('/')
def index():
    """渲染主页"""
    return render_template('kg_analysis/index.html')

@kg_bp.route('/manage')
def manage():
    """渲染图谱管理页面"""
    return render_template('kg_analysis/graph_management.html')

@kg_bp.route('/api/activities')
def api_activities():
    """获取活动分析数据"""
    try:
        name = request.args.get("name", "")
        records = find_activities(graph, name)
        data = []
        for rec in records:
            rels = rec.get("attack_relations", [])
            targets = rec.get("attack_targets", [])
            rel_info = []
            for rel in rels:
                try:
                    rel_info.append({
                        "type": rel["type"],
                        "threat_score": rel["threat_score"]
                    })
                except:
                    rel_info.append({})

            target_info = []
            for node in targets:
                target_info.append({
                    "name": node,
                    "relation_type": "Targets"
                })

            data.append({
                "attack_relations": rel_info,
                "attack_targets": target_info
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@kg_bp.route('/api/attack-chain')
def api_attack_chain():
    """获取攻击链分析数据"""
    try:
        name = request.args.get("name", "")
        records = analyze_attack_chain(graph, name)
        data = []
        for rec in records:
            nodes = rec.get("chain_nodes", [])
            relations = rec.get("chain_relations", [])
            node_names = [n.get("name", "未知") for n in nodes if hasattr(n, "get")]
            relation_types = [type(r).__name__ for r in relations]
            path_str = " → ".join(node_names)
            score = rec.get("weighted_threat_score", 0)
            data.append({
                "path": path_str,
                "score": round(score, 2),
                "relation_types": relation_types
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@kg_bp.route('/api/attacker-network')
def api_attacker_network():
    """获取攻击者网络数据"""
    try:
        name = request.args.get('name', '')
        if not name:
            return jsonify([])

        # 查询与目标节点相关的所有关系
        query = """
        MATCH (s)-[r]->(t)
        WHERE s.name = $name
        AND s.name IS NOT NULL AND t.name IS NOT NULL
        RETURN s.name AS source, t.name AS target, type(r) AS relation_type
        LIMIT 100
        """
        
        results = []
        for record in graph.run(query, name=name):
            # 确保所有必要的字段都存在
            if record["source"] and record["target"] and record["relation_type"]:
                results.append({
                    "source": str(record["source"]),
                    "target": str(record["target"]),
                    "relation_type": str(record["relation_type"])
                })
        
        print("API返回数据:", results)  # 添加调试信息
        return jsonify(results)
    except Exception as e:
        print("API错误:", str(e))  # 添加错误信息
        return jsonify({"error": str(e)}), 500

@kg_bp.route('/api/geo-map')
def api_geo_map():
    """获取地理位置分析数据"""
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'error': '请提供实体名称'}), 400
            
        records = analyze_locations(graph, name)
        data = []
        for rec in records:
            data.append({
                "threat": rec["threats"]["name"],
                "location": rec["locations"]["name"],
                "relation_type": "Located At"
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@kg_bp.route('/api/node', methods=['POST'])
def create_node():
    """创建节点"""
    try:
        data = request.get_json()
        name = data.get('name')
        labels = data.get('labels', [])
        properties = data.get('properties', {})
        
        if not name:
            return jsonify({'error': '请提供节点名称'}), 400
            
        result = graph_ops.create_node(name, labels, properties)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/node/<name>', methods=['PUT'])
def update_node(name):
    """更新节点"""
    try:
        data = request.get_json()
        properties = data.get('properties', {})
        
        result = graph_ops.update_node(name, properties)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/node/<name>', methods=['DELETE'])
def delete_node(name):
    """删除节点"""
    try:
        result = graph_ops.delete_node(name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/relationship', methods=['POST'])
def create_relationship():
    """创建关系"""
    try:
        data = request.get_json()
        from_node = data.get('from_node')
        to_node = data.get('to_node')
        type = data.get('type')
        properties = data.get('properties', {})
        
        if not all([from_node, to_node, type]):
            return jsonify({'error': '请提供完整的节点和关系信息'}), 400
            
        result = graph_ops.create_relationship(from_node, to_node, type, properties)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/relationship', methods=['PUT'])
def update_relationship():
    """更新关系"""
    try:
        data = request.get_json()
        from_node = data.get('from_node')
        to_node = data.get('to_node')
        type = data.get('type')
        properties = data.get('properties', {})
        
        if not all([from_node, to_node, type]):
            return jsonify({'error': '请提供完整的节点和关系信息'}), 400
            
        result = graph_ops.update_relationship(from_node, to_node, type, properties)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/relationship', methods=['DELETE'])
def delete_relationship():
    """删除关系"""
    try:
        data = request.get_json()
        from_node = data.get('from_node')
        to_node = data.get('to_node')
        type = data.get('type')
        
        if not all([from_node, to_node, type]):
            return jsonify({'error': '请提供完整的节点和关系信息'}), 400
            
        result = graph_ops.delete_relationship(from_node, to_node, type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kg_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传和解析"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': '请提供文件内容'}), 400
            
        # 解析文件内容
        entities = []
        relationships = []
        
        # 分离实体和关系部分
        parts = content.split('\n\n')
        for part in parts:
            if 'Named Entities:' in part:
                # 解析实体
                entity_lines = part.replace('Named Entities:', '').strip().split('\n')
                for line in entity_lines:
                    if line.strip():
                        # 提取实体信息
                        match = re.match(r'\((.*?),(.*?),(.*?)\)', line.strip())
                        if match:
                            name = match.group(1).strip()
                            labels = [l.strip() for l in match.group(2).split(',')]
                            confidence = float(match.group(3).strip())
                            entities.append({
                                'name': name,
                                'labels': labels,
                                'properties': {'confidence': confidence}
                            })
            elif 'Relationships:' in part:
                # 解析关系
                rel_lines = part.replace('Relationships:', '').strip().split('\n')
                for line in rel_lines:
                    if line.strip():
                        # 提取关系信息
                        match = re.match(r'\((.*?),(.*?),(.*?),(.*?)\)', line.strip())
                        if match:
                            from_node = match.group(1).strip()
                            type = match.group(2).strip()
                            to_node = match.group(3).strip()
                            confidence = float(match.group(4).strip())
                            relationships.append({
                                'from_node': from_node,
                                'to_node': to_node,
                                'type': type,
                                'properties': {'confidence': confidence}
                            })
        
        # 创建节点和关系
        for entity in entities:
            graph_ops.create_node(
                entity['name'],
                entity['labels'],
                entity['properties']
            )
            
        for rel in relationships:
            graph_ops.create_relationship(
                rel['from_node'],
                rel['to_node'],
                rel['type'],
                rel['properties']
            )
            
        return jsonify({
            'message': '文件导入成功',
            'entities': len(entities),
            'relationships': len(relationships)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 