from openai import OpenAI
from rich import print
import numpy as np
import time

# 新版本 opnai
client = OpenAI(api_key="EMPTY", base_url="http://192.168.102.19:8082/v1")
# model: acge_text_embedding yinka zpoint
t1 = time.time()
response = client.embeddings.create(
    model=["qwen3-embedding", "Conan-embedding-v1"][0],
    input=[
        "我喜欢你" * 1,
    ]
    * 1,
)
t2 = time.time()
print(f"耗时： {(t2-t1)*1000:.2f} ms")
print(response.data)
assert 0
embeddings = [np.array(item.embedding) for item in response.data]  # 转为NumPy数组

v_a = embeddings[0].reshape(1, -1)  # 向量a
v_b = embeddings[1].reshape(-1, 1)  # 向量b
print(v_a.shape)
# 计算余弦相似度
similarity = np.dot(v_a, v_b)[0][0]
print(f"余弦相似度: {similarity:.4f}")
