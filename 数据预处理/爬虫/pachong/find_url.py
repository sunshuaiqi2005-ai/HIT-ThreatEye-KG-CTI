import os
import re
from urllib.parse import urlparse
import os
from tqdm import tqdm

def find_subfolders(directory):
    """
    查找指定目录下的全部子文件夹，并将它们的绝对路径存储到一个列表中。

    :param directory: 要查找的目录路径
    :return: 包含所有子文件夹绝对路径的列表
    """
    subfolders = []  # 用于存储子文件夹的绝对路径

    # 遍历目录
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            # 获取子文件夹的绝对路径
            subfolder_path = os.path.join(root, dir_name)
            subfolders.append(subfolder_path)

    return subfolders

def extract_domains_from_readme(readme_path):
    domains = ""
    with open(readme_path, 'r', encoding='utf-8') as file:
        save_flag=False
        for line in file:
            if save_flag: domains=line.replace("\n","")
            if str(line).find('**References**:') != -1:
                save_flag=True
    return domains

def traverse_directories_and_extract_domains(root_dir):
    all_domains = []
    for subdir, _, files in os.walk(root_dir):
        if 'README.md' in files:
            readme_path = os.path.join(subdir, 'README.md')
            all_domains.append(extract_domains_from_readme(readme_path))
    return all_domains

def save_domains_to_file(domains, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for domain in domains:
            file.write(domain + '\n')

if __name__ == "__main__":
    root_directory = r'C:\Users\sunsh\Desktop\APT_Digital_Weapon-master'  # 修改为你的根目录路径
    output_file = 'domains.txt'
    folders=find_subfolders(root_directory)
    new_domains = []
    for i in tqdm(folders):
        domains = traverse_directories_and_extract_domains(root_directory)
        new_domains+=domains
    print(new_domains)
    save_domains_to_file(domains, output_file)
    print(f"Domains have been saved to {output_file}")
