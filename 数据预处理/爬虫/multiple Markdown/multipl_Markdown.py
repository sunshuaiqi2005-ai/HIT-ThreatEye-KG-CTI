import os
import re

# 定义查找的关键词
pattern = r'\[(.*?)\]\((.*?)\)'

# 设置文件夹路径
folder_path = './Threat-Hunting-master/'

# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # 只处理文件，不处理子文件夹
    if os.path.isfile(file_path) and filename.endswith(('.md', '.markdown')):  # 只处理 Markdown 文件
        try:
            url_pattern = re.compile(pattern)

            # 打开文件并读取内容
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    matches = url_pattern.findall(line)
                if matches:
                    for match in matches:
                        with open("./Threat-Hunting-master/sources.txt", "a", encoding="utf-8") as file:
                            file.write(match[1] + "\n")

        except Exception as e:
            print(f"无法读取文件 '{filename}'，错误: {e}")
