import json

def validate_json_format(file_path):
    try:
        # 读取 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 解析 JSON

        # 确保 JSON 结构是一个列表
        if not isinstance(data, list):
            print("❌ 错误：JSON 顶层结构必须是列表（数组）！")
            return False

        # 遍历每个条目，检查格式
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"❌ 错误：索引 {i} 的数据不是字典！")
                return False

            # 必须包含的字段
            required_fields = ["instruction", "input", "output"]
            for field in required_fields:
                if field not in item:
                    print(f"❌ 错误：索引 {i} 缺少字段 '{field}'！")
                    return False
                if not isinstance(item[field], str):
                    print(f"❌ 错误：索引 {i} 的 '{field}' 应该是字符串！")
                    return False
                if field in ["instruction", "output"] and not item[field].strip():
                    print(f"❌ 错误：索引 {i} 的 '{field}' 不能为空！")
                    return False

        print("✅ JSON 格式正确！")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误：{e}")
        return False
    except Exception as e:
        print(f"❌ 发生未知错误：{e}")
        return False

# 指定 JSON 文件路径
file_path = "alpaca_dataset.json"  # 你的 JSON 文件路径

# 运行检测
validate_json_format(file_path)
