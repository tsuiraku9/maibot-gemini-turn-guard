"""Tests for the pure terminal-turn guard."""

import json
import os
import sys
import types
import unittest
from enum import Enum
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class _PluginConfigBase:
    pass


class _MaiBotPlugin:
    pass


def _field(*, default=None, default_factory=None, **kwargs):
    del kwargs
    return default_factory() if default_factory is not None else default


def _hook_handler(*args, **kwargs):
    del args
    del kwargs

    def decorator(func):
        return func

    return decorator


class _HookMode(str, Enum):
    BLOCKING = "blocking"


class _HookOrder(str, Enum):
    LATE = "late"


class _ErrorPolicy(str, Enum):
    SKIP = "skip"


sdk_module = types.ModuleType("maibot_sdk")
sdk_module.Field = _field
sdk_module.HookHandler = _hook_handler
sdk_module.MaiBotPlugin = _MaiBotPlugin
sdk_module.PluginConfigBase = _PluginConfigBase

sdk_types_module = types.ModuleType("maibot_sdk.types")
sdk_types_module.ErrorPolicy = _ErrorPolicy
sdk_types_module.HookMode = _HookMode
sdk_types_module.HookOrder = _HookOrder

sys.modules.setdefault("maibot_sdk", sdk_module)
sys.modules.setdefault("maibot_sdk.types", sdk_types_module)

from plugin import append_user_continuation  # noqa: E402


class AppendUserContinuationTests(unittest.TestCase):
    def test_appends_after_assistant_without_mutating_input(self) -> None:
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "draft"},
        ]

        guarded = append_user_continuation(messages, "continue")

        self.assertEqual(len(messages), 2)
        self.assertEqual(
            guarded,
            [*messages, {"role": "user", "content": "continue"}],
        )

    def test_appends_after_native_model_role(self) -> None:
        guarded = append_user_continuation(
            [{"role": "model", "content": "draft"}],
            "continue",
        )

        self.assertEqual(
            guarded,
            [
                {"role": "model", "content": "draft"},
                {"role": "user", "content": "continue"},
            ],
        )

    def test_role_matching_is_normalized(self) -> None:
        guarded = append_user_continuation(
            [{"role": " Assistant ", "content": "draft"}],
            "  continue  ",
        )

        self.assertEqual(guarded[-1], {"role": "user", "content": "continue"})

    def test_user_terminal_turn_is_unchanged(self) -> None:
        messages = [{"role": "user", "content": "hello"}]

        self.assertIsNone(append_user_continuation(messages, "continue"))

    def test_invalid_message_collections_are_unchanged(self) -> None:
        self.assertIsNone(append_user_continuation(None, "continue"))
        self.assertIsNone(append_user_continuation([], "continue"))
        self.assertIsNone(append_user_continuation(["assistant"], "continue"))

    def test_empty_prompt_is_unchanged(self) -> None:
        messages = [{"role": "assistant", "content": "draft"}]

        self.assertIsNone(append_user_continuation(messages, "  "))

    @unittest.skipUnless(os.environ.get("MAIBOT_FAILED_SNAPSHOT"), "未指定真实失败快照")
    def test_real_failed_snapshot_is_guarded(self) -> None:
        snapshot_path = Path(os.environ["MAIBOT_FAILED_SNAPSHOT"])
        with snapshot_path.open(encoding="utf-8") as snapshot_file:
            snapshot = json.load(snapshot_file)

        messages = snapshot["provider_request"]["request_kwargs"]["messages"]
        guarded = append_user_continuation(messages, "continue")

        self.assertEqual(messages[-1]["role"], "assistant")
        self.assertIsNotNone(guarded)
        self.assertEqual(len(guarded), len(messages) + 1)
        self.assertEqual(guarded[-1], {"role": "user", "content": "continue"})


if __name__ == "__main__":
    unittest.main()
