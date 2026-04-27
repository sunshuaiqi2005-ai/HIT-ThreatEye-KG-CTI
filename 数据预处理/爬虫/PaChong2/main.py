import requests

# 设定请求头，模拟 Chrome 在 Windows 上的访问
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 目标 URL
url = "https://blog.talosintelligence.com/yorotrooper-espionage-campaign-cis-turkey-europe/"

# 发送 GET 请求，并禁用 SSL 证书验证
response = requests.get(url, headers=headers, verify=False)

# 输出响应状态码
print(f"Response Status Code: {response.status_code}")

# 如果返回 200，打印前 500 个字符
if response.status_code == 200:
    print(response.text[:500])
