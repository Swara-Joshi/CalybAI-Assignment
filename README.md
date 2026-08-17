# Calyb AI Engineering Intern Assignment

This repository contains the Calyb AI engineering assignment implementation.
The implemented project is `research-evolution-map/`, a deterministic research
onboarding and reasoning system for a focused study of LLM agent research.

The repository also contains `agent-research-knowledge-system/`, an earlier
configuration-only scaffold. It is not the implementation described below.

## 1. Problem

Research papers about LLM agents describe problems, methods, tasks,
benchmarks, limitations, and follow-on directions in separate documents. A
researcher joining the area needs more than a keyword search: they need to see
which method addresses which problem, which task it targets, what limitations
were recorded, and how later work relates to earlier work.

This project normalizes a selected paper corpus into an explicit knowledge
state and answers a new research proposal with structured, evidence-bearing
links to that state. It is a research navigation and reasoning prototype, not
a claim that the full literature has been captured.

## 2. Why LLM agent research

The configured topic is `Evolution of LLM Agent Research`. This area was
selected because it naturally contains the kinds of evolution links the schema
represents: planning problems lead to methods, methods target tasks, papers
report benchmarks and limitations, and limitations motivate later research
directions. The selected subtopics are:

- planning
- tool use
- memory
- multi-agent coordination

The implementation does not claim that these are the only important areas of
LLM agent research. They are the configured scope for this assignment.

## 3. Exact research scope

The default `ResearchConfig` in
`research-evolution-map/src/config/settings.py` defines:

- Topic: `Evolution of LLM Agent Research`
- Subtopics: planning, tool use, memory, and multi-agent coordination
- Target corpus size: 75 papers
- Allowed range: 50 to 100 papers
- Date range: 2022-01-01 through 2025-12-31
- Queries:
	- `LLM agent planning research`
	- `LLM tool use agent research`
	- `LLM agent memory research`
	- `multi-agent coordination LLM research`

The implemented ingestion adapters are arXiv and Semantic Scholar. `OpenAlex`
is present in the default configuration, but the current `PaperIngestor`
dispatches only `arXiv` and `Semantic Scholar`; unsupported configured sources
are skipped. Therefore OpenAlex must not be reported as an implemented data
source for the current version.

## 4. Dataset size and sources

The intended dataset is a focused corpus of 50–100 papers, with a default
target of 75. The source adapters query arXiv and Semantic Scholar and store
normalized records in `research-evolution-map/data/processed/`.

No processed corpus or serialized knowledge state is committed in the current
checkout. The exact paper count is therefore determined only after ingestion;
it must be read from the ingestion summary and generated artifacts rather than
assumed from the target count. Deduplication is performed by normalized paper
identifier, and the ingestor records how many duplicates were removed.

## 5. System architecture

The implemented flow is:

```text
ResearchConfig
		|
		v
PaperIngestor -> ArxivClient / SemanticScholarClient
		|
		+--> data/raw/       raw source responses
		+--> data/processed/ normalized paper metadata
															|
															v
									build_knowledge_state.py
															|
															v
									KnowledgeState + relationships
															|
															v
							data/knowledge_state/knowledge_state.json
															|
						 +----------------+----------------+
						 v                                 v
			 inspect_knowledge.py              reason.py / evaluate.py
```

The main reasoning components are:

- `ProposalReasoner`: orchestrates proposal parsing, concept matching,
	traversal, evidence collection, and structured output.
- `Subgraph`: collects matched concept nodes and incident relationships.
- `TraversalResult`: performs bounded breadth-first traversal over directed
	relationship edges.
- `EvidenceCollector`: returns relationship provenance, evidence text,
	source-paper IDs, and confidence values.

There is no LLM call, embedding index, vector database, or automatic graph
extraction tool in this implementation.

## 6. Knowledge model

The model is a manually designed Pydantic schema. Entities are stored in typed
collections, and relationships are typed records with source and target IDs.
Relationship compatibility is checked against an explicit
`RELATIONSHIP_TYPE_MAP`.

