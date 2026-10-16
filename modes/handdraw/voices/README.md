# 命名音色

以后给桌面助手文案时，可以直接说：**“用玄骨配音，制作手绘视频：……”**。助手读取本目录的预设，用本机参考资料生成新旁白，再按真实时码排字幕和画面。省去重新找片段、截音和提取人声的步骤；每篇新稿仍须合成，不能复用旧稿音频。

当前预设：`玄骨`，固定版本ID为 `xuangu-v1`。兼容别名“玄骨上人”“萧诧”“xuangu”和旧名 `xiaocha-reference-v1`。这是依据用户提供片段合成的参考音色，实际效果以试听为准。明确指定音色时优先于本机个人默认音色；没有指定时保留原默认选择。

## 查询和调用

完成手绘模式setup后，在仓库根目录运行（Windows将 `python3` 换成已安装的Python命令）：

```sh
python3 tools/kit.py voice handdraw list
python3 tools/kit.py voice handdraw info 玄骨
python3 tools/kit.py voice handdraw synthesize 玄骨 --text-file projects/本期文案.txt --output-dir projects/本期-v1/voice
```

也可传 `--story projects/本期-v1/story.json`，取场景中的完整字幕作为旁白。输出目录必须尚不存在。脚本生成独立连续旁白 `narration.wav/mp3`、原始合成 `synthesis.wav` 和带字符实测时码的 `narration-record.json`；传story时另存一份已绑定所选音色的 `story.json`，不改原稿。默认以0.90倍生成语速交付，保持音高，不自动添加本期故事专用的展示停顿。

助手使用输出story中的voice参数和同目录旁白记录，交给现有手绘字幕工具；先短预览和代表帧，再导出。现有ComfyUI的Edge联网节点不会因为命名音色而自动切换引擎。指定音色未就绪、参考哈希不符、超时或时码异常时明确失败，不静默替换声音，不覆盖旧输出。默认任务超时900秒，可用 `--timeout` 在60—1800秒之间调整。

## 本地资料和迁移

Git同步 `presets.json`、脚本和流程说明。参考录音、模型、生成音频和本机路径保存在被忽略的 `projects/` 中，代码更新保留这些资料。**仅clone仓库到另一台电脑不会自动得到这个音色。**

本地音色资料固定在 `projects/voices/xuangu-v1/`，包含 `reference.wav`、`reference.txt`、`profile.json`。迁移时单独复制整个目录到新仓库相同位置；这是可备份的音色资料包，不包含模型或依赖。每次调用仍校验音频和台词SHA-256，资料缺失或不匹配就停止。

已有原始导出资料时，也可导入同一版本的参考音频与台词：

```sh
python3 tools/kit.py voice handdraw import 玄骨 --audio /本地备份/reference.wav --text-file /本地备份/reference.txt
python3 tools/kit.py voice handdraw configure --python /独立声音环境/bin/python --model-dir /本地模型/Qwen3-TTS-12Hz-1.7B-Base --aligner-dir /本地模型/Qwen3-ForcedAligner-0.6B
```

Windows独立环境Python通常位于 `Scripts/python.exe`。这些路径只写入 `projects/config.local.json` 的 `handdraw.voice_runtime`；仓库内路径保存为相对路径。配置不替换已认可的个人默认音色，也不修改ComfyUI环境。

命名预设工具本身只用Python标准库，不把声音模型依赖加入普通手绘环境。合成在显式配置的独立Python进程执行，结束后释放模型；需要本地FFmpeg和已安装的PyTorch、qwen-tts、qwen-asr、NumPy、SoundFile。本机验证环境使用qwen-tts 0.1.1、qwen-asr 0.0.6、Transformers 4.57.3；本地模型为Qwen3-TTS 1.7B Base和ForcedAligner 0.6B。普通Edge模式不需要这些可选依赖。此工具不负责自动安装、下载模型或新建常驻服务。

用户提供的参考录音及后续输出仍仅在本地；GitHub更新的是可移植的命名、身份校验和调用方式。更换参考资料需要新增预设版本，不在原ID下悄悄换声。仓库同步沿用显式提交推送与快进更新规则，不设置无人确认的自动推送。
