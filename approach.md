# Approach

## 1. Problem

The assignment addresses a research-onboarding problem: papers about LLM agents describe problems, methods, tasks, benchmarks, limitations, and follow-on work in separate documents. A researcher joining the area needs to connect those concepts and inspect the evidence for each connection.

The implemented system converts a selected paper corpus into a typed, serialized knowledge state and processes a new proposal against that state. It returns related papers, methods, problems, limitations, benchmarks, research directions, bounded relationship paths, and relationship evidence. It is a deterministic research-navigation prototype. It is not a general literature search engine, a RAG chatbot, an LLM reasoning service, or a system that proves novelty.

The central design choice is to make the knowledge state inspectable JSON with typed relationships rather than an opaque generated answer. That choice follows the repository's implementation: Pydantic models, deterministic mapping, validation, serialization, and graph traversal are all explicit Python operations.

## 2. Research scope

The active project is `research-evolution-map/`. The other project, `agent-research-knowledge-system/`, is a configuration-only scaffold and is not the implementation described here.

The default `ResearchConfig` defines:

- topic: `Evolution of LLM Agent Research`;
- subtopics: planning, tool use, memory, and multi-agent coordination;
- target corpus size: 75 papers;
- allowed corpus range: 50 to 100 papers;
- configured date range: 2022-01-01 through 2025-12-31; and
- queries:
  - `LLM agent planning research`;
  - `LLM tool use agent research`;
  - `LLM agent memory research`; and
  - `multi-agent coordination LLM research`.

The implemented ingestion adapters are arXiv and Semantic Scholar. OpenAlex is named in the default configuration, but `PaperIngestor` has no OpenAlex adapter and skips unsupported sources. Therefore OpenAlex is part of configuration validation, not an implemented ingestion source.

The paper count is a target, not a guaranteed result. Ingestion stops at the configured maximum after valid unique records are collected and may return fewer records. The checked-in repository does not contain a processed corpus or a serialized knowledge-state snapshot, so no realized paper count is asserted in this document.

The date range is also configuration-only in the current ingestion path. `ResearchConfig` validates that the range is well formed, but `PaperIngestor` does not filter normalized results by it. This is recorded as an implementation limitation rather than treated as an achieved dataset property.

## 3. Why this subset of LLM agent research was selected

The selected subtopics are the values actually present in the default configuration. They were retained because they fit the relationship vocabulary implemented by the system: problems can be connected to methods, methods to tasks, papers to benchmarks and limitations, and limitations to research directions. Together, those categories allow the prototype to represent an evolution-oriented path such as:

```text
Paper --proposes--> Method --targets--> Task
Paper --identifies--> Limitation --motivates--> ResearchDirection
ResearchDirection --explored_by--> Paper
```

The repository does not establish that these four subtopics are the complete or objectively best partition of LLM-agent research. The selection is an assignment-scoped, configurable subset that exercises the model and reasoning path. Any research gap identification is consequently bounded by this selected dataset and its recorded relationships.

## 4. Dataset construction

`PaperIngestor` iterates over configured queries, configured sources, and pages of ten results. It calls the implemented arXiv or Semantic Scholar client, stores each raw response under `data/raw/`, normalizes accepted records into `PaperMetadata`, and writes a timestamped normalized list under `data/processed/`.

The adapters request different source fields and normalize them to a common record. arXiv contributes an identifier, title, authors, summary, publication year parsed from the publication date, venue, and an abstract URL. Semantic Scholar contributes an identifier, title, authors, abstract, year, venue, URL, citation count, and reference identifiers. Missing abstract, venue, or URL values are replaced with explicit fallback values during normalization; the ingestor separately counts records that still lack required metadata.

The raw and normalized stages are kept separate because the implementation needs both source-level audit material and a stable input to knowledge-state construction. `build_knowledge_state.py` loads the latest JSON file in `data/processed/`, validates records as `Paper` entities, maps them, and serializes the result to `data/knowledge_state/knowledge_state.json`.

