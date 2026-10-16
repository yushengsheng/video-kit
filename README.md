# video-kit · 视频工具箱

一个仓库，多个独立制作模式。共享代码与流程，不同步成片和大素材。

**当前可用：淡彩墨线手绘 `handdraw`。** 包含《井里的月亮》、枸杞食养、办公室漫画、墨线点红四个示例。沙画等模式尚未实现，后续各建独立模块，不修改手绘入口。

## 日常使用

把本仓库作为桌面代码助手的项目打开，然后直接说：

> 用手绘模式制作以下文案，约一分钟，交付 MP4：……

助手依次读取根目录和模式规则，完成分镜、原创代码画面、连续旁白、字幕、预览与导出。**不要求用户准备图片，也不接 GPT 模型 API。** 这不是纯 ComfyUI 从任意文案自动绘图的无人值守程序。

新片、配音复用和画面修订的具体顺序见 [手绘制作流程](modes/handdraw/WORKFLOW.md)。个人生产代码与媒体放在projects独立版本内，复用模式依赖；导出后修改保留旧版。

## 首次安装

需要 Git、Python **3.10+**、Node.js **22+**（含 npm）、Brave 或 Chrome。首次安装依赖和字体需要联网；默认旁白使用 Edge 在线 TTS，也需要联网，本地命名音色另按其说明配置。原验证平台是 **macOS / Apple Silicon**；本地 Windows 11 x64 已验证 `moon` 示例的安装、ComfyUI 短预览与完整 1080p 导出，其他 Windows 示例未逐一导出验证。

```sh
git clone https://github.com/yushengsheng/video-kit.git
cd video-kit
python3 tools/kit.py setup handdraw
python3 tools/kit.py prepare handdraw --example moon
python3 tools/kit.py check handdraw
python3 tools/kit.py render handdraw --example moon --preview
python3 tools/kit.py verify handdraw --example moon --preview
# 看过短预览后：
python3 tools/kit.py render handdraw --example moon
python3 tools/kit.py verify handdraw --example moon
```

自动查找已安装的 Brave / Chrome（Windows 也可使用 Edge），启动独立无界面实例。其他安装位置可设置环境变量 `REMOTION_BROWSER_EXECUTABLE` 为浏览器可执行文件的绝对路径。视频检查优先使用 PATH 中的 ffprobe，否则查找当前平台的 Remotion 工具，也可设置 `FFPROBE_EXECUTABLE`。

Windows PowerShell 中将上述 `python3` 换成 `py -3.10`（本次验证使用 Python 3.10）。文件读写统一使用 UTF-8；无需修改系统编码或 ComfyUI 的 Python 环境。

示例 `--example` 可选 `moon`、`goji`、`comic`、`inkred`。它们是确定内容的可复用示例，不是随便改一句文案就能自动重画。真实新稿由助手准备独立版本画面和代码。示例首次复制到本地 `content/`，不会因代码更新自动覆盖本地稿件；需要最新示例时另建本地副本。

## 命名音色

可直接对助手说：“用玄骨配音，制作手绘视频：……”。本地资料就绪后按名称调用，无需再次截取参考录音；调用方式、预设和说明随仓库更新。运行 `python3 tools/kit.py voice handdraw list` 查看是否就绪，详见 [命名音色与迁移](modes/handdraw/voices/README.md)。

参考录音、模型和个人配置仍留在本地 `projects/`，更新代码会保留；换电脑需另行复制音色资料并配置独立声音环境。普通Edge流程不增加模型依赖，现有ComfyUI联网节点也不会自动切换引擎。

## 目录与隔离

```text
modes.json                已实现模式与版本
modes/handdraw/            独立依赖、绘图器、渲染器、ComfyUI适配、示例和规则
skills/video-kit/          可移植的桌面助手技能
licenses/                 第三方基础素材与字体授权文本
tools/                    安装、模式入口和安全更新工具
projects/                 本地个人项目（不入Git，按需创建）
```

各模式不跨目录导入另一模式内部代码；新增模式在自己的目录完成，再注册到 `modes.json`。修改根工具或公共接口后，应检查受影响的模式；“独立”不意味着不需要回归测试。

## 更新

```sh
python3 tools/update.py          # 获取远端状态，显示可更新提交数
python3 tools/update.py --apply  # 仅快进更新
```

遇到本地代码改动、未跟踪代码、本地提交或非 main 分支时停止，不 reset、不 stash、不强推。被忽略的个人项目、视频和素材不覆盖。依赖改变时重新运行对应模式的 `setup`；已有运行文案和配音不被清除。技能文件随代码更新，若自行装过全局副本，需要另行同步全局副本。

**GitHub 不会自动收到未提交的改动。** 维护者需本地验证后明确提交并推送；不配置无人确认的自动推送。下载者主动运行更新命令获取改进。

## ComfyUI（可选）

先完成手绘 setup，再安装到你自己的 ComfyUI 目录：

```sh
python3 tools/kit.py install-comfy handdraw --comfy-directory /你的/ComfyUI目录
# 仓库更新后，显式同步受管节点与工作流：
python3 tools/kit.py install-comfy handdraw --comfy-directory /你的/ComfyUI目录 --update
```

如果 ComfyUI 启动时指定了 `--user-directory`，安装时也传入相同的 `--user-directory /你的/用户目录`，确保工作流出现在当前界面。

安装后重启 ComfyUI，在“手绘故事”中打开短预览／完整导出。安装器写入本机路径，不把路径上传。已有非本工具安装的节点拒绝覆盖；受管代码或工作流被你手工修改时，更新也停止。默认四节点支持原手绘路径后端，特殊广告示例使用各自独立脚本入口，不把它们冒充四节点自动支持的功能。

## 不上传什么

`.gitignore` 排除成片、音频、大素材、运行缓存、依赖环境、任务快照、个人工程和本机配置。字体与基础画笔由带 SHA-256 的 `assets.json` 首次下载到本地 `public/`，不进仓库；不需要 Git LFS。

旁白音色、发音与画面效果需要实际审查；技术检查不等于主观验收。产品包装示例不是实物认证，食养成分介绍不构成疗效保证。第三方依赖／字体／素材分别适用其许可，Remotion 使用须遵守其授权条款。原创代码尚未另行指定开源许可证，不因仓库公开就推定所有商业复用已获授权。
