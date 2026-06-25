#!/usr/bin/env bash
# 通过 ModelScope 下载 BGE reranker 到 backend/models/
set -euo pipefail

BACKEND_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$BACKEND_ROOT/models/bge-reranker-base"

echo "==> 下载到: $DEST"
echo "==> 来源: ModelScope (BAAI/bge-reranker-base)"

python - <<PY
import shutil
import sys
from pathlib import Path

try:
    from modelscope import snapshot_download
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "modelscope"])
    from modelscope import snapshot_download

dest = Path("$DEST")
dest.mkdir(parents=True, exist_ok=True)

cache = snapshot_download(
    "BAAI/bge-reranker-base",
    cache_dir=str(dest.parent / ".modelscope"),
    allow_patterns=[
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "sentencepiece.bpe.model",
        "sentence_bert_config.json",
        "modules.json",
        "README.md",
    ],
)

src = Path(cache)
for name in [
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
    "sentence_bert_config.json",
    "modules.json",
    "README.md",
]:
    f = src / name
    if f.exists():
        shutil.copy2(f, dest / name)
        print(f"  + {name}")

weights = dest / "model.safetensors"
if not weights.exists():
    print("错误: model.safetensors 未下载成功", file=sys.stderr)
    sys.exit(1)

print(f"完成: {weights} ({weights.stat().st_size // (1024*1024)} MB)")
PY

echo ""
echo "==> backend/.env 确认:"
echo "    RERANK_ENABLED=true"
echo "    RERANK_MODEL_NAME=models/bge-reranker-base"
