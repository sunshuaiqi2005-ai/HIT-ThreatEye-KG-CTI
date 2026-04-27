import os
import shutil


def move_pdfs(source_dir, destination_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # 遍历源文件夹中的每一个子文件夹及其子文件夹
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # 检查文件是否为 PDF 文件
            if file.lower().endswith('.pdf'):
                # 获取源文件的完整路径
                source_file = os.path.join(root, file)
                # 获取目标文件的完整路径
                destination_file = os.path.join(destination_dir, file)

                # 检查目标文件夹中是否已有同名文件，如果有则重命名
                if os.path.exists(destination_file):
                    base, ext = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(destination_file):
                        destination_file = os.path.join(destination_dir, f"{base}_{counter}{ext}")
                        counter += 1

                # 将 PDF 文件移动到新文件夹
                shutil.move(source_file, destination_file)
                print(f"已移动文件: {source_file} -> {destination_file}")


def main():
    source_folder = r".\APT_REPORT-master"  # 源文件夹路径
    destination_folder = r".\APT"  # 目标文件夹路径

    move_pdfs(source_folder, destination_folder)


if __name__ == "__main__":
    main()
