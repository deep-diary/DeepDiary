# from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_tavily import TavilySearch
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

load_dotenv(dotenv_path="../../../.env", override=True) 

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
print(f"TAVILY_API_KEY: {TAVILY_API_KEY}")  # 可以通过打印查看

search = TavilySearch(max_results=2)


tools = [search]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一名助人为乐的助手，并且可以调用工具进行网络搜索，获取实时信息。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# 初始化模型
model = init_chat_model("deepseek-chat", model_provider="deepseek")

agent = create_tool_calling_agent(model, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

agent_executor.invoke({"input": "请问DeepDiary是什么？"})
