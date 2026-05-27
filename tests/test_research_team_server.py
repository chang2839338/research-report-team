import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import research_team_server as server  # noqa: E402


class FakeServer(server.ResearchTeamServer):
    def __init__(self, config, reply):
        super().__init__(config)
        self.reply = reply

    def _run_codex(self, prompt, cwd, last_message_path):
        last_message_path.write_text(self.reply, encoding="utf-8")
        return subprocess.CompletedProcess(args=["codex"], returncode=0, stdout="", stderr="")


class ResearchArtifactTests(unittest.TestCase):
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
"""
        sections = server._split_artifact_sections(
            response,
            ["01_research.md", "01_sources.md", "01_claims.md", "01_gaps.md"],
        )

        self.assertEqual(sections["01_research.md"], "Research\n")
        self.assertEqual(sections["01_sources.md"], "Sources\n")
        self.assertEqual(sections["01_claims.md"], "Claims\n")
        self.assertEqual(sections["01_gaps.md"], "Gaps\n")

    def test_split_artifact_sections_fails_on_missing_marker(self):
        response = """
<!-- artifact: 01_research.md -->
Research
"""
        with self.assertRaisesRegex(RuntimeError, "required artifact section missing"):
            server._split_artifact_sections(response, ["01_research.md", "01_sources.md"])

    def test_run_role_keeps_single_artifact_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "run"
            (root / "prompts").mkdir()
            (run_dir / "prompts").mkdir(parents=True)
            (run_dir / "artifacts").mkdir()
            (root / "prompts" / "analyst.md").write_text("# Analyst\n", encoding="utf-8")
            config = server.ServerConfig(root, root / "runs", "codex", "", "read-only", 30)
            app = FakeServer(config, "Single artifact")

            app._run_role(
                run_dir,
                {"title": "한글 제목", "brief": "한글 요청"},
                {
                    "key": "analyst",
                    "role": "Analyst",
                    "label": "Analysis",
                    "prompt": "analyst.md",
                    "prompt_file": "03_analyst.md",
                    "artifact": "02_analysis.md",
                    "inputs": [],
                    "goal": "Analyze",
                },
            )

            self.assertEqual((run_dir / "artifacts" / "02_analysis.md").read_text(encoding="utf-8"), "Single artifact")

    def test_run_role_writes_research_extra_artifacts(self):
        reply = """
<!-- artifact: 01_research.md -->
연구 메모
<!-- artifact: 01_sources.md -->
출처 원장
<!-- artifact: 01_claims.md -->
주장 검증
<!-- artifact: 01_gaps.md -->
공백 리스크
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "run"
            (root / "prompts").mkdir()
            (run_dir / "prompts").mkdir(parents=True)
            (run_dir / "artifacts").mkdir()
            (root / "prompts" / "researcher.md").write_text("# Researcher\n", encoding="utf-8")
            config = server.ServerConfig(root, root / "runs", "codex", "", "read-only", 30)
            app = FakeServer(config, reply)

            app._run_role(
                run_dir,
                {"title": "한글 제목", "brief": "한글 요청"},
                {
                    "key": "researcher",
                    "role": "Researcher",
                    "label": "Research",
                    "prompt": "researcher.md",
                    "prompt_file": "02_researcher.md",
                    "artifact": "01_research.md",
                    "extra_artifacts": ["01_sources.md", "01_claims.md", "01_gaps.md"],
                    "inputs": [],
                    "goal": "Research",
                },
            )

            self.assertEqual((run_dir / "artifacts" / "01_research.md").read_text(encoding="utf-8"), "연구 메모\n")
            self.assertEqual((run_dir / "artifacts" / "01_sources.md").read_text(encoding="utf-8"), "출처 원장\n")
            self.assertEqual((run_dir / "artifacts" / "01_claims.md").read_text(encoding="utf-8"), "주장 검증\n")
            self.assertEqual((run_dir / "artifacts" / "01_gaps.md").read_text(encoding="utf-8"), "공백 리스크\n")

    def test_json_round_trips_korean_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            payload = {"title": "한글 제목", "state": "진행 중"}
            server._write_json(path, payload)
            self.assertEqual(server._read_json(path), payload)


if __name__ == "__main__":
    unittest.main()
