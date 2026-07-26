#!/usr/bin/env python3
"""Min-K% Prob contamination signal (Shi et al., ICLR 2024) for open-weight models.
Usage: python 02_min_k_prob.py --model meta-llama/Llama-3.2-1B-Instruct --bench data/benqa --k 10 20
Writes: outputs/<model>/<bench>/mink.csv  (one row per item)
"""
import argparse, csv, os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def min_k_score(model, tok, text, k_pcts, device):
    ids = tok(text, return_tensors="pt", truncation=True, max_length=2048).input_ids.to(device)
    with torch.no_grad():
        logits = model(ids).logits
    logprobs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
    token_lp = logprobs.gather(1, ids[0, 1:].unsqueeze(1)).squeeze(1)
    out = {}
    for k in k_pcts:
        n = max(1, int(len(token_lp) * k / 100))
        out[f"mink_{k}"] = token_lp.sort().values[:n].mean().item()
    return out

def load_items(bench_dir):
    """Return list of dicts with 'id' and 'text' (item formatted EXACTLY as distributed).
    Adapt the loader per benchmark format (CSV/JSON on disk from 01_download_data.py)."""
    import json, glob
    items = []
    for path in glob.glob(os.path.join(bench_dir, "**/*.json*"), recursive=True)[:1]:
        with open(path) as f:
            for i, line in enumerate(f):
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                items.append({"id": row.get("id", i), "text": json.dumps(row, ensure_ascii=False)})
    if not items:
        raise SystemExit(f"Adapt load_items() for the format of {bench_dir}")
    return items

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bench", required=True)
    ap.add_argument("--k", nargs="+", type=int, default=[10, 20])
    ap.add_argument("--load-4bit", action="store_true")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    kwargs = dict(device_map="auto", torch_dtype=torch.float16)
    if args.load_4bit:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True,
                                                            bnb_4bit_quant_type="nf4")
    model = AutoModelForCausalLM.from_pretrained(args.model, **kwargs)
    model.eval()

    out_dir = os.path.join("outputs", args.model.replace("/", "__"),
                           os.path.basename(args.bench.rstrip("/")))
    os.makedirs(out_dir, exist_ok=True)
    items = load_items(args.bench)
    with open(os.path.join(out_dir, "mink.csv"), "w", newline="") as f:
        writer = None
        for it in items:
            row = {"id": it["id"], **min_k_score(model, tok, it["text"], args.k, device)}
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=row.keys()); writer.writeheader()
            writer.writerow(row)
    print(f"Wrote {out_dir}/mink.csv ({len(items)} items)")
    print("Remember: run the SAME script on your private probe set for the AUROC baseline.")
