import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 定义 Edge 浏览器的 User-Agent
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
}

#禁用代理并忽略 SSL 验证
proxies = {
    "http": "127.0.0.1:7890",
   "https": "127.0.0.1:7890"
}

def fetch_and_save_domains(input_file, output_dir):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()  # 去除多余空白符
        if not url:
            continue

        try:
            # 发送 GET 请求，忽略 SSL 验证
            response = requests.get(url, headers=headers, proxies=proxies, verify=False)
            #response = requests.get(url, headers=headers, verify=False)

            # 检查请求是否成功
            if response.status_code == 200:
                print(f"请求成功: {url}")

                # 保存内容到文件
                domain = url.replace("://", "_").replace("/", "_")
                output_file = os.path.join(output_dir, f"{domain}.html")
                with open(output_file, 'w', encoding='utf-8') as out_file:
                    out_file.write(response.text)
                print(f"内容已保存到: {output_file}")
            else:
                print(f"请求失败，状态码: {response.status_code}, URL: {url}")

        except Exception as e:
            print(f"请求 URL {url} 失败: {e}")


# 使用路径调用函数
input_file_path = "C:/Users/sunsh/Desktop/pachong/domains2.txt" # 输入文件路径
output_directory = "C:/Users/sunsh/Desktop/pachong/output"  # 输出文件夹路径
fetch_and_save_domains(input_file_path, output_directory)
