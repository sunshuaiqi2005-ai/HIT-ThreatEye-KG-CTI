from bs4 import BeautifulSoup
import re
import os
import pdfplumber
import pymupdf
import base64
import api
import pymupdf4llm
import requests
import html2text

CurrentImgProcessAPI = 'deepseek'
CurrentTextProcessAPI = 'deepseek'

def getHtmlText(path):
    with open(path, 'r+', encoding='utf-8') as html:
        raw = html.read()
    soup = BeautifulSoup(raw, 'html.parser')
    pattern = r"\n\s*\n"  # 匹配连续的空行 删除
    text = re.sub(pattern, "\n", soup.get_text())
    return text

def getPdfTextGrouped(path, lowerBound):
    textlist = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.page_number == 1:
                text = page.extract_text()
            else:
                text += page.extract_text()
            if len(text) >= lowerBound:
                textlist.append(text)
        textlist.append(text)
    return textlist

def getPdfText(path) -> str:
    with pdfplumber.open(path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.crop((0, 0.05 * float(page.height), page.width, 0.95 * float(page.height))).extract_text() # 尝试削除页眉和页脚的无效信息
    return text

def processHtmlFiles(input_folder, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith('.html'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)

            # 提取文本内容
            text_content = getHtmlText(input_file_path)

            # 将文本内容写入输出文件
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(text_content)

            print(f"Processed: {filename}")

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
            textlist = getPdfTextGrouped(input_file_path)

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


def extractHTMLcontent(path: str) -> str:
    md_text = pymupdf4llm.to_markdown(doc=path)

def process_html_to_text(html_content: str, base_url: str):
    """
    处理HTML内容并生成带有占位符的纯文本。
    
    :param html_content: HTML文件的内容 (str)
    :param base_url: HTML文件的基础URL，用于补全相对路径
    :return: 转换后的纯文本 (str)
    """
    # 初始化html2text处理器
    with open("inputDir\input2\http_blog.nsfocus.net_murenshark_.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    h = html2text.HTML2Text()
    h.ignore_links = True  # 保留链接
    h.images_to_alt = True  # 将图像替换为alt属性或链接
    h.body_width = 0  # 不限制行宽
    soup = BeautifulSoup(html_content, 'html.parser')

    # 提取所有图像标签并替换为链接占位符
    # for img_tag in soup.find_all('img'):
    #     img_src = img_tag.get('src', '')
    #     if not img_src.startswith(('http://', 'https://')):
    #         img_src = requests.compat.urljoin(base_url, img_src)  # 补全相对路径
    #     img_tag.replace_with(f"[Image: {img_src}]")  # 替换为图像链接占位符

    # # 提取所有表格标签并替换为占位符
    # for table_tag in soup.find_all('table'):
    #     table_placeholder = "[Table]"
    #     table_tag.replace_with(table_placeholder)

    # 使用html2text将处理后的HTML转换为纯文本
    processed_html = str(soup)
    plain_text = h.handle(processed_html)
    return plain_text

def extractPDFcontent(path: str) -> str:
    doc = pymupdf.Document(path)
    smask_list = []
    content = ''
    for page in doc:
        content += page.get_text()
        images = page.get_images()
        base64_str_list = []
        for image in images:
            xref = image[0]
            if xref in smask_list: # 筛除蒙版图
                continue
            try:
                obj = doc.extract_image(xref)
            except:
                continue
            if not obj:
                continue # 筛除非图像
            if obj["width"] < 50 or obj["height"] < 30: # 筛除小图像
                continue
            smask = obj["smask"]
            if smask > 0:
                smask_list.append(smask)
            img_format = obj["ext"]
            base64_str_list.append(f"data:image/{img_format};base64,{base64.b64encode(obj['image']).decode('utf-8')}")
        content += 'There are pictures on this page with the following description:\n'
        content += api.API2(CurrentImgProcessAPI, base64_str_list, 'img', 'Describe the content of this image')
        content += '\nend of page\n'
    return content

def extractPDFimg(inDir: str, filename: str, outDir: str):
    doc = pymupdf.Document(f"{inDir}\{filename}")
    xref_num = doc.xref_length()
    smask_list = []
    for xref in range(1, xref_num):
        if xref in smask_list: # 筛除蒙版图
            continue
        try:
            obj = doc.extract_image(xref)
        except:
            continue
        if not obj:
            continue # 筛除非图像
        if obj["width"] < 50 or obj["height"] < 30: # 筛除小图像
            continue
        pix = pymupdf.Pixmap(obj["image"])
        smask = obj["smask"]
        if smask > 0:
            smask_list.append(smask)
            mask = pymupdf.Pixmap(doc.extract_image(smask)["image"])
            # pix = pymupdf.Pixmap(pix, mask) # 将蒙版组合到原图像
        img_format = obj["ext"]
        base64_str = f"data:image/{img_format};base64,{base64.b64encode(obj['image']).decode('utf-8')}"
        image_description = api.API2('zhipu', base64_str, 'img', '描述图片内容')
        # pix.save(f"{outDir}\{filename}-{xref}.{img_format}")


def GetPDFContent(path: str, threshold: int) ->list[str]:
    content_list = []
    start = 0
    content = extractPDFcontent(path)
    contentlen = len(content)
    while start < contentlen:
        end = min(start + threshold, contentlen)
        if end < contentlen:
            strippos = content.rfind('\nend of page\n', start, end + 1)
            if strippos != -1 and strippos >= start:
                end = strippos + 1
        content_list.append(content[start:end])
        start = end
    return content_list

# if __name__ == "__main__":
#     print(GetPDFContent("inputDir\PDF2\Iranian-Nation-State-APT-Leak-Analysis-and-Overview.pdf", 8192))


# 示例：读取本地HTML文件并处理
if __name__ == "__main__":
    # 读取HTML文件内容
    with open("inputDir\input2\http_blog.nsfocus.net_murenshark_.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    base_url = ""

    # 转换为纯文本
    result_text = process_html_to_text(html_content, base_url)

    # 输出结果到文件
    with open("outputDir\output.txt", "w", encoding="utf-8") as output_file:
        output_file.write(result_text)

    print("转换完成！输出已保存到 output.txt")