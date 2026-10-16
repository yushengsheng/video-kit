---
name: video-kit
description: 在 video-kit 仓库中根据文案制作代码手绘视频，复用淡彩墨线、旁白字幕和 Remotion／ComfyUI 流程。用于调用固定视频模板；用户无需准备图片，不接 GPT 模型 API。其他模式以仓库实际注册能力为准。
---

# video-kit

定位当前项目中的 video-kit 仓库根目录（含 modes.json），先读 AGENTS.md、README.md 和所选模式的说明。不要使用作者机器上的固定路径。当前仅 handdraw 已实现；沙画尚未提供，不把计划当可用工具。

用户只提供文案；由助手拆镜、编写匹配情境的原创绘制代码、整理素材、连续配音、字幕、渲染并检查。默认淡彩墨线、暖白纸张、真实描线和局部填色；详细默认读取 modes/handdraw/content/presets/handdraw-story-code-v1.json。原示例脚本并不能自动理解任意文案。

执行命令通过 `python3 tools/kit.py`，先 `list`，初次 `setup handdraw`，示例再 `prepare handdraw --example moon`、`render handdraw --example moon --preview`、检查、完整导出和 `verify`。新稿要另建本期代码与内容，不能只换旧字幕。

保留人物和物件一致性，一两句一个情境，镜头服从旁白时码。先内部短预览再全片；用户已经委托完整成片时，不反复询问已定参数。中药系列额外规则按模式 AGENTS.md 处理。

不接 GPT 模型 API，不索取 Key 或启动代理。字体等基础资源首次下载到忽略的 public/；Edge 配音需要网络。ComfyUI 可选，仅负责本机任务调度，不具备凭文案自动绘图能力。

作品、音频、素材和执行数据留在忽略目录；不入 Git。只报告实际做过的解码、输入哈希、视觉抽帧和试听，不能以命令成功代替内容审查。未经明确授权不推送或发布。