The construction dataset is separate from the evaluation dataset. `data/evaluation/proposals.json` contains new proposal texts and manually curated gold IDs and paths. The builder never reads that file, and the evaluator rejects a dataset whose type is not `new_proposal_holdout`.

## 5. Knowledge representation

The active serialized model is `src/knowledge/state.py`. It stores typed collections for papers, research problems, methods, tasks, benchmarks, limitations, and research directions, plus a discriminated union of typed relationships. State metadata records schema version, dataset name, paper count, generation time, and source information.

Pydantic was chosen because the implementation already uses it to enforce required fields, relationship discriminators, confidence bounds, and serialization/deserialization. Before saving, `KnowledgeStateSerializer` runs validation; loading parses the JSON back into the typed state and validates it again. The result is a portable snapshot that can be inspected and traversed without a database, vector index, or external service.

## 6. Entities and why each was chosen

All entities are defined in `src/models/entities.py`.

| Entity | Stored fields | Why it is included |
|---|---|---|
| `Paper` | ID, title, authors, year, abstract, venue, source, URL | It is the source and unit of organization for paper metadata, provenance, citations, and research claims. |
| `ResearchProblem` | ID, name, description | It represents the problem a paper addresses and gives proposals a problem-level comparison point. |
| `Method` | ID, name, description | It represents an approach proposed by a paper and is the main unit for comparing prior approaches. |
| `Task` | ID, name, description | It represents the operational task targeted by a method, allowing a method to be connected to what it does. |
| `Benchmark` | ID, name, description | It represents an evaluation setting associated with a paper, so output can identify relevant evaluation contexts. |
| `Limitation` | ID, name, description | It records limitations identified by papers and provides the input to the follow-on direction relationship. |
| `ResearchDirection` | ID, name, description | It represents a research direction connected to limitations and papers exploring it. |

These categories are fixed by the implementation rather than discovered dynamically. The choice keeps the state schema small enough for deterministic mapping and makes each returned ID interpretable to an engineering reviewer.

## 7. Relationships and why each was chosen

Relationship compatibility is enforced by `RELATIONSHIP_TYPE_MAP`; each type specifies its allowed source and target entity classes. Every relationship below is represented by a typed Pydantic class.

| Relationship | Source -> target | Why it is included |
|---|---|---|
| `addresses` | Paper -> ResearchProblem | Connects a paper to the problem it studies. |
| `proposes` | Paper -> Method | Records the method introduced by a paper. |
| `targets` | Method -> Task | Connects an approach to its operational target. |
| `evaluates_on` | Paper -> Benchmark | Records the benchmark used for evaluation. |
| `identifies` | Paper -> Limitation | Records a limitation reported by a paper. |
| `extends` | Paper -> Paper | Represents an explicit extension from one paper to another. |
| `challenges` | Paper -> Paper | Represents an explicit challenge to prior work. |
| `improves_upon` | Method -> Method | Represents an explicit method-level improvement. |
| `motivates` | Limitation -> ResearchDirection | Connects a limitation to a follow-on direction. |
| `explored_by` | ResearchDirection -> Paper | Records a paper exploring a direction. |
| `cites` | Paper -> Paper | Represents an internal citation edge. |

The full schema supports all eleven types because the evolution model needs both paper-to-concept links and paper-to-paper or method-to-method evolution links. The default `build_knowledge_state.py` currently supplies fixed problem, method, task, benchmark, limitation, and direction names to each paper. It therefore emits `addresses`, `proposes`, `targets`, `evaluates_on`, `identifies`, `motivates`, and `explored_by`. It passes an empty citation list and does not provide extension or challenge inputs, so `cites`, `extends`, and `challenges` are not emitted by the default build. `improves_upon` is supported by the model but is not created by the current builder. The generic mapper accepts citation, extension, and challenge inputs for callers that provide them.

## 8. Explicit versus semantic relationships

The graph structure is explicit: a relationship has a source ID, target ID, and fixed relationship type, and the state validates that the endpoint types are compatible. Traversal follows those stored directed edges; it does not infer a new edge from proximity or a language model.

