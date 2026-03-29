from huggingface_hub import snapshot_download
from pathlib import Path

# Set your desired local path on E: drive
mistral_models_path = Path("E:/mistral_models/7B-Instruct-v0.3")
mistral_models_path.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    allow_patterns=["params.json", "consolidated.safetensors", "tokenizer.model.v3"],
    local_dir=mistral_models_path
)

print(f"Model files downloaded to: {mistral_models_path}")
