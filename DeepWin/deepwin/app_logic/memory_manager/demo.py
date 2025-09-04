import os
from mem0 import Memory,MemoryClient
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
OPENAI_API_KEY = '***'
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["MEM0_API_KEY"] = "***"
# Initialize a LangChain model directly
openai_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    max_tokens=2000
)

# Pass the initialized model to the config
config = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "path": "./faiss_db",
            "collection_name": "test"
        }
    },
    "llm": {
        "provider": "langchain",
        "config": {
            "model": openai_model
        }
    },
    "history_db_path": "./history.db",
}

m = Memory.from_config(config)
client = MemoryClient()

messages = [
    {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
    {"role": "assistant", "content": "How about a thriller movies? They can be quite engaging."},
    {"role": "user", "content": "I'm not a big fan of thriller movies but I love sci-fi movies."},
    {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
]


# result = m.add(messages, user_id="blue", metadata={"category": "movie_recommendations"})
# print(f"add result:-----------------\r\n {result}\r\n")

result = m.get_all(user_id="blue")
print(f"client get all result:-----------------\r\n {result}\r\n")

related_memories = m.search(query="What do you know about me?", user_id="blue")
print(f"related memories:-----------------\r\n {related_memories}\r\n")


