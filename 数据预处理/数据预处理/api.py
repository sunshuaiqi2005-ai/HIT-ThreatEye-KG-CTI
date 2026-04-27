import requests
import json
from openai import OpenAI
import os
import base64
from pathlib import Path
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage, ImageChatMessage
from google import genai
import PIL.Image
import base64
from zhipuai import ZhipuAI

# 接口设计:
# 模型备选: "moonshot-v1-8k-vision-preview" "qwen-vl-max-latest" 

# QwQ-plus: 推理模型 最大上下文长度：131072，最大回复长度：8192，最大输入：98304
# qwen2.5-max：最大上下文长度：32768，最大回复长度：8192，最大输入：30720
# qwen-plus：最大上下文长度：131072，最大回复长度：8192，最大输入：129024
# qwen-long：长上下文窗口 最大上下文长度：10000000，最大回复长度：8192，最大输入：10000000
# qwen-omni：多模态 最大上下文长度：32768，最大回复长度：2048，最大输入：30720
# qwen-vl-max：视觉理解 最大上下文长度：131072，最大回复长度：8192，最大输入：129024

default_prompt = """Please identify the following types of entities and then extract the relationships between these extracted entities:
Entities: (Attack Pattern, Campaign, Identity, Indicator, Infrastructure, Location, Malware, Observed Data, Threat Actor, Tool, Vulnerability, misc)
Relationship: (attributed to, impersonates, indicates, authored by, beacons to, exfiltrate to, located at, based on, targets, uses, delivers, exploits, has, originates from, consists of, communicates with, hosts, owns, downloads, drops, controls, compromises, variant of, else)
In addition to identifying the entities and relationships, please provide a confidence score for each entity and relationship in your output. The confidence score should be a number between 0 and 1, where 1 represents the highest confidence in the prediction and 0 represents the lowest confidence. If there are no entities and relationships pertaining to the specified types, please state ‘No related entities and relations’. Make sure to follow the output format shown in the following example.
Input: A hitherto unknown attack group has been observed targeting a materials research organization in Asia. The group, which Symantec calls Clasiopa, is characterized by a distinct toolset, which includes one piece of custom malware (Backdoor.Atharvan). At present, there is no firm evidence on where Clasiopa is based or whom it acts on behalf.
Output: Named Entities: (Clasiopa,Threat Actor,0.95),(custom malware, Tool,0.75),(Backdoor.Atharvan, Malware,0.85)...\nRelationships: (Clasiopa, uses, custom malware,0.88),(custom malware, has, Backdoor.Atharvan,0.91)...
"""

ERNIE_API_KEY = "fDyg397w0FZQoDUTjZ2wCo5v"
ERNIE_SECRET_KEY = "MLqH1pogdiVZKY28Dh4CKlZi066lDB4i"
ERNIE_BASE_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token="

QIANFAN_URL = "https://qianfan.baidubce.com/v2/chat/completions"

QIANFAN_API_KEY = "bce-v3/ALTAK-iLR3CN5XsThR119hW7hLB/80cc9e7c9e833658c3bb29a7d17cf7bb94db94e4"
QIANFAN_DEEPSEEKVL_URL = 'https://qianfan.baidubce.com/v2'

ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
ERNIE_HEADERS = {
    'Content-Type': 'application/json'
}
ACCESS_PARAMS = {
    "grant_type": "client_credentials", 
    "client_id": ERNIE_API_KEY, 
    "client_secret": ERNIE_SECRET_KEY
}

DEEPSEEK_API_KEY = "sk-4245257abbee4c479d94e1ebb212f0c5"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

MOONSHOT_API_KEY = "sk-RzaPe6HguOjkiwM0DaPHULv3n8cAliHD5Xs5y79GyRY5oVWF"
MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"

QWEN_API_KEY = "sk-ed1bb607e3474a018c630a0595798278"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_API_KEY = 'f9a72e41-8a24-47db-a9fb-2e6961aa55a8'

GEMINI_API_KEY = "AIzaSyBN5Ne2utQhC4cNpYboBTTD00iW91OTnmo"

LLAMA_API_KEY = '3bdea8dd-509f-411a-a8b0-ea1833b785bd'
LLAMA_BASE_URL = "https://api.llama-api.com/"

ZHIPU_API_KEY = "c92981450f6d4c258dba39c0dd7b35e8.87eJGN7AL7iUO1yz"

SPARK_APP_ID = '5343b6c0'
SPARK_API_KEY = 'c4b8024649dd03d23494027d36c0ef9d'
SPARK_API_SECRET = 'ZjcwNDQ2ZWRmMGE3MDhlYjU0YWUxMTVm'

# PNG图像：  f"data:image/png;base64,{base64_image}"
# JPEG图像： f"data:image/jpeg;base64,{base64_image}"
# WEBP图像： f"data:image/webp;base64,{base64_image}"

