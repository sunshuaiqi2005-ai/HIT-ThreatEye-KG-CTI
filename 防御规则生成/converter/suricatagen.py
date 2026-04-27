from utils import IndexInfo

CUR_SID = 2000001  # 初始 SID

def gen_SRCT_ruleset_for_ip(ip: IndexInfo) -> list[str]:
    global CUR_SID
    ruleset = []
    ruleset.append(f"alert ip {ip.value} any -> any any (msg:\"Malicious IP Source\"; sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert ip any any -> {ip.value} any (msg:\"Malicious IP Destination\"; sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    return ruleset

def gen_SRCT_ruleset_for_domain(domain: IndexInfo) -> list[str]:
    global CUR_SID
    ruleset = []
    ruleset.append(f"alert dns $HOME_NET any -> any any \
(msg:\"DNS Query for Malicious Domain\"; \
dns.query; content:\"{domain.value}\"; nocase; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert http $HOME_NET any -> $EXTERNAL_NET any \
(msg:\"HTTP Request to Malicious Domain in Host Header\"; flow:established,to_server; \
http.host; content:\"{domain.value}\"; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert tls $HOME_NET any -> $EXTERNAL_NET any \
(msg:\"TLS SNI Malicious Domain\"; flow:established,to_server; \
tls.sni; content:\"{domain.value}\"; nocase; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    return ruleset

def gen_SRCT_ruleset_for_hash(hash: IndexInfo) -> list[str]:
    f"alert http any any -> any any (msg:\"Malicious File Detected by Hash\"; flow:to_client,to_server,established; filesha256:\"malware_sha256.list\"; sid:{CUR_SID}; rev:1;)"
    return []

def gen_SRCT_ruleset_for_hex(hex: IndexInfo) -> list[str]:
    global CUR_SID
    ruleset = []
    indicator_string = hex.value
    hex_string = ' '.join(f'{byte:02x}' for byte in indicator_string)
    ruleset.append(f"alert ip any any -> any any (msg:\"Indicator String Detected\"; content:\"|{hex_string}|\"; sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    return ruleset

def gen_SRCT_ruleset_for_email(email: IndexInfo) -> list[str]:
    return []

def gen_rule_for_ip(indexlist: list[IndexInfo], output_filename: str) -> list[str]:
    name = "badip"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("# Suricata IP dataset\n")
        for index in indexlist:
            f.write(index.value + "\n")
    global CUR_SID
    ruleset = []
    ruleset.append(f"alert ip $EXTERNAL_NET any -> $HOME_NET any (msg:\"Malicious IP Source\"; \
ip.src; \
dataset:isset,{name},type ip,load {output_filename}; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert ip $HOME_NET any -> any any (msg:\"Malicious IP Destination\"; \
ip.dst; \
dataset:isset,{name},type ip,load {output_filename}; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    return ruleset

def gen_rule_for_domain(indexlist: list[IndexInfo], output_filename: str) -> list[str]:
    name = "baddomain"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("# Suricata domain dataset\n")
        for index in indexlist:
            f.write(index.value + "\n")
    global CUR_SID
    ruleset = []
    ruleset.append(f"alert dns $HOME_NET any -> any any (msg:\"DNS Query for Malicious Domain\"; \
dns.query; \
dataset:isset,{name},type string,load {output_filename}; nocase; nocase; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert http $HOME_NET any -> $EXTERNAL_NET any (msg:\"HTTP Request to Malicious Domain (Host Header)\"; \
flow:established,to_server; http.host; \
dataset:isset,{name},type string,load {output_filename}; nocase; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    ruleset.append(f"alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:\"TLS SNI Malicious Domain\"; \
flow:established,to_server; tls.sni; \
dataset:isset,{name},type string,load {output_filename}; nocase; \
sid:{CUR_SID}; rev:1;)\n")
    CUR_SID += 1
    return ruleset

def gen_rule_for_hex(indexlist: list[IndexInfo]) -> list[str]:
    pass

def gen_SRCT_ruleset(indexlist: list[IndexInfo]) -> list[str]:
    suricata_rules = []
    for index in indexlist:
        match index.type:
            case "ip":
                suricata_rules += gen_SRCT_ruleset_for_ip(index)
            case "domain":
                suricata_rules += gen_SRCT_ruleset_for_domain(index)
            case "hash":
                suricata_rules += gen_SRCT_ruleset_for_hash(index)
            case "email":
                suricata_rules += gen_SRCT_ruleset_for_email(index)
            case "hex":
                suricata_rules += gen_SRCT_ruleset_for_hex(index)

    return suricata_rules