The serialized state contains:

- metadata, including schema version, dataset name, paper count, generation
	timestamp, and source information;
- papers;
- research problems;
- methods;
- tasks;
- benchmarks;
- limitations;
- research directions;
- typed relationships.

The schema is intentionally explicit so a reviewer can inspect the JSON and
trace a conclusion to a relationship record.

## 7. Entities

All entity definitions are in
`research-evolution-map/src/models/entities.py`.

| Entity | Definition | Why it is in the model |
|---|---|---|
| `Paper` | Paper ID, title, authors, year, abstract, venue, source, and URL | The source unit from which research claims and metadata are organized |
| `ResearchProblem` | Named problem with an optional description | Represents the problem a paper addresses |
| `Method` | Named method with an optional description | Represents an approach proposed or improved by research |
| `Task` | Named task with an optional description | Represents the operational task targeted by a method |
| `Benchmark` | Named benchmark with an optional description | Represents an evaluation setting associated with a paper |
| `Limitation` | Named limitation with an optional description | Represents a limitation recorded by a paper |
| `ResearchDirection` | Named direction with an optional description | Represents a direction motivated by limitations and explored by papers |

These entities are not inferred from an unconstrained graph-learning system;
they are the fixed categories used by the mapping and reasoning code.

## 8. Relationships

The typed relationship classes are in
`research-evolution-map/src/models/relationships.py`.

| Relationship | Source -> target | Why it is in the model |
|---|---|---|
| `addresses` | Paper -> ResearchProblem | Connects a paper to the problem it studies |
| `proposes` | Paper -> Method | Records a method introduced by a paper |
| `targets` | Method -> Task | Connects a method to its target task |
| `evaluates_on` | Paper -> Benchmark | Records an evaluation benchmark |
| `identifies` | Paper -> Limitation | Records a limitation identified by a paper |
| `extends` | Paper -> Paper | Records an extension of prior work |
| `challenges` | Paper -> Paper | Records a challenge to prior work |
| `improves_upon` | Method -> Method | Records method-level improvement |
| `motivates` | Limitation -> ResearchDirection | Connects a limitation to a follow-on direction |
| `explored_by` | ResearchDirection -> Paper | Records a paper exploring a direction |
| `cites` | Paper -> Paper | Represents an internal citation edge |

Every relationship has source and target IDs and a relationship type. Semantic
relationships additionally carry non-empty evidence, a source paper ID, and a
confidence value between 0 and 1. Compatibility validation rejects invalid
source/target entity types and missing entity IDs.

## 9. Knowledge construction

Construction is a deterministic, explicit pipeline:

1. `PaperIngestor` queries configured sources and normalizes source-specific
	 records into `PaperMetadata`.
2. Raw responses are written to `data/raw/` and normalized papers to
	 `data/processed/`.
3. `build_knowledge_state.py` loads the latest processed JSON file.
4. Each paper is mapped with explicit names for problems, methods, tasks,
	 benchmarks, limitations, and directions.
5. `map_paper_to_relationships()` creates typed relationships and attaches
	 deterministic evidence text and confidence values.
6. Entities are deduplicated by canonicalized name within each entity type.
7. The resulting state is validated and serialized.

The current mapping is deterministic and uses the explicit mapping lists in
`build_knowledge_state.py`. It is not an automatic entity extraction system.

## 10. Serialized knowledge state

`KnowledgeStateSerializer` writes a Pydantic `KnowledgeState` to JSON at:

```text
research-evolution-map/data/knowledge_state/knowledge_state.json
```

Before saving, the serializer runs knowledge-state validation by default. On
load, it validates the JSON into the typed state and validates relationships
again. This makes the file independently inspectable and prevents consumers
from silently using references to missing entities or incompatible entity
types.

The file is a dataset snapshot, not a vector index. It can be opened as JSON,
validated with the project script, and traversed without an external service.

## 11. Processing a new research proposal

