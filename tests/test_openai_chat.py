from openai import OpenAI

# 新版本 opnai
client = OpenAI(api_key="EMPTY", base_url="http://192.168.102.19:8082/v1")

stream = True
output = client.chat.completions.create(
    model="qwen3.5",
    messages=[{"role": "user", "content": "你是谁"}],
    stream=stream,
    # reasoning_effort="none",
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    # extra_body={"enable_thinking": True},
)
if stream:
    for chunk in output:
        print(chunk)
        # print(
        #     getattr(chunk.choices[0].delta, "reasoning_content", ""), end="", flush=True
        # )
        # print(chunk.choices[0].delta.content or "", end="", flush=True)
else:
    print(output.choices[0].message.content)
print()
