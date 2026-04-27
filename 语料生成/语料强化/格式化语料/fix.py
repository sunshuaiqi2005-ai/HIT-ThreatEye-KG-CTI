def clean_text_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # 去除所有空格、制表符
            cleaned_line = line.replace(' ', '').replace('\t', '')
            outfile.write(cleaned_line)

# 用法示例
clean_text_file('train_augmented.txt', 'output.txt')
