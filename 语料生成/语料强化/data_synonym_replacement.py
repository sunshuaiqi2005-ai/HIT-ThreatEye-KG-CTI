import json
import random
import jieba
from hashlib import md5
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


custom_synonyms = {
    # ==================== 中文术语（仅中文同义词）====================
    "战术": ["策略", "手法", "作战方式"],
    "技术": ["方法", "手段", "技术手段"],
    "数据": ["信息", "资料", "数据集"],
    "远程执行": ["远程代码执行", "远程命令执行"],
    "威胁": ["风险", "危害", "潜在威胁"],
    "恶意软件": ["病毒", "木马", "恶意程序", "恶意代码"],
    "钓鱼": ["欺诈", "仿冒", "诱骗攻击"],
    "服务器": ["主机", "计算机", "服务器设备"],
    "网络": ["互联网", "计算机网络", "局域网", "广域网"],
    "加密": ["数据加密", "加密算法", "信息加密"],
    "解密": ["数据解密", "破解", "密码解密"],#"C2": ["指挥控制中心", "C2服务器", "控制基础设施"],
    #"APT": ["高级持续性威胁", "持续性攻击", "长期威胁活动"],
    "后门": ["后门程序", "隐蔽访问通道", "远程访问后门"],
    #"DDoS": ["分布式拒绝服务攻击", "分布式拒绝服务", "洪水攻击"],
    "特权提升": ["权限升级", "提权", "系统权限提升"],
    "僵尸网络": ["Botnet", "僵尸主机", "受控网络", "僵尸设备"],
    "木马": ["后门程序", "远程控制木马", "恶意木马"],
    "键盘记录": ["键盘监听", "按键记录", "键盘操作捕获"],
    "恶意代码": ["恶意脚本", "有害程序", "攻击性代码"],
    "社会工程学": ["心理操控", "诱导欺骗", "社会工程攻击"],
    "钓鱼邮件": ["欺诈邮件", "伪装邮件", "恶意钓鱼邮件"],
    #"XSS": ["跨站脚本攻击", "跨站漏洞", "XSS注入漏洞"],
    "SQL注入": ["SQLi攻击", "数据库注入", "SQL注入漏洞"],
    #"RCE": ["远程代码执行", "远程命令执行", "远程Shell执行"],
    "代码执行": ["远程代码执行", "恶意代码执行", "执行恶意脚本"],
    "侧信道攻击": ["旁道攻击", "侧信道漏洞利用", "侧信道分析攻击"],
    "信息泄露": ["数据泄漏", "敏感数据外泄", "信息暴露"],
    "恶意广告": ["恶意广告投放", "恶意推广", "恶意广告程序"],
    "流量劫持": ["DNS劫持", "HTTP劫持", "网络流量劫持"],
    "远控木马": ["远程木马", "远程控制木马", "远程访问木马"],
    "病毒": ["计算机病毒", "恶意病毒", "自我复制病毒"],
    "社会工程学攻击": ["社工攻击", "社会工程欺骗", "社交操控攻击"],
    "凭证窃取": ["身份盗窃", "凭证盗窃", "密码盗窃"],
    "代码混淆": ["代码加密", "代码隐藏", "反逆向工程技术"],
    "浏览器劫持": ["浏览器控制", "恶意插件劫持", "浏览器篡改"],
    "XSS": ["Cross-Site Scripting", "XSS", "script injection"],
    "DDoS": ["Distributed Denial of Service", "Flood Attack", "Service Disruption"],
    "RCE": ["Remote Code Execution", "Remote Command Execution", "Remote Shell Execution"],
    "Privilege Escalation": ["Privilege Elevation", "System Access Upgrade"],
    "Man-in-the-Middle": ["MITM Attack", "Eavesdropping", "Interception Attack"],
    "DNS Spoofing": ["DNS Cache Poisoning", "DNS Hijacking"],
    "SQL Injection": ["SQLi", "Database Injection", "SQL Injection Attack"],
    "Brute Force": ["Password Cracking", "Brute Force Attack", "Dictionary Attack"],
    "Credential Stuffing": ["Password Stuffing", "Credential Reuse Attack"],
    "Cryptojacking": ["Malicious Mining", "Crypto Mining Malware"],
    "Cross-Site Request Forgery": ["CSRF", "Session Hijacking"],
    "Cross-Site Scripting": ["XSS", "Scripting Injection"],
    "Shellshock": ["Bash Vulnerability", "Shellshock Exploit"],
    # 基础概念
    "攻击": ["入侵", "渗透", "攻陷", "突破", "恶意行为", "入侵活动", "网络攻击"],
    "防御": ["防护", "抵御", "安全防护", "安全加固", "防护措施", "网络安全防护"],
    "漏洞": ["安全缺陷", "脆弱性", "安全弱点", "系统缺陷", "软件缺陷", "安全漏洞"],
    "威胁指标":["攻击指纹", "威胁特征", "威胁痕迹", "入侵证据"],
    "网络武器": ["攻击工具包", "漏洞武器库", "黑客工具集"],
    "暗网情报": ["深网数据", "暗网监控", "非法论坛情报"],
    "威胁情报共享": ["TIP共享", "情报交换", "STIX/TAXII共享"],"命令行注入": ["命令注入", "CLI攻击", "Command Injection", "Shell注入"],

    # 攻击技术
    "网络钓鱼": ["钓鱼攻击", "网络诈骗", "社交工程攻击", "伪装攻击", "欺诈攻击", "电子钓鱼"],
    "水坑攻击": ["定向网站攻击", "供应链钓鱼", "资源投毒", "网站挂马攻击"],
    "鱼叉攻击": ["定向钓鱼", "精准钓鱼", "针对性钓鱼", "高级钓鱼攻击"],
    "勒索软件": ["加密病毒", "勒索病毒", "文件加密木马", "数据绑架软件", "加密勒索"],
    "挖矿木马": ["加密货币木马", "恶意挖矿", "僵尸挖矿", "非法挖矿程序"],

    # 防御技术
    "防火墙": ["安全网关", "网络防护", "网络屏障", "访问控制设备", "边界防护"],
    "入侵检测": ["攻击检测", "入侵防御", "IDS系统", "异常行为检测", "安全监测"],
    "安全加固": ["系统加固", "防护强化", "安全强化", "系统强化", "配置加固"],

    # 高级威胁
    "APT攻击": ["高级持续性威胁", "定向攻击", "长期潜伏攻击", "APT组织攻击", "高级威胁攻击"],
    "供应链攻击": ["上游攻击", "依赖链攻击", "第三方攻击", "软件供应链攻击", "供应链污染"],
    "横向移动": ["内网渗透", "横向扩散", "横向突破", "网络横向传播", "内网横向攻击"],

    # 安全运营
    "威胁情报": ["威胁信息", "安全情报", "攻击指标", "威胁数据", "安全威胁情报"],
    "安全运维": ["安全运营", "SOC运营", "安全运营中心", "网络安全运维", "安全监控"],

    # ==================== 英文术语（仅英文同义词）====================
    # 基础概念
    "Malware": ["Virus", "Trojan", "Backdoor", "Spyware", "Malicious code", "Threatware"],
    "Exploit": ["Vulnerability abuse", "Attack vector", "Security flaw exploit", "Zero-day exploit"],

    # 攻击技术
    "Phishing": ["Scam", "Fraudulent", "Deceptive", "Email spoofing", "Credential theft"],
    "Ransomware": ["Crypto-malware", "File-encryptor", "Data kidnapper", "Extortionware"],
    "Botnet": ["Zombie network", "DDoS network", "Attack bot network", "Malware network"],

    # 防御技术
    "Firewall": ["Network barrier", "Security gateway", "Packet filter", "Access controller"],
    "IDS": ["Intrusion Detection System", "Network monitor", "Threat detector", "Anomaly detector"],
    "SIEM": ["Security analytics", "Log analyzer", "Event manager", "Threat correlator"],

    # 高级威胁
    "APT": ["Advanced Persistent Threat", "Targeted attack", "Stealthy threat", "Cyber espionage"],
    "C2": ["Command and Control", "C&C", "C2 Server", "Bot controller", "Attack infrastructure"],

    # ==================== 混合术语（严格区分语言）====================
    # 中英文对照术语（使用时需根据上下文语言环境选择）
    "零日漏洞": ["0day漏洞", "未公开漏洞", "零时差漏洞"],
    "Zero-Day": ["0day", "Unpatched vulnerability", "Unknown exploit"],

    "社会工程": ["社工攻击", "心理操控", "社会工程学攻击"],
    "Social Engineering": ["Human hacking", "Psychological manipulation", "Deception attack"],

    "蜜罐": ["诱捕系统", "伪装服务器", "虚拟诱捕环境"],
    "Honeypot": ["Decoy system", "Trap server", "Cyber bait"],

    # ==================== 新增术语（2023年最新）====================
    # 中文新增
    "AI安全": ["人工智能安全", "机器学习安全", "算法安全", "智能系统防护"],
    "量子安全": ["抗量子密码", "后量子密码", "量子加密", "量子通信安全"],
    "云原生安全": ["容器安全", "微服务防护", "云微隔离", "K8s安全"],

    # 英文新增
    "AI Security": ["ML Security", "Algorithm protection", "Neural network defense"],
    "Quantum Security": ["Post-quantum crypto", "QKD security", "Quantum-resistant"],
    "Cloud-Native": ["Container security", "Microservice protection", "Kubernetes defense"]
}