def qianfan_deepseekvl(query: str, prompt: str):
    client = OpenAI(
        base_url=QIANFAN_DEEPSEEKVL_URL,
        api_key=QIANFAN_API_KEY
    )
    response = client.chat.completions.create(
        model="deepseek-vl2",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encode_image(query)
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content

def ernie35(query: str) -> str:
        
    LLM_URL = ERNIE_BASE_URL + get_access_token()
    
    payload = json.dumps({
        "temperature": 0.95,
        "top_p": 0.8,
        "penalty_score": 1,
        "enable_system_memory": False,
        "disable_search": False,
        "enable_citation": False,
        "response_format": "text",
        "messages":[
            {
                "role": "user",
                "content": query
            }
        ]
    })
    
    response = requests.request("POST", LLM_URL, headers=ERNIE_HEADERS, data=payload)
    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            print("响应内容不是有效的 JSON")
    else:
        print(f"请求失败，状态码: {response.status_code}")

    return data.get('result') # default: None
    
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    return str(requests.post(ACCESS_TOKEN_URL, params=ACCESS_PARAMS).json().get("access_token"))

def API(modelname: str, query: str, query_type: str, prompt: str):
    match modelname:
        case 'deepseek':
            match query_type:
                case 'text':
                    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant"},
                            {"role": "user", "content": prompt},
                            {"role": "user", "content": query},
                        ],
                        stream=False
                    )
                    return response.choices[0].message.content
                case 'img':
                    return qianfan_deepseekvl(query, prompt)
        case 'qwen':
            client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
            match query_type:
                case "img":
                    # qwen api 要求base64编码图片 
                    img_type = Path(query).suffix.lstrip('.')
                    base64_image = encode_image(query)
                    response = client.chat.completions.create(
                        model="qwen-vl-max-latest",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant"},
                            {"role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        # PNG图像：  f"data:image/png;base64,{base64_image}"
                                        # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
                                        # WEBP图像： f"data:image/webp;base64,{base64_image}"
                                        "image_url": {"url": f"data:image/{img_type};base64,{base64_image}"}, 
                                    },
                                    {"type": "text", "text": prompt},
                                ]
                            }
                        ],
                    ) 
                case "text":
                    response = client.chat.completions.create(
                        model="qwen-max-2025-01-25",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant"},
                            {"role": "user", "content": query},
                        ]
                    )
            return response.choices[0].message.content
        case 'moonshot':
            client = OpenAI(api_key = MOONSHOT_API_KEY, base_url = MOONSHOT_BASE_URL)
            match query_type:
                case "img":
                    img_type = Path(query).suffix.lstrip('.')
                    base64_image = encode_image(query)
                    response = client.chat.completions.create(
                        model="moonshot-v1-128k-vision-preview",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant"},
                            {"role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/{img_type};base64,{base64_image}"}, 
                                    },
                                    {"type": "text", "text": prompt},
                                ]
                            }
                        ],
                    )
                case "text":
                    response = client.chat.completions.create(
                        model = "moonshot-v1-8k", # 8k 可改为 32k 或 128k
                        messages = [
                            {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
                            {"role": "user", "content": query}
                        ],
                        temperature = 0.3,
                    )
            return response.choices[0].message.content
        case 'ernie':
            return ernie35(query)
        case 'spark':
            match query_type:
                case 'img':
                    image_content = encode_image(query)
                    spark = ChatSparkLLM(
                        spark_app_id=SPARK_APP_ID,
                        spark_api_key=SPARK_API_KEY,
                        spark_api_secret=SPARK_API_SECRET,
                        spark_llm_domain="image",
                        streaming=False,
                        user_agent="test"
                    )
                    messages = [ImageChatMessage(
                        role="user",
                        content=image_content,
                        content_type="image"
                    ),ImageChatMessage(
                        role="user",
                        content=prompt,
                        content_type="text"
                    )]
                    return spark.generate([messages], callbacks=[]).generations[0][0].text
        case 'doubao':
            match query_type:
                case 'img':
                    img_type = Path(query).suffix.lstrip('.')
                    base64_image = encode_image(query)
                    client = OpenAI(
                        base_url=DOUBAO_URL,
                        api_key=DOUBAO_API_KEY,
                    )
                    response = client.chat.completions.create(
                        model="doubao-vision-pro-32k-241028",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/{img_type};base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                    )
                    return response.choices[0].message.content
        case 'gemini':
            match query_type:
                case 'img':
                    img = PIL.Image.open(query)
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[img, prompt],
                    )
                    return response.text
        case 'llama':
            match query_type:
                case 'img':
                    client = OpenAI(
                        api_key='3bdea8dd-509f-411a-a8b0-ea1833b785bd',
                        base_url="https://api.llama-api.com/"
                    )

                    chat_completion = client.chat.completions.create(
                        messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
                                    },
                                    {
                                        "role": "user",
                                        "content": "how can I solve 8x + 7 = -23"
                                    }
                                ],
                        model="llama3-8b",
                        stream=False
                    )
                    return chat_completion
        case 'zhipu':
            match query_type:
                case 'img':
                    client = ZhipuAI(api_key=ZHIPU_API_KEY)
                    response = client.chat.completions.create(
                        model="glm-4v-plus-0111",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": encode_image(query)
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                                ]
                            }
                        ]
                    )
                    return response.choices[0].message.content
        case _:
            print("未知的大模型名称")
            return

