import json
from openai import OpenAI
from langchain_core.documents import Document
from ragas.testset import TestsetGenerator
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from config import settings

# 1. Завантажити готові чанки з JSON
with open("index/chunks.json", "r", encoding="utf-8") as f:  
    chunks = json.load(f)

documents = [
    Document(page_content=chunk["text"], metadata=chunk["metadata"])
    for chunk in chunks
]

# 2. LLM і embeddings
openai_client = OpenAI(api_key=settings.api_key.get_secret_value())
generator_llm = llm_factory("gpt-4.1-mini", client=openai_client)
generator_embeddings = RagasOpenAIEmbeddings(
    model="text-embedding-3-small",
    client=openai_client,
)

# 3. Генерація тестового датасету
generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
dataset = generator.generate_with_langchain_docs(documents=documents, testset_size=10)

# 4. Результат
df = dataset.to_pandas()
print(df)
df.to_csv("tests/golden_data.csv", index=False)
print(f"\nSaved {len(df)} test samples to tests/golden_data.csv")
