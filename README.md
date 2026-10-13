# How Reliable Are Bengali LLM Benchmarks? — Audit Code
​
[![DOI](https://img.shields.io/badge/DOI-10.21203%2Frs.3.rs--10491036%2Fv1-blue)](https://doi.org/10.21203/rs.3.rs-10491036/v1)
​
Official code for the paper:
​
> **How Reliable Are Bengali LLM Benchmarks? A Cross-Lingual Contamination and Robustness Audit of Open-Weight Language Models**
> Md Fahim Faisal Tanha — Research Square (2026)
> DOI: [10.21203/rs.3.rs-10491036/v1](https://doi.org/10.21203/rs.3.rs-10491036/v1)
​
## What this repository does
​
Audits Bengali LLM benchmarks (translations of established English test sets) with three complementary signals:
​
1. **Min-K% Prob** — likelihood-based membership probing
2. **TS-Guessing** — guided reconstruction of withheld item content
3. **Perturbation robustness** — score and ranking stability under meaning-preserving perturbations
​
Pilot evaluation runs on BoolQ-bn with open-weight instruction models on free-tier GPUs (Kaggle/Colab T4, 4-bit quantization).
​
## Repository structure
​
| File | Purpose |
| --- | --- |
| `01_download_data.py` | Fetch benchmark data |
| `02_min_k_prob.py` | Likelihood-probe signal |
| `03_ts_guessing.py` | Reconstruction-test signal |
| `04_perturb.py` | Perturbation generation and scoring |
| `05_run_eval.sh` | GPU evaluation driver |
| `06_analyze.py` | Regenerates every table and statistic in the paper |
| `pilot_boolq_bn.ipynb` | Pilot run notebook (BoolQ-bn) |
| `pilot_data/` | Pilot sample data |
| `manifest.json` | Frozen run manifest (hashes, seeds) |
​
## Reproduce
​
```bash
python3 01_download_data.py
python3 02_min_k_prob.py && python3 03_ts_guessing.py && python3 04_perturb.py
bash 05_run_eval.sh        # GPU step (Kaggle/Colab T4)
python3 06_analyze.py      # all paper tables and statistics
```
​
## Citation
​
```bibtex
@misc{tanha2026bengali,
  author = {Tanha, Md Fahim Faisal},
  title  = {How Reliable Are Bengali LLM Benchmarks? A Cross-Lingual Contamination and Robustness Audit of Open-Weight Language Models},
  year   = {2026},
  doi    = {10.21203/rs.3.rs-10491036/v1},
  note   = {Preprint, Research Square}
}
```
​
## License
​
Code: MIT (see `LICENSE`). Preprint text: CC BY 4.0.
​
