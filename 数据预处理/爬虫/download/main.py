import requests

def download(url):
    try:
        # 发送 GET 请求
        response = requests.get(url, allow_redirects=True)

        # 检查是否成功
        if response.status_code == 200:
            # 提取文件名
            filename = url.split('/')[-1] + ".pdf"
            # 保存文件
            with open(filename, "wb") as file:
                file.write(response.content)
            print(f"文件下载成功：{filename}")
        else:
            print(f"下载失败，错误代码: {response.status_code}")

    except Exception as e:
        print(f"发生错误：{e}")

# 文件链接列表
urls = []

# 下载每个文件
for url in urls:
    download(url)