from py2neo import Node, Relationship, Graph, NodeMatcher
from typing import List, Dict, Optional
import logging
import json
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_graph_connection(uri: str = "bolt://localhost:7687",
                            user: str = "neo4j",
                            password: str = "chenhao86031327",
                            name: str = "neo4j") -> Graph:
    """
    创建并返回Neo4j图数据库连接对象
    """
    try:
        graph = Graph(uri, auth=(user, password), name=name)
        _verify_connection(graph)
        return graph
    except Exception as e:
        logging.error(f"数据库连接失败: {str(e)}")
        raise


def _verify_connection(graph: Graph) -> None:
    """验证数据库连接有效性"""
    try:
        graph.run("MATCH (n) RETURN COUNT(n) AS node_count LIMIT 1")
    except Exception as e:
        logging.error(f"连接验证失败: {str(e)}")
        raise


def delete_disconnected_nodes(graph):
    """
    删除离散节点的最终优化版本（兼容Neo4j 5.15+）
    """
    try:
        # 删除完全孤立节点
        graph.run("""
            MATCH (n)
            WHERE NOT (n)--()
            DETACH DELETE n
        """)

        # 删除二元孤立边节点对（使用多重MATCH和WITH）
        graph.run("""
            MATCH (a)-[r]-(b)
            OPTIONAL MATCH (a)--()
            WITH a, b, COUNT(a) AS degree_a
            OPTIONAL MATCH (b)--()
            WITH a, b, degree_a, COUNT(b) AS degree_b
            WHERE degree_a = 1 AND degree_b = 1
            DETACH DELETE a, b
        """)
        print("离散节点删除完成")
    except Exception as e:
        print(f"删除过程中发生错误: {str(e)}")
        raise


def find_activities(graph: Graph, name: str) -> List[Dict]:
    """查找恶意活动行为链（优化）"""
    query = """
    MATCH path=(m:`Threat Actor`|Malware {name: $name})-[r*1..5]->(n)
    OPTIONAL MATCH (m)-[r1:Uses]->(t)
      WHERE t.name IS NOT NULL
    OPTIONAL MATCH (m)-[r2:Targets|Exploits]->(t1)
      WHERE t1.name IS NOT NULL
    RETURN 
        m.name AS malicious_entity,
        [rel IN collect(r1) | {
            type: type(rel), 
            threat_score: CASE 
                WHEN rel.threat_score IS NOT NULL THEN rel.threat_score  
                ELSE 0 
            END
        }] AS attack_relations,
        [target IN collect(DISTINCT t) | target.name] AS attack_targets,
        [rel IN collect(r2) | {
            type: type(rel), 
            threat_score: CASE 
                WHEN rel.threat_score IS NOT NULL THEN rel.threat_score  
                ELSE 0 
            END
        }] AS exploitation_relations,
        [target IN collect(DISTINCT t1) | target.name] AS exploited_entities,
        length(path) AS path_length,
        REDUCE(s=0, rel IN relationships(path) | 
            s + CASE 
                 WHEN rel.threat_score IS NOT NULL THEN rel.threat_score  
                ELSE 0 
            END
        ) AS total_threat_score
    ORDER BY total_threat_score DESC
    LIMIT 1000
    """
    try:
        result = graph.run(query, name=name)
        return [record.data() for record in result]
    except Exception as e:
        logger.error(f"分析失败 [{name}]: {str(e)}")
        raise

def analyze_attack_chain(graph: Graph, name: str) -> List[Dict]:
    """分析攻击行为链"""
    query = """
    MATCH path = (n {name: $name})-[*1..5]->(m)
    WHERE n:`Threat Actor` OR n:Malware
    RETURN 
        nodes(path) AS chain_nodes,
        relationships(path) AS chain_relations,
        length(path) AS chain_length,
        REDUCE(s = 0, rel IN relationships(path) | 
            CASE 
                WHEN rel:DELIVERS THEN s + 0.9
                WHEN rel:EXPLOITS THEN s + 0.7
                ELSE s + 0.5
            END
        ) AS weighted_threat_score
    ORDER BY weighted_threat_score DESC
    LIMIT 20
    """
    try:
        return [record.data() for record in graph.run(query, name=name)]
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise



def analyze_locations(graph: Graph) -> List[Dict]:
    """分析攻击目标地理位置"""
    query = """
    MATCH path=(n:`Threat Actor`|Malware)-[r:`Located At`|Targets*1..5]->(m:Location)
    RETURN 
        path AS paths,
        n AS threats,
        m AS locations
    ORDER BY LENGTH(path) DESC
    LIMIT 1000
    """
    try:
        return [record.data() for record in graph.run(query)]
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise


def analyze_attacker(graph: Graph) -> List[Dict]:
    """分析攻击者之间的关联关系"""
    query = """
    MATCH path=(n:`Threat Actor`|Malware)-[r*1..5]->(m:`Threat Actor`|Malware)
    WHERE n <> m
    RETURN 
        path AS paths,
        n, m AS attackers,
        r AS chain_relations
    ORDER BY LENGTH(path) DESC
    LIMIT 1000
    """
    try:
        return [record.data() for record in graph.run(query)]
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise


def save_results_to_json(results: List[Dict], filename: str, folder: str = "test_output") -> None:
    """
    保存分析结果为 JSON 文件

    :param results: 分析结果（通常为 List[Dict]）
    :param filename: 要保存的文件名，如 "attack_chain.json"
    :param folder: 保存目录，默认为 "output"
    """
    try:
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"分析结果已保存到：{full_path}")
    except Exception as e:
        logger.error(f"保存 JSON 文件失败: {str(e)}")
        raise
