import os
import re


# 提取Markdown文件中的URL
def extract_urls_from_markdown(file_path):
    urls = []
    # 使用正则表达式提取URL
    url_pattern = re.compile(r'http[s]?://[a-zA-Z0-9./?=_-]+')

    try:
        # 打开并读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找所有URL
            urls = url_pattern.findall(content)
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")

    return urls


# 定义一个函数遍历文件夹及其子文件夹
def find_readme_files_and_extract_urls(root_folder):
    # 用于存储所有找到的URL
    all_urls = []

    # 遍历文件夹中的所有文件和子文件夹
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            # 查找名为"README.md"的文件
            if filename.lower() == 'readme.md':
                file_path = os.path.join(dirpath, filename)
                print(f"正在处理文件: {file_path}")

                # 提取URL并保存
                urls = extract_urls_from_markdown(file_path)
                if urls:
                    all_urls.extend(urls)

    return all_urls


root_folder = './APT_Digital_Weapon-master'  # 替换为目标文件夹路径
urls = find_readme_files_and_extract_urls(root_folder)

# 输出所有提取的URL
if urls:
    print("\n提取到的URL:")
    for url in urls:
        print(url)
else:
    print("没有找到任何URL。")
