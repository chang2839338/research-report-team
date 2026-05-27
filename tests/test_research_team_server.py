import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import contracts  # noqa: E402
import research_team_server as server  # noqa: E402
from store import RunStore  # noqa: E402
from workflow import WorkflowEngine  # noqa: E402


class FakeRunner:
    def __init__(self, replies):
        self.replies = list(replies)

    def run(self, prompt, cwd, last_message_path):
        if not self.replies:
            raise AssertionError("no fake reply queued")
        reply = self.replies.pop(0)
        last_message_path.write_text(reply, encoding="utf-8")
        stdout = '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
        return subprocess.CompletedProcess(args=["codex"], returncode=0, stdout=stdout, stderr="")


class ContractTests(unittest.TestCase):
    def test_split_artifact_sections_requires_all_markers(self):
        response = """
<!-- artifact: 01_research.md -->
Research
<!-- artifact: 01_sources.md -->
Sources
<!-- artifact: 01_claims.md -->
Claims
<!-- artifact: 01_gaps.md -->
Gaps
<!-- artifact: 01_numeric_assumptions.md -->
Numbers
"""
        sections = contracts.split_artifact_sections(
            response,
            [
                "01_research.md",
                "01_sources.md",
                "01_claims.md",
                "01_gaps.md",
                "01_numeric_assumptions.md",
            ],
        )
        self.assertEqual(sections["01_research.md"], "Research\n")
        self.assertEqual(sections["01_numeric_assumptions.md"], "Numbers\n")

    def test_split_artifact_sections_fails_on_missing_marker(self):
        response = """
<!-- artifact: 01_research.md -->
Research
"""
        with self.assertRaisesRegex(RuntimeError, "required artifact section missing"):
            contracts.split_artifact_sections(response, ["01_research.md", "01_sources.md"])

    def test_split_artifact_sections_fails_on_duplicate_marker(self):
        response = """
<!-- artifact: a.md -->
A
<!-- artifact: a.md -->
B
"""
        with self.assertRaisesRegex(RuntimeError, "duplicate artifact section"):
            contracts.split_artifact_sections(response, ["a.md"])

    def test_split_artifact_sections_fails_on_unexpected_marker(self):
        response = """
<!-- artifact: a.md -->
A
<!-- artifact: b.md -->
B
"""
        with self.assertRaisesRegex(RuntimeError, "unexpected artifact section"):
            contracts.split_artifact_sections(response, ["a.md"])

    def test_workflow_artifacts_follow_agent_order(self):
        expected = [
            ("manager", "00_task_brief.md"),
            ("researcher", "01_research.md"),
            ("evidence_auditor", "02_evidence_audit.md"),
            ("analyst", "03_analysis.md"),
            ("writer", "04_draft.md"),
            ("reviewer", "05_review.md"),
            ("revision_writer", "06_revision.md"),
            ("final_verifier", "07_final_verification.md"),
            ("publisher", "08_final.md"),
        ]
        actual = [(role.key, role.primary_artifact) for role in contracts.WORKFLOW]
        self.assertEqual(actual, expected)
        self.assertNotIn("05_final.md", contracts.all_artifact_paths())
        self.assertIn("08_final.docx", contracts.all_artifact_paths())
        self.assertIn("08_final_manifest.json", contracts.all_artifact_paths())

    def test_json_round_trips_korean_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp))
            path = Path(tmp) / "status.json"
            payload = {"title": "한국어 제목", "state": "진행 중", "label": "품질 검사 대기"}
            store.write_json(path, payload)
            self.assertEqual(store.read_json(path), payload)


