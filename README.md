# MaiBot Gemini Turn Guard

一个最小的 MaiBot SDK 2.x 插件，用于兼容不接受以 `assistant` / `model` 回合结尾的 Gemini API 网关。

## 背景

部分 Gemini 兼容网关会拒绝末尾角色为模型的请求，并返回类似错误：

```text
Requests ending with a model turn are not supported.
```

本插件订阅 `maisaka.planner.before_request`。仅当 planner 请求的最后一条消息角色为 `assistant` 或 `model` 时，才在末尾追加一条中性的 `user` 消息。请求已经以 `user` 结尾时不会进行任何修改。

## 安装

将仓库克隆到 MaiBot 的第三方插件目录：

```bash
cd /path/to/MaiBot/plugins
git clone https://github.com/tsuiraku9/maibot-gemini-turn-guard.git
```

随后通过 WebUI 重载插件，或重启 MaiBot。

## 配置

Runner 首次加载后会根据 `config_model` 生成 `config.toml`：

```toml
[plugin]
enabled = true
config_version = "1.0.0"

[guard]
continuation_prompt = "请根据以上上下文继续完成本轮规划。"
```

## 行为边界

- 只处理 `maisaka.planner.before_request`。
- 只在末尾角色为 `assistant` 或 `model` 时生效。
- 不修改既有消息、工具定义、图片或 system prompt。
- 使用 `HookOrder.LATE`，在同模式的普通 Hook 之后执行最终结构守卫。
- 新版 MaiBot 如果已经确保请求以 `user` 结尾，本插件会自动成为无操作。

## 测试

```bash
python -m unittest discover -s tests -v
```

可选地指定 MaiBot 保存的失败请求快照，验证真实消息结构：

```bash
MAIBOT_FAILED_SNAPSHOT=/path/to/failed-request.json \
  python -m unittest discover -s tests -v
```

## 许可证

MIT
