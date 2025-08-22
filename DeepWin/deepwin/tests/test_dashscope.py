import os
from http import HTTPStatus
from dashscope import Application
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
TEST_APP_API_KEY = os.getenv("TEST_APP_API_KEY")
TEST_APP_ID = os.getenv("TEST_APP_ID")

print(DASHSCOPE_API_KEY)
print(TEST_APP_API_KEY)
print(TEST_APP_ID)
# ------------------------------------------------------------
# response = Application.call(
#     # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
#     api_key=os.getenv("TEST_APP_API_KEY"),
#     app_id=os.getenv("TEST_APP_ID"),# 替换为实际的应用 ID
#     prompt='你是谁？')

# if response.status_code != HTTPStatus.OK:
#     print(f'request_id={response.request_id}')
#     print(f'code={response.status_code}')
#     print(f'message={response.message}')
#     print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
# else:
#     print(response.output.text)


# prompt = '请帮我详细整理下这个网页里的内容：https://docs.cherry-ai.com/'
# response = Application.call(
#     api_key=TEST_APP_API_KEY,
#     app_id=TEST_APP_ID,
#     prompt=prompt)
# print(response.output.text)


# ------------------------------------------------------------
# try:
#     client = OpenAI(
#         # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
#         api_key=os.getenv("DASHSCOPE_API_KEY"),
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )

#     completion = client.chat.completions.create(
#         model="qwen-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
#         messages=[
#             {'role': 'system', 'content': 'You are a helpful assistant.'},
#             {'role': 'user', 'content': '你是谁？'}
#             ]
#     )
#     print(completion.choices[0].message.content)
# except Exception as e:
#     print(f"错误信息：{e}")
#     print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")


# ------------------------------------------------------------