`ProposalReasoner.reason()` receives proposal text and:

1. strips and validates the input;
2. extracts a small set of configured proposal concepts;
3. matches concepts against names, titles, descriptions, abstracts, and
	 entity IDs in the serialized state;
4. constructs a scoped subgraph from matched IDs;
5. traverses the directed relationships to a maximum depth of two;
6. collects relationship evidence for matched nodes;
7. assembles related papers, methods, problems, limitations, benchmarks, and
	 research directions;
8. returns a structured dictionary containing paths, evidence, confidence,
	 prior approaches, later work, and dataset-scope qualifications.

An empty proposal is rejected. Concept matching is deterministic and uses
token boundaries to avoid matching a concept inside a different word.

## 12. Relationship-based reasoning

The reasoner does not generate a free-form literature answer. It follows
explicit graph edges. For example, a paper-to-method edge followed by a
method-to-task edge forms a bounded path:

```text
Paper --proposes--> Method --targets--> Task
```

The traversal uses breadth-first search over relationship source and target
IDs, tracks visited nodes, and enforces a maximum depth. Evidence is collected
from the actual relationship records encountered or attached to matched
entities. The output therefore exposes both the claimed connection and the
stored provenance fields.

## 13. Installation

From a fresh clone on Windows PowerShell:

```powershell
Set-Location .\CalybAI-Assignment\research-evolution-map
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
cd CalybAI-Assignment/research-evolution-map
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project requires Python 3.10 or newer and Pydantic 2.x. The test
dependencies are included in `requirements.txt`.

## 14. Environment variables

The checked-in `.env.example` contains:

```text
APP_ENV=development
LOG_LEVEL=INFO
```

The current research-evolution-map ingestion clients do not require API keys.
The clients use public arXiv and Semantic Scholar endpoints through `httpx`.
Do not add credentials to the repository. Environment-variable loading is
not required for the default command path.

## 15. Data ingestion

Run from `research-evolution-map/`:

```bash
python scripts/ingest_papers.py
```

This performs live HTTP requests to the implemented arXiv and Semantic Scholar
clients, writes timestamped raw responses under `data/raw/`, and writes a
timestamped normalized paper file under `data/processed/`.

The command is intentionally not used by the automated test suite. Tests mock
the HTTP clients so they do not require network access. Ingestion may return
fewer than the target count if the sources do not provide enough valid unique
records.

To inspect citation edges from the latest processed file:

```bash
python scripts/build_citation_graph.py
```

## 16. Knowledge-state generation

After ingestion, build the serialized state:

```bash
python scripts/build_knowledge_state.py
```

The command reads the latest `data/processed/*.json`, maps the papers into the
fixed schema, writes mapping diagnostics to
`data/processed/mapping_results.json`, and writes the state to
`data/knowledge_state/knowledge_state.json`.

Validate the result independently:

```bash
python scripts/validate_knowledge_state.py
```

## 17. Knowledge inspection

Print counts, relationship types, citation summaries, and example multi-hop
paths:

```bash
python scripts/inspect_knowledge.py
```

Inspect one paper or method:

```bash
python scripts/inspect_knowledge.py --paper-id <paper-id>
python scripts/inspect_knowledge.py --method-id <method-id>
```

Use a different state snapshot with:

```bash
python scripts/inspect_knowledge.py --state path/to/knowledge_state.json
```

## 18. New proposal reasoning

Reason over a proposal using the serialized state:

```bash
python scripts/reason.py \
	--state data/knowledge_state/knowledge_state.json \
	--input "I propose an LLM agent with persistent memory that learns from previous tool interactions."
```

The default output is structured JSON. For a readable summary:

```bash
python scripts/reason.py \
	--state data/knowledge_state/knowledge_state.json \
	--format human \
	--input "I propose an LLM agent with persistent memory that learns from previous tool interactions."
```

The result includes matched IDs, closest prior approaches, evidence records,
bounded reasoning paths, later-work relationships, relevant benchmarks, and
potentially underexplored areas. The qualification in the output explicitly
states that absence from this selected state is not evidence of absence from
the literature and is not a novelty judgment.

## 19. Evaluation

Evaluation data is kept separate from construction data in
`data/evaluation/proposals.json`. It contains manually curated holdout
proposals and gold labels for prior papers, methods, problems, paths, and
evidence. The evaluator rejects the wrong dataset type and proposal IDs that
overlap with construction paper IDs.

After constructing a compatible state, run:

```bash
python scripts/evaluate.py \
	--dataset data/evaluation/proposals.json \
	--state data/knowledge_state/knowledge_state.json \
	--output data/evaluation/report.json \
	--markdown data/evaluation/report.md
```

The report contains per-proposal and aggregate results for:

- prior paper identification;
- method identification;
- research problem identification;
- relationship traversal correctness;
- evidence grounding;
- unsupported conclusion rate;
- structured output validity.

The current evaluation corpus is a small manually curated holdout fixture, not
a claim of statistically representative performance. Its purpose is to verify
that proposal inputs are evaluated separately from the construction path.

## 20. Tests

Run the complete research-evolution-map suite:

```bash
pytest -q
```

The tests cover configuration, mocked source ingestion, deduplication,
citations, entity and relationship validation, state construction,
serialization/deserialization, mapping, subgraphs, bounded traversal,
evidence, proposal reasoning, invalid inputs, missing data, and evaluation.

The suite does not make external API calls. HTTP responses are mocked in
ingestion tests.

## 21. Limitations

- The committed checkout does not contain a processed corpus or serialized
	knowledge-state artifact; those are generated outputs.
- The default target of 75 papers is a configuration target, not a guaranteed
	realized count.
- OpenAlex is configured as a source name but has no implemented adapter.
- Knowledge mapping currently uses deterministic explicit lists in the state
	builder rather than extracting entities from paper text.
- Proposal concept extraction uses a small hardcoded phrase set and is not a
	general natural-language understanding system.
- Relationship traversal is bounded and directed; it does not perform open-
	ended graph search or probabilistic inference.
- Confidence values describe the stored relationship metadata and are not
	calibrated probabilities.
- Research-gap output is bounded by the selected dataset. It does not prove
	novelty, completeness, or absence of related work in the wider literature.
- Live ingestion depends on endpoint availability and source response quality.
- There is a legacy second `KnowledgeState` definition in
	`src/models/knowledge_state.py`; the active serialized pipeline uses
	`src/knowledge/state.py`.

## 22. Future improvements

The next engineering improvements, consistent with the current architecture,
would be:

1. Add an OpenAlex client or remove it from the default configured sources.
2. Make the corpus snapshot reproducible by committing a manifest of paper IDs,
	 source responses, and retrieval metadata.
3. Replace fixed mapping lists with a reviewed annotation workflow while
	 retaining the explicit Pydantic schema and human-auditable relationships.
4. Expand proposal concept extraction and add stronger normalization without
	 turning the system into an uninspectable automatic graph extractor.
5. Add richer relationship-aware ranking and explainable path selection.
6. Expand the manually curated holdout set and report results by subtopic.
7. Consolidate or clearly deprecate the legacy knowledge-state definition.
8. Add rate limiting, caching, and retry backoff for larger live ingestion
	 runs.

## What this is not

This project is not:

- a search engine, although it queries paper sources during ingestion;
- a vector database demonstration, because it stores no embeddings or vector
	index;
- a generic RAG chatbot, because it does not retrieve arbitrary text chunks
	and ask an LLM to synthesize an answer;
- an LLM wrapper, because the current reasoning path is deterministic and has
	no model API dependency;
- an automatic knowledge-graph extraction tool, because the entity and
	relationship categories are human-designed and the current mapping inputs
	are explicit.

Its central artifact is an independently inspectable, typed knowledge-state
JSON snapshot and its central operation is bounded reasoning over explicit
relationships.