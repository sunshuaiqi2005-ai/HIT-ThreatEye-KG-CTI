import re
from tld import is_tld
import socket

from utils import IndexInfo

INDEX_ID_MAP = {}  # 特征 ID 到特征字符串的映射
RULES_MAP = {}  # 特征 ID 到规则的一对多关系
SID_TO_INDEX_ID = {}  # SID 到特征 ID 的映射
CUR_INDEX_ID = 1  # 初始特征 ID
DECREASE_TIME = 1000 # 降级时间间隔

def parse_doc_for_index_set(file_path: str) -> list[IndexInfo]:
    indexlist = []
    with open(file_path, 'r') as file:
        for line in file:
            index = parse_line_for_index(line)
            indexlist += index
    return indexlist

def parse_line_for_index(line: str) -> list[IndexInfo]:
    """
    解析单行的特征
    """
    global CUR_INDEX_ID
    # 去掉双引号和首尾空白字符
    line = line.strip().strip('"')
    
    if not line:
        return []
    
    # IPv4 地址匹配规则
    ipv4_pattern = r'(\d{1,3})(?:\[\.\]|\.)(\d{1,3})(?:\[\.\]|\.)(\d{1,3})(?:\[\.\]|\.)(\d{1,3})'
    ipv4_match = re.fullmatch(ipv4_pattern, line)
    
    if ipv4_match:
        # 提取 IPv4 的四个部分并转换为标准格式
        octets = [int(octet) for octet in ipv4_match.groups()]
        if all(0 <= octet <= 255 for octet in octets):
            oid = CUR_INDEX_ID
            CUR_INDEX_ID += 1
            return [IndexInfo(id=oid, type="ip", subtype="ipv4", value=f"{octets[0]}.{octets[1]}.{octets[2]}.{octets[3]}")]
        else:
            print("Invalid IPv4 address: Octets out of range. " + ipv4_match)
            return []
    
    # CIDR 格式的 IPv4 地址匹配规则
    cidr_pattern = ipv4_pattern + r'/(\d{1,2})'
    cidr_match = re.fullmatch(cidr_pattern, line)
    
    if cidr_match:
        # 提取 IPv4 的四个部分和子网掩码
        octets = [int(octet) for octet in cidr_match.groups()[:4]]
        prefix_length = int(cidr_match.group(5))     
        if all(0 <= octet <= 255 for octet in octets) and 0 <= prefix_length <= 32:
            oid = CUR_INDEX_ID
            CUR_INDEX_ID += 1
            return [IndexInfo(id=oid, type="ip", subtype="ipv4-cidr", value=f"{octets[0]}.{octets[1]}.{octets[2]}.{octets[3]}/{prefix_length}")]
        else:
            print("Invalid CIDR format: Octets or prefix length out of range. " + cidr_match)
            return []
    
    # SHA512 哈希值匹配规则
    sha512_pattern = r'(0[xX])?[a-fA-F0-9]{128}'
    if re.fullmatch(sha512_pattern, line):
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        line = line.lower()
        return [IndexInfo(id=oid, type="hash", subtype="sha512", value=line[2:] if line.startswith('0x') else line)]

    # SHA256 哈希值匹配规则
    sha256_pattern = r'(0[xX])?(?P<hash>[a-fA-F0-9]{64})'
    if re.fullmatch(sha256_pattern, line):
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        line = line.lower()
        return [IndexInfo(id=oid, type="hash", subtype="sha256", value=line[2:] if line.startswith('0x') else line)]
    
    # SHA1 哈希值匹配规则
    sha1_pattern = r'(0[xX])?(?P<hash>[a-fA-F0-9]{40})'
    if re.fullmatch(sha1_pattern, line):
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        line = line.lower()
        return [IndexInfo(id=oid, type="hash", subtype="sha1", value=line[2:] if line.startswith('0x') else line)]

    # MD5 哈希值匹配规则
    md5_pattern = r'(0[xX])?(?P<hash>[a-fA-F0-9]{32})'
    if re.fullmatch(md5_pattern, line):
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        line = line.lower()
        return [IndexInfo(id=oid, type="hash", subtype="md5", value=line[2:] if line.startswith('0x') else line)]

    # 域名匹配规则（支持多层后缀）
    domain_pattern = r'([a-zA-Z0-9-]+(\[\.\]|\.))+(?P<tld>[a-zA-Z0-9-]+)'
    domain_match = re.fullmatch(domain_pattern, line)
    
    if domain_match:
        # 移除点号两边的 [] 并转换为标准域名
        top_domain = domain_match.group("tld")
        top_domain = top_domain.lower()
        if is_tld(top_domain):
            parts = re.split(r'\[\.\]|\.', line)
            standard_domain = ".".join(parts).lower()  # 域名部分转换为小写
            try:
                ip_str = socket.gethostbyname(standard_domain)
            except Exception as e:
                print(f"Failed to resolve IP: {e}")
                oid = CUR_INDEX_ID
                CUR_INDEX_ID += 1
                return [IndexInfo(id=oid, type="domain", subtype="domain", value=standard_domain)]
            oid = CUR_INDEX_ID
            CUR_INDEX_ID += 2
            return [IndexInfo(id=oid, type="domain", subtype="domain", value=standard_domain), IndexInfo(id=oid+1, type="ip", subtype="ipformdomain", value=ip_str)]
        else:
            print("Invalid top level domain: " + top_domain)
            return []
    
    # 电子邮件地址匹配规则（支持忽略点号和 @ 符号两侧的 []）
    email_pattern = r'([a-zA-Z0-9_%+-]+)(?:\[@\]|@)(' + domain_pattern + ')'
    email_match = re.fullmatch(email_pattern, line)
    
    if email_match:
        # 提取用户名和域名部分
        username = email_match.group(1)
        domain = email_match.group(2)
        
        # 移除点号两侧的 []
        domain_parts = re.split(r'\[\.\]|\.', domain)
        standard_domain = ".".join(domain_parts).lower()  # 域名部分转换为小写
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        return [IndexInfo(id=oid, type="email", subtype="email", value=f"{username}@{standard_domain}")]
    
    # 十六进制字符串匹配规则
    hex_pattern = r'([0-9a-fA-F]{2}\s?)+'
    if re.fullmatch(hex_pattern, line):
        # 去掉空格并将十六进制字符串转换为字节串
        hex_str = line.replace(" ", "")
        oid = CUR_INDEX_ID
        CUR_INDEX_ID += 1
        return [IndexInfo(id=oid, type="hex", subtype="hex", value=bytes.fromhex(hex_str))]
    
    print(f"Unrecognized indicator format: {line}")
    return []