def encode_image(image_path):
    """
    将图片以base64编码
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def API2(modelname: str, query: str | list[str], query_type: str, prompt: str) -> str:
    match modelname:
        case 'deepseek':
            match query_type:
                case 'text':
                    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "user", "content": prompt + query},
                        ],
                        max_tokens=8192
                    )
                    return response.choices[0].message.content
                case 'img':
                    client = OpenAI(api_key=QIANFAN_API_KEY, base_url=QIANFAN_DEEPSEEKVL_URL)
                    response = client.chat.completions.create(
                        model="deepseek-vl2",
                        messages=imgToMessage(query, prompt)
                    )
                    return response.choices[0].message.content
        case 'qwen':
            client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
            match query_type:
                case "text":
                    response = client.chat.completions.create(
                        model="qwen-max-latest",
                        messages=[
                            {"role": "user", "content": prompt + query},
                        ]
                    )
                case "img":
                    # 这里的 query 直接需格式前缀
                    # 可以传入多个image_url对象,但是模型会根据给定的上下文长度在数量过多时截断
                    response = client.chat.completions.create(
                        model="qwen-vl-max-latest",
                        messages=imgToMessage(query, prompt)
                    ) 
            return response.choices[0].message.content
        case 'moonshot':
            client = OpenAI(api_key=MOONSHOT_API_KEY, base_url=MOONSHOT_BASE_URL)
            match query_type:
                case "text":
                    response = client.chat.completions.create(
                        model = "moonshot-v1-128k", # 8k, 32k, 128k
                        messages = [
                            {"role": "user", "content": prompt + query}
                        ],
                        temperature=0.3
                    )
                case "img":
                    # 这里的 query 直接需格式前缀
                    response = client.chat.completions.create(
                        model="moonshot-v1-128k-vision-preview",
                        messages=imgToMessage(query, prompt)
                    )
            return response.choices[0].message.content
        case 'ernie':
            return ernie35(query)
        case 'spark':
            match query_type:
                case "text":
                    pass 
                case 'img':
                    # 这里的 query 直接将图片编码成base64格式, 无需格式前缀
                    spark = ChatSparkLLM(
                        spark_app_id=SPARK_APP_ID,
                        spark_api_key=SPARK_API_KEY,
                        spark_api_secret=SPARK_API_SECRET,
                        spark_llm_domain="image",
                        streaming=False,
                        user_agent="test"
                    )
                    messages = [
                        ImageChatMessage(
                            role="user",
                            content=query,
                            content_type="image"
                        ),
                        ImageChatMessage(
                            role="user",
                            content=prompt,
                            content_type="text"
                        )
                    ]
                    return spark.generate([messages], callbacks=[]).generations[0][0].text
        case 'doubao':
            match query_type:
                case "text":
                    client = OpenAI(api_key=DOUBAO_API_KEY, base_url=DOUBAO_URL)
                    response = client.chat.completions.create(
                        model = "doubao",
                        messages = [
                            {"role": "user", "content": prompt + query}
                        ],
                    )
                case 'img':
                    # 这里的 query 无需格式前缀
                    # 可以传入多个image_url对象,但是模型会根据给定的上下文长度在数量过多时截断
                    client = OpenAI(api_key=DOUBAO_API_KEY, base_url=DOUBAO_URL)
                    response = client.chat.completions.create(
                        model="doubao-vision-pro-32k-241028",
                        messages=imgToMessage(query, prompt)
                    )
                    return response.choices[0].message.content
        case 'gemini':
            match query_type:
                case "text":
                    pass
                case 'img':
                    # 这里的 query 是本地路径
                    img = PIL.Image.open(query)
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[img, prompt],
                    )
                    return response.text
        case 'llama':
            match query_type:
                case "text":
                    client = OpenAI(api_key=LLAMA_API_KEY, base_url=LLAMA_BASE_URL)
                    response = client.chat.completions.create(
                        messages = [
                            {"role": "user", "content": prompt + query}
                        ],
                        model="llama3-8b",
                        stream=False
                    )
                    return response.choices[0].message.content
                case 'img':
                    pass
        case 'zhipu':
            client = ZhipuAI(api_key=ZHIPU_API_KEY)
            match query_type:
                case "text":
                    response = client.chat.completions.create(
                        model="glm-4-plus",
                        messages = [
                            {"role": "user", "content": prompt + query}
                        ]
                    )
                    return response.choices[0].message.content
                case 'img':
                    # 若模型为glm-4v, content中image_url类型的条数不能超过1
                    # 若模型为glm-4v-plus, content中image_url类型的条数不能超过5
                    response = client.chat.completions.create(
                        model="glm-4v-plus-0111",
                        messages=imgToMessage(query, prompt)
                    )
                    return response.choices[0].message.content
        case _:
            print("未知的大模型名称")
            return

def imgToMessage(images, prompt):
    content = []
    if isinstance(images, list):
        for img in images:
            content.append({"type": "image_url", "image_url": {"url": img}})
    else:
        content.append({"type": "image_url", "image_url": {"url": images}})
    content.append({"type": "text", "text": prompt})
    return [{
        "role": "user",
        "content": content
    }]

