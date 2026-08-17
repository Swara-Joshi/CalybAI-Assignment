# Evaluation Data

`proposals.json` is a manually curated holdout set. It is evaluation-only:
`scripts/build_knowledge_state.py` reads papers from `data/processed`, while
`scripts/evaluate.py` reads this file separately and passes only the resulting
construction snapshot to the reasoner.

Each proposal has gold IDs and relationship paths. The evaluator reports
precision, recall, and F1 for prior papers, methods, and problems; expected
path coverage; evidence grounding; unsupported conclusion rate; and structured
output validity. It writes both `report.json` and `report.md`.

Run from `research-evolution-map/` after constructing a state:

```text
python scripts/evaluate.py --state data/knowledge_state/knowledge_state.json
```

The proposal texts are new inputs, not source papers or construction records.