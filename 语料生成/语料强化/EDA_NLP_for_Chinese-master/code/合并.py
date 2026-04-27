import json
import re

def clean_text(text):
    """清理字符串中的多余空格（仅影响最终 JSON 输出）"""
    return re.sub(r'\s+', ' ', text).strip()

def parse_txt_to_json(txt_file):
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    dataset = []
    questions = []
    answers = []

    for line in lines:
        if line.startswith("0"):  # 识别问题
            question = line[1:]  # 去掉 "0 "
            questions.append(question)
        elif line.startswith("1"):  # 识别回答
            answer = line[1:]  # 去掉 "1 "
            answers.append(answer)

    # 确保问题和回答的数量一致
    min_length = min(len(questions), len(answers))

    for i in range(min_length):
        dataset.append({
            "instruction": clean_text(questions[i]),  # 仅在这里清理空格
            "input": "",
            "output": clean_text(answers[i])  # 仅在这里清理空格
        })

    return json.dumps(dataset, ensure_ascii=False, indent=4)

# 运行示例
txt_filename = "../output.txt"  # 你的txt文件
json_output = parse_txt_to_json(txt_filename)

# 保存为 JSON 文件
with open("../output.json", "w", encoding="utf-8") as f:
    f.write(json_output)

print("转换完成！JSON 数据已保存到 output.json")

