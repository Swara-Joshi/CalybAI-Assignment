# Agent Research Knowledge System

A structured Python project for studying the evolution of LLM agent research and building a knowledge representation from a focused set of research papers.

## Project goal

This assignment focuses on creating a production-quality foundation for a research knowledge system. The project is intentionally scoped to architecture, data flow, and extensible abstractions before implementing the actual research extraction workflow.

## Current scope

This repository intentionally does not yet implement:

- entity extraction
- relationship extraction
- knowledge graph construction
- the full agent research pipeline

The current phase establishes the project skeleton, configuration, modular package layout, and a clean workflow for future research ingestion and knowledge synthesis.

## Project structure

- `src/` contains the application package.
- `data/raw/` stores source documents and metadata.
- `data/processed/` stores normalized and cleaned intermediate artifacts.
- `data/knowledge_state/` stores the evolving knowledge representation state.
- `tests/` contains validation and smoke tests.
- `scripts/` contains operational utilities.

## Local setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate it:
   ```bash
   # Linux/macOS
   source .venv/bin/activate

   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Copy the sample environment:
   ```bash
   copy .env.example .env
   ```

5. Run a smoke check:
   ```bash
   python -m src.agent_research_knowledge_system
   ```

## Planned phases

- Phase 1: package and environment setup
- Phase 2: source ingestion and canonical paper metadata
- Phase 3: claim extraction and normalized evidence representation
- Phase 4: knowledge state persistence and auditing
- Phase 5: evaluation and iteration over research corpus coverage

