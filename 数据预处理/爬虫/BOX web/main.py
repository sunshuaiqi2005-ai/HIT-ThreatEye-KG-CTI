import requests
import re



def extract_file_id(url):

    # 访问主页面，获取 file_ID
    response = requests.get(url)
    if response.status_code == 200:
        # 使用正则表达式提取 file_ID
        match = re.search(r'file_id=f_(\d+)', response.text)
        if match:
            file_id = match.group(0)  # 提取的 file_ID
            return file_id
    return None


def get_download_location(file_id):
    # 生成下载链接
    download_url = f"https://app.box.com/index.php?rm=box_download_shared_file&shared_name=0cp8nyd339dnbak96x2klgz1kxm36xd2&file_id={file_id}"
    response = requests.get(download_url)
    if response.status_code == 200:
        # 使用正则表达式提取 location
        match = re.search(r'location="(https://.*?)"', response.text)
        if match:
            location = match.group(1)  # 提取的 location
            return location
    return None


def download_file(location, save_path):
    # 访问最终下载地址并保存文件
    response = requests.get(location)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print("文件下载成功！")
    else:
        print("文件下载失败！")


def main():
    # 主页面 URL
    url = "https://app.box.com/s/0cp8nyd339dnbak96x2klgz1kxm36xd2"

    # 获取 file_ID
    file_id = extract_file_id(url)
    if file_id:
        print(f"提取到 file_ID: {file_id}")

        # 获取下载链接
        download_location = get_download_location(file_id)
        if download_location:
            print(f"下载链接: {download_location}")

            # 下载文件
            download_file(download_location, 'downloaded_file.zip')  # 保存为 downloaded_file.zip
        else:
            print("未能提取到下载链接！")
    else:
        print("未能提取到 file_ID！")


if __name__ == "__main__":
    main()
