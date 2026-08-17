# Research Evolution Map

This project lays the foundation for a research onboarding system that studies the evolution of LLM agent research. The long-term goal is to collect a focused corpus of research papers, normalize their metadata, and reason over how methods, limitations, and research directions evolve over time.

## Current project scope

This stage is intentionally limited to the project foundation:

- clean modular Python package structure
- explicit research scope configuration
- basic dependency setup
- validation tests

The following are intentionally not implemented yet:

- entity extraction
- relationship extraction
- knowledge graph construction
- RAG
- embeddings
- LLM reasoning
- agents

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate it:
   ```bash
   # macOS / Linux
   source .venv/bin/activate

   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Project structure

- `src/` contains the application package.
- `src/config/` contains project configuration.
- `src/ingestion/` is reserved for future ingestion work.
- `src/models/` contains data models.
- `src/knowledge/` is reserved for knowledge representation work.
- `src/reasoning/` is reserved for reasoning logic.
- `data/` stores raw, processed, and knowledge-state artifacts.
- `tests/` contains validation tests.