The relationship classes are also `SemanticRelationship` subclasses. This name refers to their provenance metadata, not to embedding-based semantic search. Each such record stores non-empty `evidence`, a `source_paper_id`, and a confidence value between 0 and 1. The current mapper creates deterministic evidence strings such as `Paper title: addresses planning under uncertainty` and fixed confidence values by relationship category. These values are metadata supplied by the mapping process; they are not calibrated probabilities.

Proposal matching is lexical. The reasoner searches entity names, titles, descriptions, and abstracts with token boundaries. It does not use embeddings, cosine similarity, an LLM, or a semantic vector index. Thus a proposal can match a concept only where the configured phrase or fallback token is present in searchable text.

## 9. Evidence representation

Evidence is stored on relationship records rather than as free-floating claims. A returned evidence item includes:

- `source_id` and `target_id`;
- `relationship_type`;
- the relationship's evidence string;
- `source_paper_id`; and
- the stored confidence value.

`EvidenceCollector` returns relationships incident to the matched entity IDs. The reasoner also exposes relationship records inside prior-approach, later-work, and direction output. This was chosen because a reviewer can follow an output item back to a concrete graph edge and its source paper identifier.

The evidence text in the current mapper is deterministic metadata-derived text, not a quoted passage from the paper. The system therefore does not claim sentence-level or document-level extraction fidelity.

## 10. Knowledge-state construction

Construction proceeds as follows:

1. Ingest and normalize source results.
2. Load the latest processed JSON file.
3. Add every normalized paper to the state.
4. For each paper, call `map_paper_to_relationships()` with the fixed names used by the builder.
5. Collect the returned entities and relationships.
6. Deduplicate non-paper entities by canonicalized name.
7. Add relationships, suppressing duplicate `(source_id, target_id, relationship_type)` triples.
8. Validate the state and write the serialized JSON snapshot.
9. Write `data/processed/mapping_results.json` with entity counts, relationship counts, invalid relationships, and relationships missing evidence.

The builder uses explicit mapping inputs because that is what the current code implements and because it keeps construction repeatable and reviewable. It is not an automatic extraction workflow from abstracts or full text. The `TODO` descriptions created by the mapper make that boundary visible: names are supplied explicitly, while rich interpretation is not extracted automatically.

## 11. Deduplication decisions

At ingestion time, records are deduplicated by a lower-cased, stripped paper identifier. This prevents the same source record from being retained when it appears in multiple query/source results. The ingestor reports `duplicates_removed` in its summary and stops once the maximum paper count is reached.

At knowledge-state construction time, each non-paper entity type is deduplicated by a canonicalized name. Canonicalization lowercases the name, replaces non-alphanumeric runs with spaces, trims, and collapses whitespace. The first entity with a canonical name is retained. Papers are not name-deduplicated because paper identity is represented by `paper_id` and titles are not treated as stable identifiers.

Relationships are deduplicated by source ID, target ID, and relationship type in `KnowledgeState.add_relationship()`. Evidence or confidence does not create a second edge for the same triple. These decisions keep the graph compact and prevent repeated query results or repeated per-paper fixed mappings from multiplying identical edges.

## 12. Processing a new research proposal

`ProposalReasoner.reason()` accepts proposal text and first rejects empty input. `parse_proposal()` tokenizes the text and looks for a small configured phrase set including persistent memory, tool interactions, LLM agent, planning, memory, tool use, and multi-agent coordination. If no configured phrase is found, it uses up to ten longer fallback tokens.

Each concept is matched against the lower-cased name, title, description, and abstract fields of every entity collection. Matching uses token boundaries, which prevents a concept such as `memory` from matching inside `memorable`. Matches are collected as entity IDs. This deterministic approach was chosen because the repository contains no model or embedding dependency and allows the same proposal to produce the same result for the same state.

The matched IDs seed subgraph construction, traversal, evidence collection, and the structured response. A proposal with no matches still returns the required output shape and can produce a qualified potentially-underexplored observation.

## 13. Construction of relevant subgraphs

`Subgraph` receives the knowledge state and the concept-to-ID matches. Its node set is the union of matched IDs. Its edge set contains every stored relationship whose source or target is one of those nodes. It does not expand the node set through multiple hops and does not rank or infer edges.

