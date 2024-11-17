# Collab AI

## Sample Run Command for MMLU PRO

### Random Question

    python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s business -b 1 -o 4o-mini--flash-1-5

### Specific Question

    python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s physics -q 9206 -o 4o-mini--flash-1-5