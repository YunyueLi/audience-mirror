"""Structured reasoning providers used by sequential Agent runtimes."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    value: dict[str, Any]
    provider: str
    model_id: str
    model_version: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None


class JsonReasoner(Protocol):
    provider: str
    model_id: str

    def respond_json(self, prompt: str, schema: dict[str, Any]) -> ReasoningResult: ...


class ClaudeCodeJsonReasoner:
    """Development provider that invokes the authenticated Claude Code CLI.

    It is intentionally explicit and local-development oriented. Production
    deployments should use a separately governed API/VPC provider.
    """

    provider = "anthropic-claude-code-cli"

    def __init__(
        self,
        model_id: str = "sonnet",
        *,
        effort: str = "high",
        max_budget_usd: float = 0.25,
        executable: str = "claude",
        timeout_seconds: int = 180,
    ) -> None:
        self.model_id = model_id
        self.effort = effort
        self.max_budget_usd = max_budget_usd
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def respond_json(self, prompt: str, schema: dict[str, Any]) -> ReasoningResult:
        command = [
            self.executable,
            "--print",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
            "--model",
            self.model_id,
            "--effort",
            self.effort,
            "--max-budget-usd",
            str(self.max_budget_usd),
            "--no-session-persistence",
            "--safe-mode",
            "--tools",
            "",
        ]
        started = time.perf_counter()
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if process.returncode != 0:
            error = (process.stderr or process.stdout).strip()
            raise RuntimeError(f"Claude Code CLI failed ({process.returncode}): {error[-1200:]}")
        envelope = json.loads(process.stdout)
        structured = envelope.get("structured_output")
        if structured is None:
            result_text = envelope.get("result")
            if isinstance(result_text, str):
                structured = json.loads(result_text)
        if not isinstance(structured, dict):
            raise ValueError("Claude Code did not return structured_output")
        usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
        return ReasoningResult(
            value=structured,
            provider=self.provider,
            model_id=self.model_id,
            model_version=str(envelope.get("modelUsage") or envelope.get("model") or "cli-current"),
            latency_ms=latency_ms,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            estimated_cost_usd=(
                float(envelope["total_cost_usd"])
                if isinstance(envelope.get("total_cost_usd"), (int, float))
                else None
            ),
        )


class CodexCliJsonReasoner:
    """Local-development adapter for an authenticated Codex CLI session.

    The command runs in a fresh temporary directory, read-only, without project
    rules or a persistent conversation. JSON Schema constrains only the final
    response; the provider is still a remote model and must be governed as such.
    """

    provider = "openai-codex-cli"

    def __init__(
        self,
        model_id: str = "gpt-5.6-sol",
        *,
        effort: str = "xhigh",
        executable: str = "codex",
        timeout_seconds: int = 300,
    ) -> None:
        self.model_id = model_id
        self.effort = effort
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def respond_json(self, prompt: str, schema: dict[str, Any]) -> ReasoningResult:
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="audience-mirror-codex-") as temporary_directory:
            temporary = Path(temporary_directory)
            schema_path = temporary / "response.schema.json"
            output_path = temporary / "response.json"
            schema_path.write_text(
                json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            command = [
                self.executable,
                "exec",
                "--cd",
                str(temporary),
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--model",
                self.model_id,
                "--config",
                f'model_reasoning_effort="{self.effort}"',
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                prompt,
            ]
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            if process.returncode != 0:
                error = (process.stderr or process.stdout).strip()
                raise RuntimeError(f"Codex CLI failed ({process.returncode}): {error[-1200:]}")
            if not output_path.is_file():
                raise ValueError("Codex CLI did not write the structured final response")
            structured = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(structured, dict):
            raise ValueError("Codex CLI structured output is not a JSON object")
        return ReasoningResult(
            value=structured,
            provider=self.provider,
            model_id=self.model_id,
            model_version="cli-current",
            latency_ms=latency_ms,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=None,
        )
