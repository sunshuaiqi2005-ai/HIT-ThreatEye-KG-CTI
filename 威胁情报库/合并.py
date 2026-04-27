import os

def merge_files_by_prefix(input_dir, output_dir):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 用于存储文件名前缀到文件对象的映射
    prefix_to_file = {}

    # 遍历输入目录中的所有文件
    for filename in sorted(os.listdir(input_dir)):
        # 提取文件名前缀（忽略数字和后缀）
        prefix = '_'.join(filename.split('_')[:-2]) if '_o' in filename else filename

        # 检查是否已经打开了该前缀对应的文件
        if prefix not in prefix_to_file:
            # 打开一个新的输出文件
            output_filename = f"{prefix.replace(' ', '_').replace('#', '')}.txt"
            output_file = open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8')
            prefix_to_file[prefix] = output_file

        # 读取文件内容
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as infile:
            in_entities = False
            in_relationships = False
            for line in infile:
                stripped_line = line.strip()
                if stripped_line == "Named Entities:":
                    in_entities = True
                    in_relationships = False
                    prefix_to_file[prefix].write(line + '\n')
                elif stripped_line == "Relationships:":
                    in_entities = False
                    in_relationships = True
                    prefix_to_file[prefix].write(line + '\n')
                elif in_entities or in_relationships:
                    prefix_to_file[prefix].write(line + '\n')

    # 关闭所有打开的文件
    for file in prefix_to_file.values():
        file.close()

# 使用示例
input_directory = 'input/'  # 替换为你的输入目录路径
output_directory = 'output1/'  # 替换为你希望保存合并结果的输出目录路径

# 合并文件
merge_files_by_prefix(input_directory, output_directory)

print(f"Files have been merged into {output_directory}")