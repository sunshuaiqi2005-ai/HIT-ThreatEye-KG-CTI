import json
import random

def split_data(input_json_path, train_output_json_path, val_output_json_path, val_ratio=0.1, seed=42):
    """
    将Alpaca格式的JSON文件打乱并分成训练集和验证集。

    参数:
    - input_json_path: 输入的JSON文件路径。
    - train_output_json_path: 训练集输出的JSON文件路径。
    - val_output_json_path: 验证集输出的JSON文件路径。
    - val_ratio: 验证集的比例，默认为0.2（20%）。
    - seed: 随机种子，确保结果可重复，默认为42。
    """
    # 设置随机种子
    random.seed(seed)

    # 读取输入JSON文件
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 打乱数据
    random.shuffle(data)

    # 计算验证集的大小
    val_size = int(len(data) * val_ratio)
    train_size = len(data) - val_size

    # 分割数据
    train_data = data[:train_size]
    val_data = data[train_size:]

    # 保存训练集
    with open(train_output_json_path, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=4, ensure_ascii=False)

    # 保存验证集
    with open(val_output_json_path, 'w', encoding='utf-8') as f:
        json.dump(val_data, f, indent=4, ensure_ascii=False)

    print(f"数据已成功分割并保存：")
    print(f"- 训练集大小: {len(train_data)}")
    print(f"- 验证集大小: {len(val_data)}")

# 示例调用
input_json_path = 'strict_augmented_4.json'  # 输入的Alpaca格式JSON文件路径
train_output_json_path = './scripts-2/au_train_data.json'  # 训练集输出路径
val_output_json_path = './scripts-2/au_val_data.json'  # 验证集输出路径

split_data(input_json_path, train_output_json_path, val_output_json_path, val_ratio=0.2)