class WorkflowHarnessTests(unittest.TestCase):
    def test_full_workflow_publishes_docx_and_manifest(self):
        replies = [
            "# Task Brief\n\n목표",
            _research_reply(),
            "## Evidence Audit\n\n### Passable Evidence\n\n- OK",
            "## Analysis\n\n### Decision Criteria\n\n- 기준",
            "# Draft\n\n## Executive Summary\n\n초안",
            "## Review\n\n### Approval Decision\n\nApproved",
            "## Final Verification\n\n### Decision\n\nReady to publish",
            "# Final Report\n\n완료",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run1", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run1")

            status = store.read_json(run_dir / "status.json")
            task = store.read_json(run_dir / "task.json")
            self.assertEqual(status["state"], "completed")
            self.assertEqual(status["docx_status"], "generated")
            self.assertEqual(task["outputs"]["final_markdown"], "artifacts/08_final.md")
            self.assertEqual(task["outputs"]["final_docx"], "artifacts/08_final.docx")
            self.assertEqual(task["outputs"]["final_manifest"], "artifacts/08_final_manifest.json")
            self.assertTrue((run_dir / "artifacts" / "08_final.md").is_file())
            self.assertTrue((run_dir / "artifacts" / "08_final.docx").is_file())
            self.assertTrue((run_dir / "artifacts" / "08_final_manifest.json").is_file())

    def test_targeted_revision_runs_revision_writer(self):
        replies = [
            "# Task Brief\n\n목표",
            _research_reply(),
            "## Evidence Audit\n\n- OK",
            "## Analysis\n\n### Decision Criteria\n\n- 기준",
            "# Draft\n\n초안",
            "## Review\n\n### Approval Decision\n\nApproved with targeted revisions",
            "# Revised Draft\n\n수정본",
            "## Final Verification\n\n### Decision\n\nReady to publish",
            "# Final Report\n\n완료",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run2", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run2")

            status = store.read_json(run_dir / "status.json")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertIn("revision_writer", completed)
            self.assertEqual(status["revision_count"], 1)
            self.assertEqual(status["state"], "completed")
            self.assertTrue((run_dir / "artifacts" / "06_revision.md").is_file())
            self.assertTrue((run_dir / "artifacts" / "07_final_verification.md").is_file())
            self.assertTrue((run_dir / "artifacts" / "08_final.md").is_file())

    def test_server_public_response_includes_manifest_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            config = server.ServerConfig(root, root / "runs", "codex", "", "read-only", 30)
            app = server.ResearchTeamServer(config)
            run_dir = app.store.create_run("run3", "제목", "요청", "quality-first")
            response = app.get_run(run_dir.name)
            self.assertIn("artifact_manifest", response)
            self.assertIn("docx_status", response)
            self.assertIn("revision_count", response)

    def test_cli_scaffold_uses_same_final_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = RunStore(root)
            run_dir = root / "manual"
            store.scaffold_workspace(run_dir, "제목", "요청", "codex-quality-first-local-web", True)
            task = store.read_json(run_dir / "task.json")
            self.assertEqual(task["outputs"]["final_markdown"], "artifacts/08_final.md")
            self.assertEqual(task["outputs"]["final_docx"], "artifacts/08_final.docx")
            self.assertEqual(task["outputs"]["final_manifest"], "artifacts/08_final_manifest.json")
            self.assertTrue((run_dir / "artifacts" / "08_final.docx").is_file())


class PromptDocumentRegressionTests(unittest.TestCase):
    def test_manager_prompt_mentions_every_canonical_agent_and_artifact(self):
        text = (ROOT / "prompts" / "manager.md").read_text(encoding="utf-8")
        for name in [
            "Manager",
            "Researcher",
            "Evidence Auditor",
            "Analyst",
            "Writer",
            "Reviewer",
            "Revision Writer",
            "Final Verifier",
            "Publisher",
        ]:
            self.assertIn(name, text)
        for artifact in [
            "00_task_brief.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "05_review.md",
            "06_revision.md",
            "07_final_verification.md",
            "08_final.md",
        ]:
            self.assertIn(artifact, text)

    def test_docs_do_not_reference_old_artifact_names(self):
        checked = [
            ROOT / "README.md",
            ROOT / "SKILL.md",
            ROOT / "references" / "workflow.md",
            ROOT / "references" / "task-contract.md",
            ROOT / "references" / "chatgpt-pro-workflow.md",
            ROOT / "references" / "install-and-update.md",
        ]
        old_names = ["02_analysis.md", "03_draft.md", "04_review.md", "05_final.md"]
        for path in checked:
            text = path.read_text(encoding="utf-8")
            for old_name in old_names:
                self.assertNotIn(old_name, text, f"{old_name} remained in {path}")


def _research_reply():
    return """
<!-- artifact: 01_research.md -->
## Research Memo

근거
<!-- artifact: 01_sources.md -->
## Source Ledger

| ID | Source | Publisher | Date | Type | Credibility | Relevance | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Source | Pub | n/a | primary | high | useful | none |
<!-- artifact: 01_claims.md -->
## Claim Evidence Table

| Claim | Status | Evidence IDs | Confidence | Notes |
| --- | --- | --- | --- | --- |
| Claim | verified | S1 | high | ok |
<!-- artifact: 01_gaps.md -->
## Research Gaps And Risks

- 없음
<!-- artifact: 01_numeric_assumptions.md -->
## Numeric Assumptions Ledger

| Value | Unit | Period | Source ID | Direct Or Derived | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | count | now | S1 | direct | high | ok |
"""


def _write_prompts(root: Path):
    prompts = root / "prompts"
    references = root / "references"
    prompts.mkdir(parents=True)
    references.mkdir(parents=True)
    for name in [
        "manager.md",
        "researcher.md",
        "evidence_auditor.md",
        "analyst.md",
        "writer.md",
        "reviewer.md",
        "revision_writer.md",
        "final_verifier.md",
    ]:
        (prompts / name).write_text(f"# {name}\n", encoding="utf-8")
    (references / "report-quality-rubric.md").write_text("# Rubric\n", encoding="utf-8")
    (references / "quality-checklist.md").write_text("# Checklist\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
