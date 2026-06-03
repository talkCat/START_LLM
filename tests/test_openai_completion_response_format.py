from enum import Enum
from typing import Literal, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

# 新版本 opnai
client = OpenAI(api_key="EMPTY", base_url="http://localhost:8082/v1")
model = "qwen3.5"
# 方式一
# output = client.chat.completions.create(
#     model=model,
#     messages=[{"role": "user", "content": "南京到北京多远"}],
# )
# print(output.choices[0].message.content)
# print("-" * 100)
# # 方式二
output = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "用json进行回答"},
        {"role": "user", "content": "南京到北京多远"},
    ],
    response_format={"type": "json_object"},
    extra_body={"enable_thinking": False},
)
print(output.choices[0].message.content)
print("-" * 100)


class ToolData(BaseModel):
    type: Literal["tool"]
    arguments: dict


class AnswerData(BaseModel):
    type: Literal["final_answer", "b"]
    text: str


class OutPut(BaseModel):
    """定义代理的输出格式"""

    data: Optional[ToolData | AnswerData]


# # 方式三
# class Distance(BaseModel):
#     距离: int
#     单位: Data


output = client.beta.chat.completions.parse(
    model=model,
    messages=[{"role": "user", "content": "南京到北京多少公里"}],
    response_format=OutPut,
    extra_body={"enable_thinking": False},
)

print(output.choices[0].message.parsed.model_dump(mode="json"))
print()
