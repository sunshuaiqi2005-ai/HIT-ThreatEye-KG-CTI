import json
import jieba
import random
import argparse

random.seed(2019)


# 读取停用词
def load_stopwords(file_path):
    """ 加载停用词表 """
    with open(file_path, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())
# 加载停用词
stop_words = load_stopwords("../stopwords/hit_stopwords.txt")  # 假设停用词表在 "stopwords.txt" 文件中


# 读取自定义同义词库
with open("synonyms_dict.json", "r", encoding="utf-8") as f:
    custom_synonyms = json.load(f)


def get_synonyms(word):
    """从自定义同义词库中获取同义词"""
    return custom_synonyms.get(word, [])  # 没有返回空列表


########################################################################
# 1️⃣ 同义词替换 Synonym Replacement (SR)
########################################################################
def synonym_replacement(words, n):
    """ 随机替换 n 个单词为其同义词 """
    new_words = words.copy()
    random_word_list = list(set([word for word in words if word not in stop_words]))
    random.shuffle(random_word_list)
    num_replaced = 0

    for random_word in random_word_list:
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(synonyms)
            new_words = [synonym if word == random_word else word for word in new_words]
            num_replaced += 1
        if num_replaced >= n:
            break

    return new_words


########################################################################
# 2️⃣ 随机插入 Random Insertion (RI)
########################################################################
def random_insertion(words, n):
    """ 随机插入 n 个同义词 """
    new_words = words.copy()
    for _ in range(n):
        add_word(new_words)
    return new_words


def add_word(new_words):
    synonyms = []
    counter = 0
    while len(synonyms) < 1:
        random_word = new_words[random.randint(0, len(new_words) - 1)]
        synonyms = get_synonyms(random_word)
        counter += 1
        if counter >= 10:
            return
    random_synonym = random.choice(synonyms)
    random_idx = random.randint(0, len(new_words) - 1)
    new_words.insert(random_idx, random_synonym)


########################################################################
# 3️⃣ 随机交换 Random Swap (RS)
########################################################################
def random_swap(words, n):
    """ 随机交换 n 组单词 """
    new_words = words.copy()
    for _ in range(n):
        new_words = swap_word(new_words)
    return new_words


def swap_word(new_words):
    random_idx_1 = random.randint(0, len(new_words) - 1)
    random_idx_2 = random_idx_1
    counter = 0
    while random_idx_2 == random_idx_1:
        random_idx_2 = random.randint(0, len(new_words) - 1)
        counter += 1
        if counter > 3:
            return new_words
    new_words[random_idx_1], new_words[random_idx_2] = new_words[random_idx_2], new_words[random_idx_1]
    return new_words


########################################################################
# 4️⃣ 随机删除 Random Deletion (RD)
########################################################################
def random_deletion(words, p):
    """ 以概率 p 删除单词 """
    if len(words) == 1:
        return words

    new_words = []
    for word in words:
        r = random.uniform(0, 1)
        if r > p:
            new_words.append(word)

    if len(new_words) == 0:
        rand_int = random.randint(0, len(words) - 1)
        return [words[rand_int]]

    return new_words


########################################################################
# 5️⃣ EDA 数据增强
########################################################################
def eda(sentence, alpha_sr=0.3, alpha_ri=0.3, alpha_rs=0.3, p_rd=0.1, num_aug=2):
    """ 进行 EDA 数据增强 """
    seg_list = jieba.cut(sentence)
    seg_list = " ".join(seg_list)
    words = list(seg_list.split())
    num_words = len(words)

    augmented_sentences = []
    num_new_per_technique = int(num_aug / 4) + 1
    n_sr = max(1, int(alpha_sr * num_words))
    n_ri = max(1, int(alpha_ri * num_words))
    n_rs = max(1, int(alpha_rs * num_words))

    # 同义词替换 (SR)
    for _ in range(num_new_per_technique):
        a_words = synonym_replacement(words, n_sr)
        augmented_sentences.append(' '.join(a_words))

    # 随机插入 (RI)
    for _ in range(num_new_per_technique):
        a_words = random_insertion(words, n_ri)
        augmented_sentences.append(' '.join(a_words))

    # 随机交换 (RS)
    for _ in range(num_new_per_technique):
        a_words = random_swap(words, n_rs)
        augmented_sentences.append(' '.join(a_words))

    # 随机删除 (RD)
    for _ in range(num_new_per_technique):
        a_words = random_deletion(words, p_rd)
        augmented_sentences.append(' '.join(a_words))

    random.shuffle(augmented_sentences)

    if num_aug >= 1:
        augmented_sentences = augmented_sentences[:num_aug]
    else:
        keep_prob = num_aug / len(augmented_sentences)
        augmented_sentences = [s for s in augmented_sentences if random.uniform(0, 1) < keep_prob]

    augmented_sentences.append(seg_list)

    return augmented_sentences


########################################################################
# 6️⃣ 读取输入文件并写入输出文件
########################################################################
def process_file(input_file, output_file, num_aug=2):
    with open(input_file, "r", encoding="utf-8") as infile:
        sentences = infile.readlines()

    augmented_data = []
    for sentence in sentences:
        sentence = sentence.strip()

        # Remove the "01" prefix if it exists
        if sentence.startswith("01"):
            original_prefix = "01"
            sentence = sentence[2:].strip()  # Remove the "01" part
        else:
            original_prefix = ""

        # Print the sentence without the prefix for processing
        print(f"Processing sentence: {sentence}")

        augmented_sentences = eda(sentence, num_aug=num_aug)

        # Add the prefix back to the augmented sentences
        augmented_sentences = [original_prefix + augmented_sentence for augmented_sentence in augmented_sentences]

        # Add augmented sentences to the final list
        augmented_data.extend(augmented_sentences)

    # Write the augmented data to the output file
    with open(output_file, "w", encoding="utf-8") as outfile:
        for line in augmented_data:
            outfile.write(line + "\n")

    # Also preserve the original content in the output file
    with open(output_file, "a", encoding="utf-8") as outfile:
        for line in sentences:
            outfile.write(line)  # Write the original lines to the output file


########################################################################
# 7️⃣ 主程序入口
########################################################################
if __name__ == "__main__":
    # 设置默认路径
    DEFAULT_INPUT_PATH = "D:/桌面/EDA_NLP_for_Chinese-master/alpaca.txt"  # 输入文件默认路径
    DEFAULT_OUTPUT_PATH = "D:/桌面/EDA_NLP_for_Chinese-master/train_augmented.txt"  # 输出文件默认路径
    # 创建ArgumentParser对象
    parser = argparse.ArgumentParser(description="EDA for Data Augmentation")
    # 添加输入文件路径参数
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_PATH, help="输入文件路径")
    # 添加输出文件路径参数
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_PATH, help="输出文件路径")
    # 添加每个句子的增强数量参数
    parser.add_argument('--num_aug', type=int, default=2, help="每个句子的增强数量")
    # 解析命令行参数
    args = parser.parse_args()

    # 打印输入和输出路径以供调试
    print(f"Input file path: {args.input}")
    print(f"Output file path: {args.output}")
    print(f"Number of augmentations: {args.num_aug}")

    args = parser.parse_args()

    process_file(args.input, args.output, num_aug=args.num_aug)
    print(f"增强数据已写入 {args.output}")
