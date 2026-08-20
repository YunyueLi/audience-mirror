"""Non-invasive MatrAIx adapter contract and local installation doctor.

The adapter does not import, vendor or modify MatrAIx. It inspects an explicitly
provided checkout and emits a versioned task contract that a future external
runner can consume after the data and license review is complete.
"""

from __future__ import annotations

import os
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..domain import Persona, RunConfig
from ..hashing import fingerprint


AUDITED_COMMIT = "07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9"
ADAPTER_SCHEMA_VERSION = "audience-mirror.matraix-adapter/v0.1"


@dataclass(frozen=True, slots=True)
class MatrAixDoctorReport:
    available: bool
    checkout_path: str | None
    commit: str | None
    audited_commit: str
    audited_commit_match: bool
    project_version: str | None
    code_license: str | None
    media_environment_present: bool
    persona_1m_bundled: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MatrAixAdapter:
    """Inspect and describe an external MatrAIx integration without executing it."""

    def __init__(self, checkout: str | Path | None = None) -> None:
        configured = checkout or os.environ.get("MATRAIX_REPO")
        self.checkout = Path(configured).expanduser().resolve() if configured else None

    def doctor(self) -> MatrAixDoctorReport:
        if self.checkout is None or not self.checkout.is_dir():
            return MatrAixDoctorReport(
                available=False,
                checkout_path=str(self.checkout) if self.checkout else None,
                commit=None,
                audited_commit=AUDITED_COMMIT,
                audited_commit_match=False,
                project_version=None,
                code_license=None,
                media_environment_present=False,
                persona_1m_bundled=False,
                notes=(
                    "Set MATRAIX_REPO or pass --repo to inspect an external checkout.",
                    "No network access or dataset download is performed by this command.",
                ),
            )

        commit = self._git_commit()
        project_version = self._project_version()
        code_license = self._license_name()
        media_present = (self.checkout / "application" / "tasks" / "media").exists()
        persona_1m_bundled = any(
            (self.checkout / candidate).exists()
            for candidate in (
                "persona/datasets/matraix-persona-1m/release",
                "persona/datasets/matraix-persona-1m/data",
            )
        )
        notes = [
            "MatrAIx code and Persona datasets require separate license review.",
            "Audience Mirror does not redistribute Persona 1M.",
            "The current adapter only emits a contract; it does not execute upstream jobs.",
        ]
        if commit != AUDITED_COMMIT:
            notes.append("Checkout differs from the audited commit; rerun compatibility tests before use.")
        if persona_1m_bundled:
            notes.append("A Persona 1M directory was detected; verify source terms before any customer use.")

        return MatrAixDoctorReport(
            available=True,
            checkout_path=str(self.checkout),
            commit=commit,
            audited_commit=AUDITED_COMMIT,
            audited_commit_match=commit == AUDITED_COMMIT,
            project_version=project_version,
            code_license=code_license,
            media_environment_present=media_present,
            persona_1m_bundled=persona_1m_bundled,
            notes=tuple(notes),
        )

    def build_media_task_contract(
        self,
        *,
        timeline: dict[str, Any],
        personas: list[Persona],
        config: RunConfig,
    ) -> dict[str, Any]:
        doctor = self.doctor()
        return {
            "schema_version": ADAPTER_SCHEMA_VERSION,
            "adapter_mode": "contract_only",
            "upstream": {
                "name": "MatrAIx",
                "audited_commit": AUDITED_COMMIT,
                "detected_commit": doctor.commit,
                "compatible": doctor.audited_commit_match,
            },
            "task": {
                "type": "media",
                "experiment_id": config.experiment_id,
                "run_id": config.run_id,
                "timeline_id": timeline["timeline_id"],
                "timeline_hash": fingerprint(timeline),
                "persona_ids": [persona.persona_id for persona in personas],
                "execution": "independent_sequential",
                "output_contract": "audience-mirror.trace/v0.1",
            },
            "data_policy": {
                "persona_dataset_bundled": False,
                "media_bundled": False,
                "requires_separate_license_review": True,
            },
        }

    def _git_commit(self) -> str | None:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.checkout,
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        return completed.stdout.strip() or None

    def _project_version(self) -> str | None:
        pyproject = self.checkout / "pyproject.toml"
        if not pyproject.is_file():
            return None
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return None
        version = data.get("project", {}).get("version")
        return str(version) if version is not None else None

    def _license_name(self) -> str | None:
        license_path = self.checkout / "LICENSE"
        if not license_path.is_file():
            return None
        try:
            first_line = license_path.read_text(encoding="utf-8").splitlines()[0].strip()
        except (OSError, IndexError):
            return None
        return first_line or None
