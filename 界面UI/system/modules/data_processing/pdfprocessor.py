from bs4 import BeautifulSoup
import re
import os
import pdfplumber

def genTargetFilename(filename, seq):
    """
    根据原始文件名生成目标文件名，将原始文件名转换为新格式：
    前缀 + "_{序列号}_o.txt"
    参数:
        filename (str): 原始文件名（如 "hello.pdf"）
        sequence_num (int): 序列号（如 2）
    返回:
        str: 新文件名（如 "hello_2_o.txt"）
    """
    root, _ = os.path.splitext(filename)
    targetName = f"{root}_{seq}_o.txt"
    return targetName

def getPdfText(path, bound=10000):
    """
    从PDF文件中提取文本内容，并按指定字数分割。
    参数:
        path (str): PDF 文件路径
        bound (int): 文本切分的最大字数（默认 10000）
    返回:
        list[str]: 处理后的文本列表
    """
    textlist = []
    with pdfplumber.open(path) as pdf:
        isFirst = True
        for page in pdf.pages:
            if isFirst:
                text = page.extract_text()
                isFirst = False
            else:
                text += page.extract_text()
            if len(text) >= bound:
                textlist.append(text)
                isFirst = True
        textlist.append(text)
    return textlist

def getHtmlText(path, bound=10000):
    """
    从HTML文件中提取文本内容，并去除多余空行，同时提取超链接。
    参数:
        path (str): HTML 文件路径
        bound (int): 文本切分的最大字数（默认 10000）
    返回:
        tuple: (textlist, linklist)
            - textlist (list[str]): 处理后的正文文本（按字数拆分）
            - linklist (list[str]): 提取的超链接列表
    """
    textlist = []
    linklist = []

    # 读取 HTML 文件
    with open(path, 'r', encoding='utf-8') as html:
        raw = html.read()

    # 解析 HTML
    soup = BeautifulSoup(raw, 'html.parser')

    # 提取并清理正文文本
    text = soup.get_text(separator="\n").strip()  # 使用换行符分隔不同段落
    text = re.sub(r"\n\s*\n", "\n", text)  # 移除多余空行

    # 按字数拆分正文文本
    start = 0
    while start < len(text):
        end = min(start + bound, len(text))
        textlist.append(text[start:end])
        start = end

    # 提取所有超链接
    linklist = [a["href"] for a in soup.find_all("a", href=True)]

    return textlist, linklist 