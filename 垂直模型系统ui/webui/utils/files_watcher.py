import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 监听目录
UPLOAD_DIR = "../data/uploads/"

# PDF 和 HTML 文件记录的路径
PDF_LOG_FILE = "pdf_files.txt"
HTML_LOG_FILE = "html_files.txt"

# 定义处理流程的 Python 脚本（按顺序执行）
PDF_PROCESS_SCRIPTS = [
    "../scripts/wenxin.py",
    "../scripts/完全体.py"
]

HTML_PROCESS_SCRIPTS = [
    "../scripts/parse_html.py",
    "../scripts/extract_text.py",
    "../scripts/analyze_content.py"
]

# 监听时间间隔（秒）
WATCH_INTERVAL_MIN = 300  # 5 分钟
WATCH_INTERVAL_MAX = 86400  # 1 天
FAST_CHECK_INTERVAL = 60  # 1 分钟（短时间内快速增加文件时触发）

# 触发处理的文件数量阈值
PROCESS_THRESHOLD = 10


class FileHandler(FileSystemEventHandler):
    """监听文件夹内的新文件"""

    def on_created(self, event):
        if event.is_directory:
            return  # 忽略文件夹

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        # 等待文件写入完成
        time.sleep(1)

        if file_name.lower().endswith(".pdf"):
            print(f"检测到新 PDF 文件: {file_name}")
            log_file(file_path, PDF_LOG_FILE)

        elif file_name.lower().endswith(".html"):
            print(f"检测到新 HTML 文件: {file_name}")
            log_file(file_path, HTML_LOG_FILE)

        # 立即检查文件数量，并决定是否处理
        check_and_process_files()


def log_file(file_path, log_file):
    """将文件路径记录到对应的日志文件中"""
    try:
        with open(log_file, "a", encoding="utf-8") as file:
            file.write(f"{file_path}\n")
        print(f"已记录 {file_path} 到 {log_file}")

    except Exception as e:
        print(f"记录文件时出错: {e}")


def process_file(script_list):
    """依次运行多个 Python 处理脚本"""
    for script in script_list:
        try:
            print(f"运行脚本 {script}")
            subprocess.run(["python", script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"执行 {script} 时出错: {e}")


def count_files():
    """统计 PDF 和 HTML 文件总数"""
    pdf_count = sum(1 for _ in open(PDF_LOG_FILE, "r", encoding="utf-8")) if os.path.exists(PDF_LOG_FILE) else 0
    html_count = sum(1 for _ in open(HTML_LOG_FILE, "r", encoding="utf-8")) if os.path.exists(HTML_LOG_FILE) else 0
    return pdf_count + html_count


def check_and_process_files():
    """检查文件数量并决定是否处理"""
    total_files = count_files()

    if total_files >= PROCESS_THRESHOLD:
        print(f"📌 发现 {total_files} 个待处理文件，立即启动处理流程！")

        # 处理 PDF
        if os.path.exists(PDF_LOG_FILE):
            process_file(PDF_PROCESS_SCRIPTS)
            os.remove(PDF_LOG_FILE)  # 处理完后删除 PDF 记录文件

        # 处理 HTML
        if os.path.exists(HTML_LOG_FILE):
            process_file(HTML_PROCESS_SCRIPTS)
            os.remove(HTML_LOG_FILE)  # 处理完后删除 HTML 记录文件

        return WATCH_INTERVAL_MIN  # 处理后保持高频监听

    else:
        print(f"🔍 仅 {total_files} 个文件，暂不处理，等待新文件")
        return min(WATCH_INTERVAL_MAX, WATCH_INTERVAL_MIN * (PROCESS_THRESHOLD - total_files))  # 按文件数量动态调整


if __name__ == "__main__":
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, UPLOAD_DIR, recursive=False)

    print(f"正在监听 {UPLOAD_DIR} 目录...")

    observer.start()

    # **首次检查（立即执行）**
    next_check_interval = check_and_process_files()

    try:
        while True:
            time.sleep(next_check_interval)
            next_check_interval = check_and_process_files()  # 动态调整下次监听时间
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