def calculate_similarity(text1, text2):
    """计算两个文本之间的余弦相似度"""
    if not text1 or not text2:
        return 0.0

    vectorizer = CountVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    return cosine_similarity([vectors[0]], [vectors[1]])[0][0]


def get_synonyms(word):
    """ 获取自定义同义词 """
    return custom_synonyms.get(word, [])


def synonym_replacement(text, num_replacements=2):
    """
    对文本进行同义词替换，每次替换 `num_replacements` 个不同的单词。
    """
    words = jieba.lcut(text)
    candidates = [i for i, word in enumerate(words) if word in custom_synonyms]

    if not candidates:
        return text  # 没有可替换的词，直接返回原文本

    num_replacements = min(num_replacements, len(candidates))  # 避免超出可替换范围
    selected_indices = random.sample(candidates, num_replacements)  # 随机选择 `num_replacements` 个单词替换

    for idx in selected_indices:
        synonyms_list = get_synonyms(words[idx])
        if synonyms_list:
            words[idx] = random.choice(synonyms_list)

    return ''.join(words)


def generate_item_hash(item):
    """生成数据项的哈希值用于去重"""
    hash_str = f"{item.get('instruction', '')}_{item.get('input', '')}_{item.get('output', '')}"
    return md5(hash_str.encode('utf-8')).hexdigest()