# import whois
# import requests

# def query_domain_info(domain):
#     try:
#         ip = socket.gethostbyname(domain)
#     except Exception as e:
#         print(f"Failed to resolve IP: {e}")
#         ip = None

#     try:
#         w = whois.whois(domain)
#         whois_info = {
#             'domain_name': w.domain_name,
#             'registrar': w.registrar,
#             'name_servers': w.name_servers
#         }
#     except Exception as e:
#         print(f"Failed to get WHOIS info: {e}")
#         whois_info = None

#     if ip:
#         try:
#             response = requests.get(f"http://ip-api.com/json/{ip}")
#             data = response.json()
#             geo_info = {
#                 'country': data.get('country'),
#                 'regionName': data.get('regionName'),
#                 'city': data.get('city'),
#                 'isp': data.get('isp'),
#                 'org': data.get('org'),
#                 'as': data.get('as'),
#                 'query': data.get('query')
#             }
#         except Exception as e:
#             print(f"Failed to get geolocation info: {e}")
#             geo_info = None
#     else:
#         geo_info = None
#     return ip, whois_info, geo_info

# if __name__ == "__main__":
#     domain = "example.com"
#     ip, whois_info, geo_info = query_domain_info(domain)
#     print(ip)
#     print(whois_info)
#     print(geo_info)

