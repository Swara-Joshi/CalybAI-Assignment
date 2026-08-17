from pathlib import Path

from scripts.inspect_knowledge import _load_state


def test_load_state_from_serialized_file(tmp_path) -> None:
    state_path = tmp_path / "knowledge_state.json"
    state_path.write_text(
        '{"metadata":{"schema_version":"1.0","dataset_name":"research-evolution-map","paper_count":1,"generated_at":"2024-01-01T00:00:00+00:00","source_information":{}},"papers":[{"paper_id":"p1","title":"Paper One","authors":["A"],"year":2024,"abstract":"Abstract","venue":"ICML","source":"arxiv","url":"https://example.com/p1"}],"research_problems":[],"methods":[],"tasks":[],"benchmarks":[],"limitations":[],"research_directions":[],"relationships":[]}',
        encoding="utf-8",
    )

    state = _load_state(state_path)
    assert state.metadata.paper_count == 1
    assert state.papers[0].paper_id == "p1"
