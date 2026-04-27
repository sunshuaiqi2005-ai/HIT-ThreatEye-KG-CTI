import json

# 读取 JSON 文件
with open("alpaca_znen.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 处理数据并转换格式
output_lines = []
for item in data:
    output_lines.append(f"0\t{item['instruction']}")  # instruction 标记为 0
    output_lines.append(f"1\t{item['output']}")      # output 标记为 1

# 写入到文本文件
with open("alpaca.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("转换完成，结果已保存到 output.txt")