def is_too_similar(original_item, new_item, similarity_threshold=0.9):
    """
    检查增强后的数据项是否与原始数据项过于相似
    """
    # 比较instruction
    original_instruction = original_item.get('instruction', '')
    new_instruction = new_item.get('instruction', '')
    if calculate_similarity(original_instruction, new_instruction) > similarity_threshold:
        return True

    # 比较output
    original_output = original_item.get('output', '')
    new_output = new_item.get('output', '')
    if calculate_similarity(original_output, new_output) > similarity_threshold:
        return True

    return False


def augment_data(data, num_replacements=2, similarity_threshold=0.85):
    """
    对Alpaca格式的数据进行增强：
    - 保留原始文本
    - 生成2个同义词替换版本
    - 自动去重
    - 过滤掉与原始文本过于相似的增强版本
    """
    augmented_data = []
    seen_hashes = set()

    for item in data:
        original_item = item.copy()
        original_hash = generate_item_hash(original_item)

        # 添加原始数据（确保不去重原始数据）
        if original_hash not in seen_hashes:
            augmented_data.append(original_item)
            seen_hashes.add(original_hash)

        # 生成2个增强版本
        generated_count = 0
        attempt_count = 0
        max_attempts = 5  # 最多尝试生成5次，避免无限循环

        while generated_count < 2 and attempt_count < max_attempts:
            attempt_count += 1
            new_item = item.copy()

            # instruction 替换
            if 'instruction' in new_item:
                new_item['instruction'] = synonym_replacement(new_item['instruction'], num_replacements)

            # output 替换
            if 'output' in new_item:
                new_item['output'] = synonym_replacement(new_item['output'], num_replacements)

            # 检查是否与原始数据不同且未被添加过
            new_hash = generate_item_hash(new_item)

            # 检查相似度
            if is_too_similar(item, new_item, similarity_threshold):
                continue  # 跳过过于相似的版本

            if new_hash not in seen_hashes:
                augmented_data.append(new_item)
                seen_hashes.add(new_hash)
                generated_count += 1

    return augmented_data


def save_augmented_data(input_json_path, output_json_path, num_replacements=2):
    """
    读取Alpaca格式的JSON文件，进行数据增强，并保存增强后的数据。
    """
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    augmented_data = augment_data(data, num_replacements)

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, indent=4, ensure_ascii=False)

    print(f"数据增强完成，增强后的数据已保存到: {output_json_path}")
    print(f"原始数据量: {len(data)}")
    print(f"增强后数据量: {len(augmented_data)} （包含原始数据且已去重）")


# 示例调用
input_json_path = './alpaca_znen.json'
output_json_path = './augmented_alpaca_znen.json'

# 运行数据增强，每个字段至少替换2次，且保留原始文本
save_augmented_data(input_json_path, output_json_path, num_replacements=2)


