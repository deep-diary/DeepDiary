import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
import requests
import json
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, tool, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(dotenv_path="../../../.env", override=True) 

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DeepSeek_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"OPENWEATHER_API_KEY: {OPENWEATHER_API_KEY}")
print(f"DeepSeek_API_KEY: {DeepSeek_API_KEY}")  # 可以通过打印查看


#----------------------------------------------------------------------------------
@tool
def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    :return：OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    # Step 1.构建请求
    url = "https://api.openweathermap.org/data/2.5/weather"

    # Step 2.设置查询参数
    params = {
        "q": loc,               
        "appid": OPENWEATHER_API_KEY,    # 输入API key
        "units": "metric",            # 使用摄氏度而不是华氏度
        "lang":"zh_cn"                # 输出语言为简体中文
    }

    # Step 3.发送GET请求
    response = requests.get(url, params=params)
    
    # Step 4.解析响应
    data = response.json()
    return json.dumps(data)

@tool
def write_file(content):
    """
    将指定内容写入本地文件。
    :param content: 必要参数，字符串类型，用于表示需要写入文档的具体内容。
    :return：是否成功写入
    """
    
    return "已成功写入本地文件。"
#----------------------------------------------------------------------------------


#----------------------------------------------------------------------------------
model = init_chat_model(model="deepseek-chat", model_provider="deepseek")  

# 定义 天气查询 工具函数
tools = [get_weather, write_file]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是天气助手，请根据用户的问题，给出相应的天气信息，如果用户需要将查询结果写入文件，请使用write_file工具"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


# 初始化模型
model = init_chat_model("deepseek-chat", model_provider="deepseek")

# 直接使用`create_tool_calling_agent`创建代理
agent = create_tool_calling_agent(model, tools, prompt)


agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)



response = agent_executor.invoke({"input": "查一下宁波和杭州现在的温度，并将结果写入本地的文件中。"})
print(response)
#----------------------------------------------------------------------------------