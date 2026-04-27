from py2neo import Node,Relationship,Graph,NodeMatcher,RelationshipMatcher
import re
import os
import json
from natsort import natsorted

def connect():
    graph = Graph('bolt://localhost:7687',auth=('neo4j','xxxxxxxx'),name='stix')
    return graph

def extract(file):
    with open(file, 'r+', encoding='utf-8') as f:
        text = f.read()

    sort = []
    stack = []  # 栈用于记录括号的起始位置
    results = []  # 存放匹配到的最外层括号内容

    for index, char in enumerate(text):
        if char == '(':
            stack.append(index)  # 记录左括号位�?
        elif char == ')':
            if stack:
                start = stack.pop()  # 匹配到一个完整的括号
                if not stack:  # 栈为空时，说明是最外层括号
                    results.append(text[start + 1:index])

    # 对结果进行处�?
    for i in results:
        b = []
        a = i.title().split(',')
        for j in a:
            b.append(j.lstrip())
        sort.append(b)

    return sort

def _node_name(string):
    node_name = ''
    for j in string.split(' '):
        j = j.replace('\'',' ')
        j = j.replace('\\','\\\\\\\\')
        node_name += j + '.*|'
    return node_name

def bulid(graph,enti_rela):
    global bui_nodes,bui_relationship
    matcher = NodeMatcher(graph)
    for i in enti_rela:
        if len(i) == 2:
            node_a = matcher.match(name=i[0]).first()
            if node_a != None:
                if not node_a.has_label(i[1]):
                    node_a.add_label(i[1])
                    graph.push(node_a)
                continue
            node = Node(i[1],name=i[0])
            graph.create(node)
            bui_nodes += 1
        else:
            node_b = matcher.match(name=i[0]).first()
            node_c = matcher.match(name=i[2]).first()
            if node_b == None:
                node_b = Node(name=i[0])
            if node_c == None:
                node_c = Node(name=i[2])
            rela = Relationship(node_b,i[1],node_c)
            graph.merge(rela,i[1],'name')
            bui_relationship += 1

def evaluate(graph,enti_rela):    
    global eva_nodes,eva_relationships,nodes,relations,label0,label1,crt_nodes,crt_relations
    matcher = NodeMatcher(graph)
    for i in enti_rela:
        if len(i) == 3:
            eva_nodes += 1
            if float(i[2]) >= 0.85:
                nodes += 1
                node_name = _node_name(i[0])
                node_a = matcher.match().where("_.name =~ '(?i).*" + node_name + "'").first()
                if node_a != None:
                    crt_nodes += 1
                    if node_a.has_label(i[1]):
                        label0 += 1
                    continue
        elif len(i) == 4:
            eva_relationships += 1
            if float(i[3]) >= 0.85:
                relations += 1 
                node_b_name = _node_name(i[0])
                node_b = matcher.match().where("_.name =~ '(?i).*" + node_b_name + "'").first()
                node_c_name = _node_name(i[2])
                node_c = matcher.match().where("_.name =~ '(?i).*" + node_c_name + "'").first()
                if node_b == None or node_c == None:
                    continue
                rela_matcher = RelationshipMatcher(graph)
                relas = rela_matcher.match((node_b,node_c)).first()
                if relas != None:
                    crt_relations += 1
                    if relas.__class__.__name__ == i[1]:
                        label1 += 1

g = connect()

# file_dir = '\output'
current_file = os.path.dirname(__file__)
# eva_file_dir = os.path.join(current_file,"test")
eva_file_dir = os.path.join(current_file,"chatgpt_output")
# bui_file_dir = os.path.join(current_file,"main_output")
bui_file_dir = os.path.join(current_file,"main_output")
eva_file_paths = []
bui_file_paths = []

for root,dirs,files in os.walk(eva_file_dir):
    for file in natsorted(files):
        full_path = os.path.join(root,file)
        eva_file_paths.append(full_path)


for root,dirs,files in os.walk(bui_file_dir):
    for file in natsorted(files):
        full_path = os.path.join(root,file)
        bui_file_paths.append(full_path)

datas = {}

with open('data.json','w') as file:
    file.write('')

for i,j in zip(bui_file_paths,eva_file_paths):
    bui_nodes=eva_nodes=nodes=bui_relationship=eva_relationships=relations=label0=label1=crt_nodes=crt_relations = 0 
    g.delete_all()
    print(i,j)
    bulid(g,extract(i))
    evaluate(g,extract(j))

    data = {
        "Number of Entities": bui_nodes,
        "Number of Relationships": bui_relationship,
        "LLM Extracted Entities": eva_nodes,
        "LLM Extracted Relationships": eva_relationships,
        "Credible Entities": nodes,
        "Credible Relationships": relations,
        "Correct Entities": crt_nodes,
        "Correct Relationships": crt_relations,
        "Correct Entities Label": label0,
        "Correct Relationships Label": label1
    }
    datas[i.split('\\')[-1]] = data

with open("data.json","a+") as json_file:
    json.dump(datas,json_file,indent=4)
