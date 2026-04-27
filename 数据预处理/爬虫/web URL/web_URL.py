from bs4 import BeautifulSoup

html_content = ""

# 解析HTML
soup = BeautifulSoup(html_content, 'html.parser')

# 提取<tr>标签
rows = soup.find_all('tr')[1:]

# 提取标题和URL
data = []
for row in rows:
    title = row.find_all('td')[3].text.strip()
    url = row.find('a')['href']
    data.append({'title': title, 'url': url})

# 输出结果
for item in data:
    print(item['title'])
for item in data:
    print(item['url'])