The subgraph is therefore an explicit scope around the proposal's lexical matches. The reasoner uses the same matched IDs as traversal starts and then derives related papers, methods, limitations, benchmarks, and directions through the stored relationships. This keeps proposal processing bounded and makes the initial relevance criterion inspectable.

## 14. Multi-hop reasoning

`TraversalResult` builds directed adjacency from relationship source IDs to target IDs and performs breadth-first search from the sorted matched start nodes. The reasoner sets `max_depth=2`, so a returned path contains at most two relationship hops. A visited set prevents cycles and repeated node visits.

For example, a paper matched by a proposal can produce:

```text
Paper -> Method
Paper -> Method -> Task
```

The reasoner retains at most the first ten traversal paths in its output. Separately, it expands selected output fields using direct relationship lookups: paper-to-problem, paper-to-method, method-to-task, paper-to-limitation, paper-to-benchmark, limitation-to-direction, and extension/challenge links where present. This is bounded graph traversal, not open-ended inference.

## 15. Actionable output generation

The output is a structured dictionary suitable for JSON or the human formatter in `scripts/reason.py`. It contains:

- the proposal summary;
- matched problem, method, and paper IDs;
- known limitations, relevant benchmarks, and research directions;
- up to ten bounded reasoning paths;
- relationship evidence and a derived confidence score;
- closest prior approaches with their linked problems, methods, limitations, and evidence;
- later work represented by `extends` and `challenges` relationships;
- directions connected to limitations;
- potentially underexplored areas; and
- `evidence_scope` with dataset and relationship counts and an explicit qualification.

The confidence value is a bounded heuristic based on the number of collected evidence items: `0.5 + 0.08 * evidence_count`, clipped to `[0.3, 0.99]`. It is not a probability calibration. The actionable interpretation is therefore “these stored prior approaches, constraints, benchmarks, and paths are relevant within this state,” not “this proposal is novel.”

When no related paper or later-work link is present, the reasoner may return a potentially-underexplored area. The output explicitly qualifies this as dataset-based and says that it is not a novelty claim. Research gap identification is bounded by the selected dataset, its coverage, and the relationships recorded in it; absence of an edge is not evidence that the wider literature lacks that work.

## 16. Evaluation methodology

Evaluation is implemented in `scripts/evaluate.py` and uses the manually curated three-proposal holdout in `data/evaluation/proposals.json`. The holdout is separate from construction data and contains gold prior paper IDs, method IDs, problem IDs, relationship paths, and evidence keys. Its proposal texts are not read by the state builder.

For each holdout proposal, the evaluator runs the same `ProposalReasoner` against a supplied state and computes:

- prior paper identification precision, recall, and F1;
- method identification precision, recall, and F1;
- research problem identification precision, recall, and F1;
- relationship traversal path precision, recall, and F1;
- evidence grounding, based on predicted evidence with a non-empty string and a valid state edge;
- unsupported conclusion rate, based on returned claim IDs missing from the state or returned evidence; and
- structured output validity, based on required keys and basic types.

The evaluator averages the per-proposal F1 values for identification and path metrics, and the scalar values for the other metrics. It also writes JSON and Markdown reports when run. It rejects the wrong dataset type and rejects a holdout proposal ID that overlaps a construction paper ID.

## 17. Results

The checked-in repository contains no processed paper file, serialized state, `report.json`, or `report.md`. Therefore there is no realized corpus-level or live-ingestion result to report, and the configured target of 75 papers must not be presented as an achieved count.

The repository does contain automated tests for the implemented behavior. They verify mocked ingestion and normalization, duplicate removal, relationship and entity validation, state serialization and reload, deterministic mapping, subgraph incident-edge selection, bounded traversal, evidence provenance, proposal matching, empty-input rejection, human and JSON reasoner scripts, and holdout evaluator behavior. The evaluator tests verify that the three-proposal holdout is accepted, all requested metrics are produced, structured output validity is 1.0 for the fixture state, evidence grounding is non-zero, and construction-data or overlapping-ID misuse is rejected.

