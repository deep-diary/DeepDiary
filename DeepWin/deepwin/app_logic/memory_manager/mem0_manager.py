import os
from mem0 import MemoryClient

os.environ["MEM0_API_KEY"] = "****"

# class Mem0Manager:
#     def __init__(self):
#         self.client = MemoryClient()
#         self.config = {
#             "api_key": os.getenv("MEM0_API_KEY"),
#             "base_url": os.getenv("MEM0_BASE_URL"),
#             "model": os.getenv("MEM0_MODEL"),
#             "max_tokens": os.getenv("MEM0_MAX_TOKENS"),
#             "temperature": os.getenv("MEM0_TEMPERATURE"),
#         }




client = MemoryClient()

import os
from mem0 import Memory
from langchain_openai import ChatOpenAI

# Set necessary environment variables for your chosen LangChain provider
os.environ["OPENAI_API_KEY"] = "your-api-key"

# Initialize a LangChain model directly
openai_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    max_tokens=2000
)


m = Memory.from_config(config)
messages = [
    {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
    {"role": "assistant", "content": "How about a thriller movies? They can be quite engaging."},
    {"role": "user", "content": "I'm not a big fan of thriller movies but I love sci-fi movies."},
    {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
]
m.add(messages, user_id="alice", metadata={"category": "movies"})


messages = [
    {"role": "user", "content": "Hi, I'm blue. I'm a vegetarian and allergic to nuts."},
    {"role": "assistant", "content": "Hello blue! I'll remember your dietary preferences."}
]

result = client.add(messages, user_id="blue")
print(result)

query = "What should I cook for dinner?"
results = client.search(query, user_id="blue")
print(results)

memories = client.get_all(user_id="blue")
print(memories)

client.add(messages, user_id="blue", metadata={"category": "preferences"})

client.add(messages, user_id="blue", run_id="session-123")

client.add(messages, agent_id="support-bot")

client.add(messages, user_id="blue", async_mode=True)

results = client.search(
    "food preferences", 
    user_id="blue",
    categories=["preferences"],
    metadata={"category": "food"}
)

print(results)