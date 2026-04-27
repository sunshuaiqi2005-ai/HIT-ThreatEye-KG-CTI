import re
import requests
from bs4 import BeautifulSoup

def geturl(url):
    # 获取网页内容
    response = requests.get(url)
    html_content = response.text

    # 正则表达式匹配 URL
    url_pattern = r'https?://[^\s"<>]+'

    # 提取所有匹配的 URL
    urls = re.findall(url_pattern, html_content)

    # 输出所有提取到的 URL
    for url in urls:
        print(url)


def download(url):
    # 发送HTTP请求获取网页内容
    response = requests.get(url)

    # 确保请求成功
    if response.status_code == 200:
        # 使用BeautifulSoup解析网页内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取网页标题
        # title = soup.title.string if soup.title else 'untitled'
        #
        # 查找包含标题的 div 标签
        # title_div = soup.find('div', class_='title-detail')
        #
        # title = title_div.get_text(strip=True)
        # title_tag = soup.find('title')  # 查找<title>标签
        # title = title_tag.get_text()  # 返回<title>标签中的文本内容

        # 构建文件名（替换不适合文件名的字符）
        filename = f"{url}.html".replace("/", "_").replace("\\", "_").replace(":", "_").replace("|", "_")

        # 保存网页内容到本地文件
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"网页 '{url}' 已成功保存\n")
    else:
        print(f"请求失败，状态码：{response.status_code}，网址：{url}")


def main():
    url = 'https://exp-tools.github.io/threat-broadcast/'
    geturl(url)
    # 读取文件
    with open('references.txt', 'r') as file:
        for url in file:
            # 去掉可能的换行符或空格
            url = url.strip()
            if url:
                download(url)


if __name__ == "__main__":
    main()
