import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate


load_dotenv(dotenv_path="../../../.env", override=True) 

DeepSeek_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(DeepSeek_API_KEY)  # 可以通过打印查看

#----------------------------------------------------------------------------------

# 初始化DeepSeek的API客户端
# client = OpenAI(api_key=DeepSeek_API_KEY, base_url="https://api.deepseek.com")

# # 调用DeepSeek的API，生成回答
# response = client.chat.completions.create(
#     model="deepseek-chat",
#     messages=[
#         {"role": "system", "content": "你是乐于助人的助手，请根据用户的问题给出回答"},
#         {"role": "user", "content": "你好，请你介绍一下你自己。"},
#     ],
# )
# # 打印模型最终的响应结果
# print(response.choices[0].message.content)
#----------------------------------------------------------------------------------


#----------------------------------------------------------------------------------
model = init_chat_model(model="deepseek-chat", model_provider="deepseek")  
# question = "你好，请你介绍一下你自己。"
# # 直接使用模型 + 输出解析器搭建一个链
# basic_qa_chain = model | StrOutputParser()

# # result = model.invoke(question)
# result = basic_qa_chain.invoke(question)
# print(result)
#----------------------------------------------------------------------------------


#----------------------------------------------------------------------------------
schemas = [
    ResponseSchema(name="name", description="用户的姓名"),
    ResponseSchema(name="age", description="用户的年龄")
]
parser = StructuredOutputParser.from_response_schemas(schemas)

prompt = PromptTemplate.from_template(
    "请根据以下内容提取用户信息，并返回 JSON 格式：\n{input}\n\n{format_instructions}"
)

chain = (
    prompt.partial(format_instructions=parser.get_format_instructions())
    | model
    | parser
)
result = chain.invoke({"input": "用户叫李雷，今年25岁，是一名工程师。"})
print(result)  
#----------------------------------------------------------------------------------