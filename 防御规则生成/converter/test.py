from scapy.all import IP, TCP, send

# 替换为你的伪造源IP和目标IP
src_ip = "125.7.152.55"  # 伪造源 IP
dst_ip = "192.168.146.129"   # 本机某接口 IP

packet = IP(src=src_ip, dst=dst_ip) / TCP(dport=80, sport=12345, flags="S")

send(packet)


