import json
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
        self.prompts = []

    def run(self, prompt, cwd, last_message_path):
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError("no fake reply queued")
        reply = self.replies.pop(0)
        last_message_path.write_text(reply, encoding="utf-8")
        stdout = '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
        return subprocess.CompletedProcess(args=["codex"], returncode=0, stdout=stdout, stderr="")


class ContractTests(unittest.TestCase):
    def test_split_artifact_sections_requires_all_markers_and_valid_json(self):
        response = """
<!-- artifact: gate.json -->
{"decision":"ready"}
<!-- artifact: body.md -->
Body
"""
        sections = contracts.split_artifact_sections(response, ["gate.json", "body.md"])
        self.assertEqual(json.loads(sections["gate.json"])["decision"], "ready")
        self.assertEqual(sections["body.md"], "Body\n")

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

    def test_split_artifact_sections_fails_on_bad_json(self):
        response = """
<!-- artifact: gate.json -->
not json
"""
        with self.assertRaisesRegex(RuntimeError, "gate.json is not valid JSON"):
            contracts.split_artifact_sections(response, ["gate.json"])

    def test_workflow_artifacts_follow_quality_first_contract(self):
        expected = [
            ("manager", "00_task_contract.json", "codex"),
            ("researcher", "01_research.md", "codex"),
            ("evidence_auditor", "02_evidence_gate.json", "codex"),
            ("analyst", "03a_decision_frame.md", "codex"),
            ("writer", "04_draft.md", "codex"),
            ("reviewer", "05_review_decision.json", "codex"),
            ("revision_writer", "06_revision.md", "codex"),
            ("final_verifier", "07_final_verification.json", "codex"),
            ("publisher", "08_final.md", "system"),
        ]
        actual = [(role.key, role.primary_artifact, role.execution) for role in contracts.WORKFLOW]
        self.assertEqual(actual, expected)
        for artifact in [
            "00_task_contract.json",
            "01_source_provenance.md",
            "02_evidence_gate.json",
            "03b_option_evaluation.md",
            "04_writer_trace.md",
            "05_claim_audit.md",
            "06_revision_trace.md",
            "07_final_verification.json",
            "08_final_manifest.json",
        ]:
            self.assertIn(artifact, contracts.all_artifact_paths())
        self.assertNotIn("05_final.md", contracts.all_artifact_paths())

    def test_public_publisher_has_no_prompt(self):
        publisher = [role for role in contracts.public_roles() if role["key"] == "publisher"][0]
        self.assertEqual(publisher["execution"], "system")
        self.assertEqual(publisher["prompt"], "")

    def test_json_round_trips_korean_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp))
            path = Path(tmp) / "status.json"
            payload = {"title": "한국어 제목", "state": "진행 중", "label": "최종 검증 대기"}
            store.write_json(path, payload)
            self.assertEqual(store.read_json(path), payload)


