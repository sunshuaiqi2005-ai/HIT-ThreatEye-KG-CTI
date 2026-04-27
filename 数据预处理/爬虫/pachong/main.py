import requests

# 定义 Edge 浏览器的 User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
}

# 目标 URL
url = "http://www.google.com"

# 禁用代理并忽略 SSL 验证
proxies = {
    "http": "127.0.0.1:7890",
    "https": "127.0.0.1:7890"
}

for i in range(10):
    # 发送 GET 请求，忽略 SSL 验证
    response = requests.get(url, headers=headers, proxies=proxies, verify=False)

    # 检查请求是否成功
    if response.status_code == 200:
        print("请求成功！")
        print("响应内容长度:", len(response.text))
        # 打印部分响应内容
        print(response.text[:500])  # 打印前 500 个字符

    else:
        print(f"请求失败，状态码: {response.status_code}")