These are implementation and fixture-level results, not evidence of statistically representative performance. A quantitative report for a real corpus requires running ingestion, construction, and evaluation against a generated state.

## 18. Design tradeoffs

**Explicit schema versus open-ended extraction.** The fixed Pydantic entity and relationship categories make references, endpoint types, evidence, and serialized output easy to validate. The cost is that concepts outside the schema cannot be represented without code changes.

**Determinism versus language coverage.** Fixed mapping inputs, lexical phrase matching, directed BFS, and deterministic evidence make runs reproducible and easy to debug. They miss paraphrases, implicit relations, and concepts not covered by the phrase set.

**A file snapshot versus a graph database.** JSON keeps the artifact portable, inspectable, and dependency-light. It does not provide database indexing, concurrent updates, or efficient large-corpus querying.

**Bounded traversal versus unrestricted reasoning.** A depth-two search limits cost and makes returned paths understandable. It can miss relationships that require more hops.

**Heuristic confidence versus calibrated confidence.** The output gives consumers a simple signal tied to evidence volume, but the implementation does not support interpreting it as a statistical probability.

**Small holdout versus broad benchmark.** The manually curated holdout tests the end-to-end contract and keeps construction data separate. Three proposals are insufficient to establish general retrieval or reasoning quality.

## 19. What was intentionally excluded

The implemented project intentionally excludes:

- LLM calls and generated natural-language reasoning;
- embeddings, vector search, and a vector database;
- RAG over arbitrary paper chunks;
- automatic entity or relationship extraction from paper text;
- an agent loop or autonomous research workflow;
- OpenAlex ingestion, because no adapter exists;
- guaranteed date filtering, because the configured range is not applied by ingestion;
- claims of complete literature coverage; and
- novelty proof or a conclusion that an unobserved relationship is absent from the literature.

These exclusions follow the actual architecture and keep the central artifact a deterministic, inspectable knowledge-state snapshot.

## 20. Limitations

- The selected corpus is focused and finite; research-gap identification is bounded by its papers and recorded edges.
- No claim is made that the system proves novelty, completeness, or absence of related work.
- The checked-in repository has no generated corpus or state snapshot.
- The configured 75-paper target may not be reached, and the date range is not enforced in the current ingestor.
- OpenAlex is configured but unsupported and therefore skipped.
- The builder applies the same fixed labels to every processed paper rather than extracting paper-specific claims.
- Mapper evidence is deterministic descriptive text, not a source quotation or full-text citation span.
- Proposal concept extraction is a small hardcoded phrase/token mechanism, not general language understanding.
- Relationship traversal is directed and limited to two hops in proposal reasoning.
- The first ten traversal paths are returned, so additional valid paths are omitted from output.
- Confidence values are heuristic metadata and are not calibrated probabilities.
- Ingestion depends on public endpoint availability and response quality; the live path is not used by the automated tests.
- The repository contains a legacy `src/models/knowledge_state.py` definition, while the active serialized pipeline uses `src/knowledge/state.py`.

## 21. What would be built next

The next work should follow the current interfaces rather than replace them:

1. Add an OpenAlex adapter or remove OpenAlex from the default source list so configuration and runtime behavior agree.
2. Enforce the configured date range during ingestion and record retrieval metadata in a reproducible corpus manifest.
3. Preserve the typed schema while replacing fixed per-paper labels with a reviewed annotation workflow that records paper-specific evidence.
4. Expand proposal concept normalization and matching, with tests for paraphrases and domain terminology, while retaining auditable matches.
5. Populate and validate citation, extension, challenge, and method-improvement edges from reviewed inputs.
6. Add relationship-aware ranking and explainable path selection instead of returning only the first ten BFS paths.
7. Expand the holdout set and report results by subtopic, including more unseen and negative proposals.
8. Add caching, rate limiting, and exponential backoff for larger ingestion runs.
9. Consolidate or clearly deprecate the legacy knowledge-state definition.

These are future engineering steps, not capabilities claimed by the current repository.