class WorkflowHarnessTests(unittest.TestCase):
    def test_full_workflow_publishes_docx_and_manifest_without_llm_publisher(self):
        replies = [
            _manager_reply(),
            _research_reply(),
            _evidence_reply("pass"),
            _analysis_reply("ready"),
            _writer_reply(),
            _review_reply("approved"),
            _final_reply("ready", "artifacts/04_draft.md"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run1", "제목", "요청", "quality-first")
            runner = FakeRunner(replies)
            engine = WorkflowEngine(root, store, runner)

            engine.run_workflow("run1")

            status = store.read_json(run_dir / "status.json")
            manifest = store.read_json(run_dir / "artifacts" / "08_final_manifest.json")
            self.assertEqual(status["state"], "completed")
            self.assertEqual(status["docx_status"], "generated")
            self.assertEqual(status["selected_final_candidate"], "artifacts/04_draft.md")
            self.assertEqual(manifest["selected_source_artifact"], "artifacts/04_draft.md")
            self.assertIn("selected_source_sha256", manifest)
            self.assertEqual(len(runner.prompts), 7)
            self.assertTrue((run_dir / "artifacts" / "08_final.md").is_file())
            self.assertTrue((run_dir / "artifacts" / "08_final.docx").is_file())

    def test_manager_clarification_pauses_before_research(self):
        replies = [_manager_reply(status="needs_user_input")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run2", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run2")

            status = store.read_json(run_dir / "status.json")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertEqual(status["state"], "needs_clarification")
            self.assertTrue(status["pending_user_feedback"])
            self.assertEqual(completed, ["manager"])

    def test_evidence_block_stops_before_analysis(self):
        replies = [_manager_reply(), _research_reply(), _evidence_reply("blocked")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run3", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run3")

            status = store.read_json(run_dir / "status.json")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertEqual(status["state"], "blocked")
            self.assertEqual(completed, ["manager", "researcher", "evidence_auditor"])
            self.assertFalse((run_dir / "artifacts" / "03_analysis.md").is_file())

    def test_analysis_block_stops_before_writer(self):
        replies = [
            _manager_reply(),
            _research_reply(),
            _evidence_reply("pass"),
            _analysis_reply("blocked"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run4", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run4")

            status = store.read_json(run_dir / "status.json")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertEqual(status["state"], "blocked")
            self.assertNotIn("writer", completed)

    def test_targeted_revision_publishes_revision_candidate(self):
        replies = [
            _manager_reply(),
            _research_reply(),
            _evidence_reply("pass"),
            _analysis_reply("ready"),
            _writer_reply(),
            _review_reply("targeted_revision"),
            _revision_reply(),
            _final_reply("ready", "artifacts/06_revision.md"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run5", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run5")

            status = store.read_json(run_dir / "status.json")
            final_text = (run_dir / "artifacts" / "08_final.md").read_text(encoding="utf-8")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertIn("revision_writer", completed)
            self.assertEqual(status["revision_count"], 1)
            self.assertEqual(status["selected_final_candidate"], "artifacts/06_revision.md")
            self.assertIn("Revised Draft", final_text)

    def test_final_verifier_block_prevents_publish(self):
        replies = [
            _manager_reply(),
            _research_reply(),
            _evidence_reply("pass"),
            _analysis_reply("ready"),
            _writer_reply(),
            _review_reply("approved"),
            _final_reply("blocked", "artifacts/04_draft.md", block_publish=True),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run6", "제목", "요청", "quality-first")
            engine = WorkflowEngine(root, store, FakeRunner(replies))

            engine.run_workflow("run6")

            status = store.read_json(run_dir / "status.json")
            completed = [entry["key"] for entry in status["agent_runs"]]
            self.assertEqual(status["state"], "blocked")
            self.assertNotIn("publisher", completed)
            self.assertFalse((run_dir / "artifacts" / "08_final.md").is_file())

    def test_artifact_marker_repair_retries_once(self):
        replies = [
            _manager_reply(),
            "bad response without markers",
            _research_reply(),
            _evidence_reply("blocked"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            store = RunStore(root / "runs")
            run_dir = store.create_run("run7", "제목", "요청", "quality-first")
            runner = FakeRunner(replies)
            engine = WorkflowEngine(root, store, runner)

            engine.run_workflow("run7")

            self.assertEqual(len(runner.prompts), 4)
            self.assertTrue((run_dir / "artifacts" / "01_source_provenance.md").is_file())

    def test_server_public_response_includes_gate_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_prompts(root)
            config = server.ServerConfig(root, root / "runs", "codex", "", "read-only", 30)
            app = server.ResearchTeamServer(config)
            run_dir = app.store.create_run("run8", "제목", "요청", "quality-first")
            response = app.get_run(run_dir.name)
            self.assertIn("artifact_manifest", response)
            self.assertIn("docx_status", response)
            self.assertIn("revision_count", response)
            self.assertIn("final_gate", response["status"])

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
            self.assertTrue((run_dir / "artifacts" / "00_task_contract.json").is_file())


class PromptDocumentRegressionTests(unittest.TestCase):
    def test_prompts_state_role_boundaries_and_non_goals(self):
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
            text = (ROOT / "prompts" / name).read_text(encoding="utf-8")
            self.assertIn("## Non-Goals", text, name)
            self.assertIn("Boundary", text, name)

    def test_docs_do_not_reference_old_artifact_names(self):
        checked = [
            ROOT / "README.md",
            ROOT / "SKILL.md",
            ROOT / "references" / "workflow.md",
            ROOT / "references" / "task-contract.md",
            ROOT / "references" / "chatgpt-pro-workflow.md",
            ROOT / "references" / "install-and-update.md",
            ROOT / "design.md",
        ]
        old_names = ["02_analysis.md", "03_draft.md", "04_review.md", "05_final.md"]
        for path in checked:
            text = path.read_text(encoding="utf-8")
            for old_name in old_names:
                self.assertNotIn(old_name, text, f"{old_name} remained in {path}")


def _manager_reply(status="ready"):
    questions = ["대상 독자는 누구입니까?"] if status == "needs_user_input" else []
    return f"""
<!-- artifact: 00_task_contract.json -->
{{
  "contract_version": "quality-first-v2",
  "workflow_status": "{status}",
  "clarifying_questions": {json.dumps(questions, ensure_ascii=False)},
  "decision_goal": "Goal",
  "target_reader": "Reader",
  "output": {{"format":"decision brief","language":"Korean","tone":"executive","required_sections":[]}},
  "scope": {{"include":[],"exclude":[],"geography":"","time_horizon":""}},
  "evidence_policy": {{"web_research_required": false,"preferred_sources":[],"citation_style":"source IDs","numeric_traceability_required":true,"freshness_requirement":""}},
  "analysis_plan": {{"known_options":[],"initial_criteria":[],"scenarios_required":true}},
  "acceptance_criteria": ["Done"],
  "assumptions": [],
  "role_tasks": {{"researcher":"Extract","evidence_auditor":"Gate","analyst":"Model","writer":"Draft","reviewer":"Audit","revision_writer":"Patch","final_verifier":"Gate","publisher":"Publish"}}
}}
<!-- artifact: 00_task_brief.md -->
## Task Brief

Goal
"""


def _research_reply():
    return """
<!-- artifact: 01_research.md -->
## Research Memo

- [C1] Evidence-backed finding. Sources: [S1]
<!-- artifact: 01_sources.md -->
## Source Ledger

| Source ID | Source | Publisher | Date | Type | Credibility | Relevance | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | [Source](https://example.com) | Pub | n/a | primary | high | useful | none |
<!-- artifact: 01_claims.md -->
## Claim Evidence Table

| Claim ID | Claim | Preliminary support | Evidence IDs | Confidence | Notes |
| --- | --- | --- | --- | --- | --- |
| C1 | Claim | direct | S1 | high | ok |
<!-- artifact: 01_gaps.md -->
## Research Gaps And Risks

- None
<!-- artifact: 01_numeric_assumptions.md -->
## Numeric Assumptions Ledger

| Number ID | Value | Unit | Period | Source ID | Direct Or Derived | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N1 | 1 | count | now | S1 | direct | high | ok |
<!-- artifact: 01_source_provenance.md -->
## Source Provenance

| Source ID | Search query or access path | URL | Access date | Retrieved detail |
| --- | --- | --- | --- | --- |
| S1 | user | https://example.com | 2026-05-27 | snippet |
"""


def _evidence_reply(decision):
    return f"""
<!-- artifact: 02_evidence_gate.json -->
{{"decision":"{decision}","scope_checked":{{"sources":1,"claims":1,"numbers":1}},"blocking_issues":[],"claim_dispositions":[{{"claim_id":"C1","disposition":"usable","required_caveat":"","reason":""}}],"numeric_dispositions":[{{"number_id":"N1","disposition":"usable","required_caveat":"","reason":""}}],"source_issues":[],"analyst_use_rules":[]}}
<!-- artifact: 02_evidence_audit.md -->
## Evidence Audit

{decision}
"""


def _analysis_reply(decision):
    return f"""
<!-- artifact: 03a_decision_frame.md -->
## Decision Frame

Frame
<!-- artifact: 03b_option_evaluation.md -->
## Option Evaluation

Options
<!-- artifact: 03c_scenarios_and_recommendation.md -->
## Scenarios And Recommendation

Recommendation
<!-- artifact: 03_analysis.md -->
## Analysis Rollup

Use option A.
<!-- artifact: 03_analysis_status.json -->
{{"decision":"{decision}","recommendation_supported":{str(decision == "ready").lower()},"blocked_reasons":[],"required_caveats":[],"writer_instructions":[]}}
"""


def _writer_reply():
    return """
<!-- artifact: 04_draft.md -->
# Draft

## Executive Summary

Draft with [S1].
<!-- artifact: 04_writer_trace.md -->
## Writer Trace

| Draft location | Material claim | Claim type | Source IDs or artifact origin | Evidence status | Certainty label | Transformation note | Reviewer attention |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Executive Summary | Draft with S1 | factual | S1 | usable | high | From analysis | no |
"""


def _review_reply(decision):
    required = []
    if decision != "approved":
        required = [
            {
                "id": "R1",
                "severity": "targeted",
                "target_section": "Executive Summary",
                "problem": "Needs caveat",
                "required_action": "Add caveat",
                "evidence_basis": ["S1"],
                "acceptance_check": "Caveat visible",
            }
        ]
    return f"""
<!-- artifact: 05_review_decision.json -->
{{"decision":"{decision}","total_score":15,"blocker_count":0,"reviewed_candidate":"artifacts/04_draft.md","required_revisions":{json.dumps(required)}}}
<!-- artifact: 05_review.md -->
## Review

### Approval Decision
{decision}
<!-- artifact: 05_claim_audit.md -->
## Claim Audit

| Draft claim | Draft location | Evidence status | Source IDs | Trace status | Reviewer note |
| --- | --- | --- | --- | --- | --- |
| Draft | Executive Summary | usable | S1 | found | pass |
"""


def _revision_reply():
    return """
<!-- artifact: 06_revision.md -->
# Revised Draft

## Executive Summary

Revised Draft with caveat [S1].
<!-- artifact: 06_revision_trace.md -->
## Revision Trace

| Revision ID | Status | Evidence refs | Changed locations | Limitation |
| --- | --- | --- | --- | --- |
| R1 | applied | S1 | Executive Summary | none |
"""


def _final_reply(decision, candidate, block_publish=False):
    return f"""
<!-- artifact: 07_final_verification.json -->
{{"decision":"{decision}","candidate_artifact":"{candidate}","block_publish":{str(block_publish).lower()},"unresolved_required_revisions":[],"unsupported_or_new_claims":[],"missing_required_caveats":[],"carry_forward_caveats":[],"publisher_instructions":[]}}
<!-- artifact: 07_final_verification.md -->
## Final Verification

{decision}
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
    (references / "output-templates.md").write_text("# Templates\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
