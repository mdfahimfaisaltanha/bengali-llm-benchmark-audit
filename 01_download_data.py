#!/usr/bin/env python3
"""Step 1-2: Download benchmarks, freeze audit subsamples, write manifest.json.
Run on CPU. Requires: pip install datasets huggingface_hub
"""
import hashlib, json, os, random, subprocess

SEED = 20260727
MAX_ITEMS = 2000  # subsample cap for large benchmarks
OUT = "data"
os.makedirs(OUT, exist_ok=True)
manifest = {"seed": SEED, "benchmarks": {}}

# --- Git-hosted benchmarks ---
GIT_SOURCES = {
    "benqa": "https://github.com/sheikhshafayat/BEnQA",
    # Verify exact repo name on GitHub before running:
    "banglamath": "https://github.com/TabiaTanzin/BanglaMATH-A-Bangla-benchmark-dataset-for-testing-LLM-mathematical-reasoning-at-grades-6-7-and-8",
}
for name, url in GIT_SOURCES.items():
    dest = os.path.join(OUT, name)
    if not os.path.exists(dest):
        subprocess.run(["git", "clone", "--depth", "1", url, dest], check=True)
    commit = subprocess.run(["git", "-C", dest, "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    manifest["benchmarks"][name] = {"source": url, "commit": commit}

# --- Hugging Face benchmarks (TituLLMs suite; verify exact dataset ids on HF) ---
HF_SOURCES = {
    "bangla_mmlu": "hishab/bangla-mmlu",          # [VERIFY id]
    "boolq_bn": "hishab/boolq_bn",                # [VERIFY id]
    "piqa_bn": "hishab/piqa_bn",                  # [VERIFY id]
    "commonsenseqa_bn": "hishab/commonsenseqa_bn",# [VERIFY id]
    "openbookqa_bn": "hishab/openbookqa_bn",      # [VERIFY id]
}
try:
    from datasets import load_dataset
    for name, hf_id in HF_SOURCES.items():
        ds = load_dataset(hf_id, split="test")
        ds.save_to_disk(os.path.join(OUT, name))
        manifest["benchmarks"][name] = {"source": hf_id, "n_items": len(ds),
                                         "fingerprint": ds._fingerprint}
except Exception as e:
    print(f"[WARN] HF download issue ({e}); fix dataset ids and re-run.")

# --- Freeze stratified subsamples ---
random.seed(SEED)
for name, meta in manifest["benchmarks"].items():
    n = meta.get("n_items")
    if n and n > MAX_ITEMS:
        ids = sorted(random.sample(range(n), MAX_ITEMS))
        meta["subsample_ids"] = ids
        meta["subsample_sha256"] = hashlib.sha256(json.dumps(ids).encode()).hexdigest()

with open("manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print("Wrote manifest.json — commit this file and never edit it by hand.")
