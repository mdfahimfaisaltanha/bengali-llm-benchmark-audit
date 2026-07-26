#!/usr/bin/env bash
# Accuracy evaluation grid via lm-evaluation-harness (deterministic, length-normalized MCQ).
# Existing Bangla tasks in the harness: see lm_eval/tasks/bangla/ (Bangla MMLU, PIQA-bn, etc.)
# Register custom tasks (BEnQA, BanglaMATH, perturbed variants) as YAML task configs first:
#   https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/new_task_guide.md
set -euo pipefail

MODELS=(
  "meta-llama/Llama-3.2-1B-Instruct"
  "meta-llama/Llama-3.2-3B-Instruct"
  "Qwen/Qwen2.5-1.5B-Instruct"
  "google/gemma-2-2b-it"
  # 7B-9B models: add ,load_in_4bit=True to --model_args
)
TASKS="bangla_mmlu,boolq_bn,piqa_bn,commonsenseqa_bn,openbookqa_bn"  # [VERIFY task names in your harness version]

for M in "${MODELS[@]}"; do
  SAFE=$(echo "$M" | tr '/' '__')
  mkdir -p "outputs/${SAFE}"
  lm_eval --model hf \
    --model_args "pretrained=${M},dtype=float16" \
    --tasks "$TASKS" \
    --batch_size auto \
    --seed 20260727 \
    --log_samples \
    --output_path "outputs/${SAFE}/harness"
done
echo "Done. Per-sample logs are required by 06_analyze.py — keep --log_samples on."
