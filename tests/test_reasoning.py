from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from audience_mirror.reasoning import ClaudeCodeJsonReasoner, CodexCliJsonReasoner


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ok"],
    "properties": {"ok": {"type": "boolean"}},
}


class ReasoningAdapterTests(unittest.TestCase):
    def test_claude_prompt_precedes_variadic_tools_option(self) -> None:
        envelope = json.dumps({"structured_output": {"ok": True}, "usage": {}})
        with patch(
            "audience_mirror.reasoning.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, envelope, ""),
        ) as run:
            result = ClaudeCodeJsonReasoner().respond_json("PROMPT", SCHEMA)
        command = run.call_args.args[0]
        self.assertEqual(command[2], "PROMPT")
        self.assertLess(command.index("PROMPT"), command.index("--tools"))
        self.assertTrue(result.value["ok"])

    def test_codex_runs_ephemerally_with_schema_and_reads_final_message(self) -> None:
        def fake_run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text('{"ok":true}', encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("audience_mirror.reasoning.subprocess.run", side_effect=fake_run) as run:
            result = CodexCliJsonReasoner().respond_json("PROMPT", SCHEMA)
        command = run.call_args.args[0]
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[-1], "PROMPT")
        self.assertTrue(result.value["ok"])


if __name__ == "__main__":
    unittest.main()
