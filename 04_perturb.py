#!/usr/bin/env python3
"""Builds meaning-preserving perturbed variants of a benchmark.
Perturbations: (a) option reorder, (b) distractor sentence insertion,
(c) numeric substitution (math), (d) round-trip paraphrase Bn->En->Bn via NLLB-200.
Usage: python 04_perturb.py --bench data/benqa --kinds reorder distractor paraphrase
Writes: data/<bench>_perturbed_<kind>/items.jsonl
"""
import argparse, json, os, random, re

SEED = 20260727
random.seed(SEED)

DISTRACTORS_BN = [
    # Topical but irrelevant sentences, following the BanglaMATH distraction protocol.
    # Extend this list to >=20 and have a native speaker review.
    "\u098f\u0987 \u09a4\u09a5\u09cd\u09af\u099f\u09bf \u0997\u09a4\u0995\u09be\u09b2 \u09b8\u0982\u09ac\u09be\u09a6\u09aa\u09a4\u09cd\u09b0\u09c7 \u09aa\u09cd\u09b0\u0995\u09be\u09b6\u09bf\u09a4 \u09b9\u09df\u09c7\u099b\u09bf\u09b2\u0964",
]

def reorder(item):
    idx = list(range(len(item["options"])))
    random.shuffle(idx)
    item = dict(item)
    item["options"] = [item["options"][i] for i in idx]
    item["answer_idx"] = idx.index(item["answer_idx"])
    return item

def distractor(item):
    item = dict(item)
    item["question"] = random.choice(DISTRACTORS_BN) + " " + item["question"]
    return item

def numeric_sub(item):
    """Replace numbers with new values; ONLY valid if you recompute the answer.
    Implement per math benchmark with a solver or template; left as guarded stub."""
    raise NotImplementedError("Implement per-benchmark with programmatic answer recomputation.")

_MT = {}
def paraphrase_bn(text):
    """Round-trip Bn->En->Bn with NLLB-200-distilled-600M (runs on free T4)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    if not _MT:
        mid = "facebook/nllb-200-distilled-600M"
        _MT["tok"] = AutoTokenizer.from_pretrained(mid)
        _MT["model"] = AutoModelForSeq2SeqLM.from_pretrained(
            mid, torch_dtype=torch.float16, device_map="auto").eval()
    def tr(t, src, tgt):
        tok, model = _MT["tok"], _MT["model"]
        tok.src_lang = src
        ids = tok(t, return_tensors="pt", truncation=True, max_length=512).to(model.device)
        out = model.generate(**ids, forced_bos_token_id=tok.convert_tokens_to_ids(tgt), max_new_tokens=512)
        return tok.decode(out[0], skip_special_tokens=True)
    return tr(tr(text, "ben_Beng", "eng_Latn"), "eng_Latn", "ben_Beng")

KINDS = {"reorder": reorder, "distractor": distractor, "numeric": numeric_sub}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--kinds", nargs="+", default=["reorder"])
    args = ap.parse_args()

    # Adapt this loader to your benchmark format (same schema as 03_ts_guessing.py).
    def load_items(bench_dir):
        raise SystemExit(f"Adapt load_items() for {bench_dir}, then remove this line.")

    items = load_items(args.bench)
    for kind in args.kinds:
        out_dir = f"{args.bench.rstrip('/')}_perturbed_{kind}"
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "items.jsonl"), "w") as f:
            for it in items:
                if kind == "paraphrase":
                    new = dict(it); new["question"] = paraphrase_bn(it["question"])
                else:
                    new = KINDS[kind](it)
                f.write(json.dumps(new, ensure_ascii=False) + "\n")
        print(f"Wrote {out_dir}/items.jsonl")
    print("MANDATORY: manually verify a 100-item random sample of every perturbed set with a native speaker.")
