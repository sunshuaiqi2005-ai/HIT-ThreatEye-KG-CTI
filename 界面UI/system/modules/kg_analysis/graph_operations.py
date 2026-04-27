from py2neo import Node, Relationship, Graph, NodeMatcher
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GraphOperations:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.matcher = NodeMatcher(graph)
        self.logger = logging.getLogger(__name__)

    def create_node(self, name: str, labels: List[str] = None, properties: Optional[Dict] = None) -> Dict:
        """创建节点
        
        Args:
            name: 节点名称
            labels: 节点标签列表
            properties: 节点属性字典
            
        Returns:
            Dict: 创建节点后的信息
        """
        try:
            # 检查节点是否已存在
            existing_node = self.matcher.match(name=name).first()
            if existing_node:
                # 如果节点存在，添加新标签
                if labels:
                    for label in labels:
                        if not existing_node.has_label(label):
                            existing_node.add_label(label)
                # 更新属性
                if properties:
                    for key, value in properties.items():
                        existing_node[key] = value
                self.graph.push(existing_node)
                return {
                    "message": "节点已存在，已更新",
                    "node": {
                        "name": name,
                        "labels": list(existing_node.labels),
                        "properties": dict(existing_node)
                    }
                }
            
            # 创建新节点
            node = Node(*labels, name=name, **properties) if labels else Node(name=name, **properties)
            self.graph.create(node)
            return {
                "message": "节点创建成功",
                "node": {
                    "name": name,
                    "labels": list(node.labels),
                    "properties": dict(node)
                }
            }
        except Exception as e:
            self.logger.error(f"创建节点失败: {str(e)}")
            raise

    def update_node(self, name: str, properties: Dict) -> Dict:
        """更新节点属性
        
        Args:
            name: 节点名称
            properties: 要更新的属性字典
            
        Returns:
            Dict: 更新节点后的信息
        """
        try:
            node = self.matcher.match(name=name).first()
            if not node:
                return {"error": f"节点 {name} 不存在"}
            
            for key, value in properties.items():
                node[key] = value
            self.graph.push(node)
            
            return {
                "message": "节点更新成功",
                "node": {
                    "name": name,
                    "labels": list(node.labels),
                    "properties": dict(node)
                }
            }
        except Exception as e:
            self.logger.error(f"更新节点失败: {str(e)}")
            raise

    def delete_node(self, name: str) -> Dict:
        """删除节点
        
        Args:
            name: 要删除的节点名称
            
        Returns:
            Dict: 删除节点后的信息
        """
        try:
            node = self.matcher.match(name=name).first()
            if not node:
                return {"error": f"节点 {name} 不存在"}
            
            self.graph.delete(node)
            return {"message": f"节点 {name} 删除成功"}
        except Exception as e:
            self.logger.error(f"删除节点失败: {str(e)}")
            raise

    def create_relationship(self, 
                          from_node_name: str, 
                          to_node_name: str, 
                          rel_type: str,
                          properties: Optional[Dict] = None) -> Dict:
        """创建关系
        
        Args:
            from_node_name: 起始节点名称
            to_node_name: 目标节点名称
            rel_type: 关系类型
            properties: 关系属性字典
            
        Returns:
            Dict: 创建关系后的信息
        """
        try:
            # 获取或创建起始节点
            from_node = self.matcher.match(name=from_node_name).first()
            if not from_node:
                from_node = Node(name=from_node_name)
                self.graph.create(from_node)
            
            # 获取或创建目标节点
            to_node = self.matcher.match(name=to_node_name).first()
            if not to_node:
                to_node = Node(name=to_node_name)
                self.graph.create(to_node)
            
            # 创建关系
            relationship = Relationship(from_node, rel_type, to_node, **(properties or {}))
            self.graph.create(relationship)
            
            return {
                "message": "关系创建成功",
                "relationship": {
                    "from": from_node_name,
                    "to": to_node_name,
                    "type": rel_type,
                    "properties": dict(relationship)
                }
            }
        except Exception as e:
            self.logger.error(f"创建关系失败: {str(e)}")
            raise

    def update_relationship(self,
                          from_node_name: str,
                          to_node_name: str,
                          rel_type: str,
                          properties: Dict) -> Dict:
        """更新关系属性
        
        Args:
            from_node_name: 起始节点名称
            to_node_name: 目标节点名称
            rel_type: 关系类型
            properties: 要更新的属性字典
            
        Returns:
            Dict: 更新关系后的信息
        """
        try:
            # 查找关系
            query = """
            MATCH (a)-[r]->(b)
            WHERE a.name = $from_node AND b.name = $to_node AND type(r) = $type
            RETURN r
            """
            result = self.graph.run(query, from_node=from_node_name, to_node=to_node_name, type=rel_type).data()
            
            if not result:
                return {"error": "关系不存在"}
            
            relationship = result[0]['r']
            for key, value in properties.items():
                relationship[key] = value
            self.graph.push(relationship)
            
            return {
                "message": "关系更新成功",
                "relationship": {
                    "from": from_node_name,
                    "to": to_node_name,
                    "type": rel_type,
                    "properties": dict(relationship)
                }
            }
        except Exception as e:
            self.logger.error(f"更新关系失败: {str(e)}")
            raise

    def delete_relationship(self, 
                          from_node_name: str, 
                          to_node_name: str, 
                          rel_type: str) -> Dict:
        """删除关系
        
        Args:
            from_node_name: 起始节点名称
            to_node_name: 目标节点名称
            rel_type: 关系类型
            
        Returns:
            Dict: 删除关系后的信息
        """
        try:
            # 查找关系
            query = """
            MATCH (a)-[r]->(b)
            WHERE a.name = $from_node AND b.name = $to_node AND type(r) = $type
            DELETE r
            """
            self.graph.run(query, from_node=from_node_name, to_node=to_node_name, type=rel_type)
            
            return {"message": "关系删除成功"}
        except Exception as e:
            self.logger.error(f"删除关系失败: {str(e)}")
            raise 