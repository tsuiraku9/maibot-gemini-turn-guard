"""Gemini-compatible terminal-turn guard for Maisaka planner requests."""

from typing import Any

from maibot_sdk import Field, HookHandler, MaiBotPlugin, PluginConfigBase
from maibot_sdk.types import ErrorPolicy, HookMode, HookOrder


TERMINAL_ASSISTANT_ROLES = frozenset({"assistant", "model"})


def append_user_continuation(messages: Any, prompt: str) -> list[Any] | None:
    """Return a guarded copy when the request ends with an assistant turn.

    ``None`` means the original request should pass through unchanged.
    """

    if not isinstance(messages, list) or not messages:
        return None

    last_message = messages[-1]
    if not isinstance(last_message, dict):
        return None

    role = last_message.get("role")
    if not isinstance(role, str) or role.strip().lower() not in TERMINAL_ASSISTANT_ROLES:
        return None

    normalized_prompt = str(prompt or "").strip()
    if not normalized_prompt:
        return None

    guarded_messages = list(messages)
    guarded_messages.append({"role": "user", "content": normalized_prompt})
    return guarded_messages


class PluginSectionConfig(PluginConfigBase):
    """Plugin-level settings."""

    __ui_label__ = "插件"
    __ui_icon__ = "shield-check"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用 planner 末尾回合兼容修复")
    config_version: str = Field(default="1.0.0", description="配置版本")


class GuardSectionConfig(PluginConfigBase):
    """Terminal-turn guard settings."""

    __ui_label__ = "回合守卫"
    __ui_icon__ = "message-circle-more"
    __ui_order__ = 1

    continuation_prompt: str = Field(
        default="请根据以上上下文继续完成本轮规划。",
        description="仅在请求以 assistant/model 结尾时追加的 user 消息",
    )


class GeminiTurnGuardConfig(PluginConfigBase):
    """Root plugin configuration."""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    guard: GuardSectionConfig = Field(default_factory=GuardSectionConfig)


class GeminiTurnGuardPlugin(MaiBotPlugin):
    """Ensure strict Gemini gateways receive a terminal user turn."""

    config_model = GeminiTurnGuardConfig

    async def on_load(self) -> None:
        self.ctx.logger.info("Gemini Turn Guard 已加载")

    async def on_unload(self) -> None:
        self.ctx.logger.info("Gemini Turn Guard 已卸载")

    async def on_config_update(self, scope: str, config_data: dict[str, Any], version: str) -> None:
        del scope
        del config_data
        del version

    @HookHandler(
        "maisaka.planner.before_request",
        name="ensure_terminal_user_turn",
        description="当 planner 请求以 assistant/model 结尾时追加兼容性 user 回合",
        mode=HookMode.BLOCKING,
        order=HookOrder.LATE,
        error_policy=ErrorPolicy.SKIP,
    )
    async def ensure_terminal_user_turn(self, messages: Any = None, **kwargs: Any) -> dict[str, Any] | None:
        del kwargs

        if not self.config.plugin.enabled:
            return None

        guarded_messages = append_user_continuation(
            messages,
            self.config.guard.continuation_prompt,
        )
        if guarded_messages is None:
            return None

        self.ctx.logger.info("检测到 planner 请求以 assistant/model 结尾，已追加 user 兼容回合")
        return {
            "action": "continue",
            "modified_kwargs": {"messages": guarded_messages},
        }


def create_plugin() -> GeminiTurnGuardPlugin:
    """Create the plugin instance for the MaiBot runner."""

    return GeminiTurnGuardPlugin()
