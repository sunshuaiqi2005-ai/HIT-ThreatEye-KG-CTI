import os
import re

def is_already_formatted(content):
    """
    检查 Named Entities 和 Relationships 是否已格式化：
    - 确保每个实体和关系占一行
    """
    named_entities_match = re.search(r"Named Entities:\n(\(.+\))", content, re.DOTALL)
    relationships_match = re.search(r"Relationships:\n(\(.+\))", content, re.DOTALL)

    if named_entities_match and relationships_match:
        named_entities_text = named_entities_match.group(1)
        relationships_text = relationships_match.group(1)

        # 如果每个条目已经换行，则认为已格式化
        return "\n" in named_entities_text and "\n" in relationships_text
    return False

def format_named_entities(entities_text):
    """
    解析并格式化 Named Entities，使每个实体单独一行
    """
    entities = re.findall(r"\(([^)]+),\s*([^)]+),\s*([\d.]+)\)", entities_text)
    formatted_entities = ",\n".join(f"({name.strip()}, {category.strip()}, {score.strip()})" for name, category, score in entities)
    return "Named Entities:\n" + formatted_entities + "\n"

def format_relationships(relationships_text):
    """
    解析并格式化 Relationships，使每个关系单独一行
    """
    relationships = re.findall(r"\(([^)]+),\s*([^)]+),\s*([^)]+),\s*([\d.]+)\)", relationships_text)
    formatted_relationships = ",\n".join(f"({entity1.strip()}, {relation.strip()}, {entity2.strip()}, {score.strip()})" for entity1, relation, entity2, score in relationships)
    return "Relationships:\n" + formatted_relationships + "\n"

def process_txt_files(folder_path):
    """
    处理文件夹中的 txt 文件：
    1. 删除无关文件：
       - "No related entities and relations" 开头的文件
       - "Named Entities: (No related entities and relations)" 开头的文件
    2. 重新格式化 Named Entities 和 Relationships
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if filename.endswith(".txt") and os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()

            
            if content.startswith("No related entities and relations") or \
               content.startswith("Named Entities: (No related entities and relations)"):
                os.remove(file_path)
                print(f"Deleted: {filename}")
                continue

            named_entities_match = re.search(r"Named Entities:\s*(.*?)\s*Relationships:", content, re.DOTALL)
            relationships_match = re.search(r"Relationships:\s*(.*?)\s*No related entities", content, re.DOTALL)

            if named_entities_match and relationships_match:
                formatted_entities = format_named_entities(named_entities_match.group(1))
                formatted_relationships = format_relationships(relationships_match.group(1))

                # **组合新内容**
                new_content = f"{formatted_entities}\n{formatted_relationships}"

                # **写回文件**
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)

                print(f"Formatted: {filename}")


folder_path = "output"
process_txt_files(folder_path)
