
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# 设置 WebDriver（Edge 或 Chrome）
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 无头模式
driver = webdriver.Chrome(options=options)

# 输入与输出路径
input_file = "domains2_http.txt"
output_dir = "html_output"
os.makedirs(output_dir, exist_ok=True)

# 控制爬取频率（单位秒）
crawl_delay = 5

# 读取 URL 列表
with open(input_file, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

for url in urls:
    try:
        print(f"🌐 访问: {url}")
        driver.get(url)
        time.sleep(crawl_delay)  # 控制访问频率

        html = driver.page_source
        safe_filename = url.replace("://", "_").replace("/", "_").replace("?", "_")
        filepath = os.path.join(output_dir, f"{safe_filename}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ 已保存: {filepath}")

    except Exception as e:
        print(f"❌ 处理失败: {url}，错误: {e}")

driver.quit()
print("🎉 所有页面处理完成。")