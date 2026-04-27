from py2neo import Node,Relationship,Graph,NodeMatcher
import re
import os

def connect():
    graph = Graph('bolt://localhost:7687',auth=('neo4j','chenhao86031327'),name='neo4j')
    return graph



def extract(file):
    with open(file, 'r+', encoding='utf-8') as f:
        text = f.read()

    sort = []
    stack = []  # 栈用于记录括号的起始位置
    results = []  # 存放匹配到的最外层括号内容

    for index, char in enumerate(text):
        if char == '(':
            stack.append(index)  # 记录左括号位置
        elif char == ')':
            if stack:
                start = stack.pop()  # 匹配到一个完整的括号
                if not stack:  # 栈为空时，说明是最外层括号
                    results.append(text[start + 1:index])

    # 对结果进行处理
    for i in results:
        b = []
        a = i.title().split(',')
        for j in a:
            b.append(j.lstrip())
        sort.append(b)

    return sort

def bulid(graph,enti_rela):
    matcher = NodeMatcher(graph)
    for i in enti_rela:
        print(i)
        if len(i) == 2:
            node_a = matcher.match(name=i[0]).first()
            if node_a != None:
                if not node_a.has_label(i[1]):
                    node_a.add_label(i[1])
                    graph.push(node_a)
                continue
            node = Node(i[1],name=i[0])
            graph.create(node)
        else:
            node_b = matcher.match(name=i[0]).first()
            node_c = matcher.match(name=i[2]).first()
            if node_b == None:
                node_b = Node(name=i[0])
            if node_c == None:
                node_c = Node(name=i[2])
            rela = Relationship(node_b,i[1],node_c)
            graph.merge(rela,i[1],'name')


g = connect()
g.delete_all()

# file_dir = '\output'
current_file = os.path.dirname(__file__)
file_dir = os.path.join(current_file,"output1")
file_paths = []

for root,dirs,files in os.walk(file_dir):
    for file in files:
        full_path = os.path.join(root,file)
        file_paths.append(full_path)

for i in file_paths:
    print(i)
    bulid(g,extract(i))