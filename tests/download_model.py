"""
使用 Hugging Face 下载:
pip install -U huggingface_hub hf_transfer

使用 ModelScope 下载:
pip install modelscope
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


ENV_FILE = Path(__file__).with_name("download_model.env")


def load_env_file(env_file: Path) -> None:
    """从简单的 KEY=VALUE 文件中加载环境变量。"""
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def model_download(
    model_id: str,
    output_dir: str,
    hub_name: str = "hf",
    repo_type: str = "model",
) -> None:
    # 配置 hf 镜像；如果环境中已经显式设置，就尊重外部设置。
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    token = os.environ.get("HF_TOKEN")

    if hub_name == "hf":
        if not token:
            raise ValueError("HF_TOKEN is required when hub_name='hf'")

        cmd = [
            "huggingface-cli",
            "download",
            "--repo-type",
            repo_type,
            "--resume-download",
            model_id,
            "--local-dir",
            output_dir,
            "--local-dir-use-symlinks",
            "False",
            "--token",
            token,
        ]
        subprocess.run(cmd, check=True)
        print(f"下载完成: {model_id} -> {output_dir}")
    elif hub_name == "modelscope":
        from modelscope.hub.snapshot_download import snapshot_download

        snapshot_download(model_id=model_id, local_dir=output_dir, repo_type=repo_type)
        print(f"下载完成: {model_id} -> {output_dir}")
    else:
        raise ValueError("hub_name 只支持 hf 和 modelscope")


if __name__ == "__main__":
    load_env_file(ENV_FILE)

    model_id = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
    output_dir = os.environ.get(
        "MODEL_OUTPUT_DIR", "/home/dev/model/Qwen/Qwen2.5-0.5B-Instruct"
    )
    hub_name = os.environ.get("MODEL_HUB", "hf")
    repo_type = os.environ.get("MODEL_REPO_TYPE", "model")

    model_download(
        model_id=model_id,
        output_dir=output_dir,
        hub_name=hub_name,
        repo_type=repo_type,
    )
