from bs4 import BeautifulSoup
import re
import os
import pdfplumber

def getHtmlText(path):
    with open(path, 'r+', encoding='utf-8') as html:
        raw = html.read()
    soup = BeautifulSoup(raw, 'html.parser')
    pattern = r"\n\s*\n"  # 匹配连续的空行
    text = re.sub(pattern, "\n", soup.get_text())
    return text

def getPdfText(path, bound):
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

def processPDFDir(input_folder: str, output_folder: str):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith('.pdf'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)

            # 提取文本内容
            textlist = getPdfText(input_file_path)

            # 将文本内容写入输出文件
            seq = 0
            for text in textlist:
                with open(output_file_path + str(seq), 'w', encoding='utf-8') as file:
                    file.write(text)
                seq += 1

            print(f"Processed: {filename}")

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


