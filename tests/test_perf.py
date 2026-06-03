from evalscope.perf.arguments import Arguments
from evalscope.perf.main import run_perf_benchmark
from rich import print

if __name__ == "__main__":
    # [1000, 1500, 2000, 2500, 3000]
    # [2000, 3000, 4000, 5000, 6000]
    args = Arguments(
        url="http://192.168.102.19:8082/v1/chat/completions",  # 请求的URL地址
        parallel=[50][0],  # 并行请求的任务数量
        model="qwen3.5",  # 使用的模型名称
        number=[50][0],  # 请求数量
        api="openai",  # 使用的API服务
        dataset="random",  # 数据集名称
        stream=True,  #  是否启用流式处理
        min_tokens=512,
        max_tokens=512,
        min_prompt_length=250,
        max_prompt_length=256,
        name="qwen3_5_log",
        tokenizer_path="/home/dev/model/Qwen/Qwen3___5-2B/",
        extra_args={"ignore_eos": True},
    )
    run_perf_benchmark(args)
    print(
        "想要了解指标的含义,请访问: https://evalscope.readthedocs.io/zh-cn/latest/user_guides/stress_test/quick_start.html"
    )
