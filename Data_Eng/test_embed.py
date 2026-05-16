import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

result = client.models.embed_content(
    model    = "models/gemini-embedding-2",
    contents = ["test physics text", "second test"],
    config   = {
        "task_type":             "RETRIEVAL_DOCUMENT",
        "output_dimensionality": 3072,
    },
)

print(f"Type of result          : {type(result)}")
print(f"Attributes              : {dir(result)}")
print(f"result.embeddings type  : {type(result.embeddings)}")
print(f"result.embeddings       : {result.embeddings[:1]}")
print(f"First item type         : {type(result.embeddings[0])}")
print(f"First item attrs        : {dir(result.embeddings[0])}")

# Try different access patterns
try:
    print(f".values length          : {len(result.embeddings[0].values)}")
except Exception as e:
    print(f".values failed          : {e}")

try:
    print(f".embedding length       : {len(result.embeddings[0].embedding)}")
except Exception as e:
    print(f".embedding failed       : {e}")

try:
    print(f"direct list length      : {len(list(result.embeddings[0]))}")
except Exception as e:
    print(f"direct list failed      : {e}")