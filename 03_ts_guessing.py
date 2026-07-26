#!/usr/bin/env python3
"""TS-Guessing-style option reconstruction test (generation-based contamination signal).
Masks one INCORRECT option of an MCQ item and asks the model to produce it verbatim.
Usage: python 03_ts_guessing.py --model <hf-id> --bench data/bangla_mmlu [--load-4bit]
Writes: outputs/<model>/<bench>/tsguess.csv
"""
import argparse, csv, os, random
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 20260727
PROMPT = ("\u09a8\u09bf\u099a\u09c7\u09b0 \u09ac\u09b9\u09c1\u09a8\u09bf\u09b0\u09cd\u09ac\u09be\u099a\u09a8\u09c0 \u09aa\u09cd\u09b0\u09b6\u09cd\u09a8\u09c7\u09b0 \u098f\u0995\u099f\u09bf \u0985\u09aa\u09b6\u09a8 \u09ae\u09c1\u099b\u09c7 \u09ab\u09c7\u09b2\u09be \u09b9\u09df\u09c7\u099b\u09c7\u0964 "
          "\u09ae\u09c1\u099b\u09c7 \u09ab\u09c7\u09b2\u09be \u0985\u09aa\u09b6\u09a8\u099f\u09bf \u09b9\u09c1\u09ac\u09b9\u09c1 \u09b2\u09bf\u0996\u09c1\u09a8\u0964\n\n{question}\n{options}\n\n\u09ae\u09c1\u099b\u09c7 \u09ab\u09c7\u09b2\u09be \u0985\u09aa\u09b6\u09a8 ({letter}):")
# Prompt (in Bengali): "One option of the following MCQ has been masked. Write the masked option verbatim."

def load_mcq_items(bench_dir):
    """Adapt per benchmark: must return dicts with id, question, options (list), answer_idx."""
    raise SystemExit(f"Adapt load_mcq_items() for {bench_dir} format, then remove this line.")

def rougeL_f(a, b):
    # lightweight LCS-based ROUGE-L F1
    a, b = a.split(), b.split()
    if not a or not b:
        return 0.0
    dp = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i+1][j+1] = dp[i][j]+1 if a[i]==b[j] else max(dp[i][j+1], dp[i+1][j])
    lcs = dp[-1][-1]
    p, r = lcs/len(b), lcs/len(a)
    return 2*p*r/(p+r) if p+r else 0.0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bench", required=True)
    ap.add_argument("--load-4bit", action="store_true")
    args = ap.parse_args()
    random.seed(SEED)

    tok = AutoTokenizer.from_pretrained(args.model)
    kwargs = dict(device_map="auto", torch_dtype=torch.float16)
    if args.load_4bit:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
    model = AutoModelForCausalLM.from_pretrained(args.model, **kwargs).eval()

    out_dir = os.path.join("outputs", args.model.replace("/", "__"), os.path.basename(args.bench.rstrip("/")))
    os.makedirs(out_dir, exist_ok=True)
    letters = ["A", "B", "C", "D", "E"]
    with open(os.path.join(out_dir, "tsguess.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "masked_idx", "target", "generation", "exact", "rougeL"])
        for it in load_mcq_items(args.bench):
            wrong = [i for i in range(len(it["options"])) if i != it["answer_idx"]]
            m = random.choice(wrong)
            target = it["options"][m]
            opts = "\n".join(f"{letters[i]}. {'____' if i==m else o}" for i, o in enumerate(it["options"]))
            prompt = PROMPT.format(question=it["question"], options=opts, letter=letters[m])
            ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
            with torch.no_grad():
                gen = model.generate(ids, max_new_tokens=48, do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            text = tok.decode(gen[0, ids.shape[1]:], skip_special_tokens=True).strip().split("\n")[0]
            w.writerow([it["id"], m, target, text, int(text == target), round(rougeL_f(text, target), 4)])
    print(f"Wrote {out_dir}/tsguess.csv — also run on the probe set for the chance baseline.")
