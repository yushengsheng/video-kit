# 新稿制作与修订流程

这份流程由桌面助手执行。用户提供文案并可指定音色；分镜、代码绘画、旁白时码、字幕和导出由助手准备。现有示例和ComfyUI节点不能从任意文案自行创作画面。

## 1. 独立项目与原稿

每部新片放在仓库根目录 `projects/<故事名>-v1/`。本期 `src/`、画稿生成器、story/art JSON、渲染与检查脚本都放进个人项目，不向共享模式的src目录不断添加个人作品入口。复用本模式已有依赖和基础素材，不重复安装Node或复制模型。

建议项目包含 `story-input.json`、`voice/`、`create_art.py`、`art.json`、`src/`、`prepare.py`、`render.mjs`、`verify.py`、`timeline.json`、`captions.srt`、`out/`。这些是本地生产资料，不作为空框架预先提交。

保持用户原稿，按一两句拆镜；画面说明不读进旁白。食品和养生内容保留传统解释、现代证据和个人条件的区分。新稿绘制新情境，延用角色、画风和造型原语，不用无关旧画面替换字幕。

## 2. 明确选声，再绑定实测时间

用户指定“玄骨”等名称时，先按 [命名音色说明](voices/README.md) 查询资料和运行环境，再调用：

```sh
python3 tools/kit.py voice handdraw info 玄骨
python3 tools/kit.py voice handdraw synthesize 玄骨 --story projects/本期-v1/story-input.json --output-dir projects/本期-v1/voice
```

声音生成期间可以编写画面；正式排镜依据最终旁白的实测字符时码。语速、停顿或音频处理一旦变化，字幕时码也必须按最终声音重建或明确变换。普通Edge示例仍走原prepare入口；现有ComfyUI的Edge节点不自动切换成本地模型。

命名工具生成的 `voice/story.json` 含实际voice参数；`voice/narration-record.json` 的签名绑定完整文字和voice参数。将这份绑定正确的story和音频记录一起用于缓存字幕接口，不保留原稿里未实际使用的声音参数。内容、音色和音频身份不匹配时停止，不悄悄借用旧声音。

只改画面或片尾时，文案、voice参数和参考身份完全匹配的旁白可以复用，不重复合成。新版本的story顶层id/version仍应更新；不能把旧 `voice/story.json` 原样复制后，覆盖掉本期的版本标识。

## 3. 项目入口和依赖

个人项目的TSX可以直接放在projects下。渲染脚本用 `createRequire` 读取本模式已安装的Remotion包；bundle明确指定本模式根目录、public目录和模块查找位置。以下片段用于助手编写本期脚本，不是新增的通用自动制片命令：

```js
const mode = path.resolve(root, '../../modes/handdraw');
const require = createRequire(path.join(mode, 'package.json'));
const {bundle} = require('@remotion/bundler');
const serveUrl = await bundle({
  entryPoint: path.join(root, 'src/index.tsx'),
  rootDir: mode,
  publicDir: path.join(mode, 'public'),
  enableCaching: false,
  webpackOverride: config => ({
    ...config,
    resolve: {...config.resolve, modules: [path.join(mode, 'node_modules'), 'node_modules']},
  }),
});
```

TypeScript检查也指向已有模式依赖及 `@types/react`，不为个人入口安装第二套包。story.id、timeline.id、注册的Composition id和选择渲染的id必须一致，进入长时间渲染前检查。相同缓存目录下的预览、静帧和完整渲染顺序执行；隔离的个人入口可关闭bundle缓存，避免多个进程竞争同一缓存文件。

## 4. 绘画与镜头节奏

沿用暖白纸张、淡彩墨线、真实路径描线、局部填色和笔尖跟随；书页文字可随画面出现，但字体渐显不表述为真实汉字逐笔书写。SVG数值解析需支持科学计数法，或先将计算结果格式化成普通小数，避免三角函数产生的极小数被误判成命令。

短镜头应给完整人物和关键道具留出可见时间；连续的短姿态变化可以保留已画好的角色。片尾若重点是日光、呼吸或烛火变化，应让完整画面保持，只改变目标效果，不在旁白结束前一直重画场景。绘画完成度与效果时间分开控制：保持画面完整时，日光仍从本镜真实时间开始渐变，不能把所有时间都提前到完成状态。

必要时在旁白后留少量无声画面，让变化落稳；同时更新总帧数、最后一镜时长和实际导出范围，不拉长语音或改写已定稿原文。

## 5. 验证与版本保护

先做类型检查、短预览和代表帧检查，再完整导出1080p、30fps、H.264/AAC。默认不加配乐。完整导出后重新抽查编码文件，至少覆盖每镜、所有变体、描绘初中末阶段和关键光线变化，不能只检查渲染前静帧。

技术检查覆盖原稿与字幕、非重叠时码、音色及参考身份、音轨与源旁白对应、尾部未截断、完整解码、尺寸／帧率／时长、文件哈希和画面边界。记录画面、声音、时间轴、组件、渲染脚本及用到的公共辅助脚本、预设和依赖锁文件的身份，防止改了输入却使用旧检查结果。

技术解码、强制对齐、机器转写、画面抽帧和主观试听分别记录。未实际听验，不称逐字发音、相似度或自然度通过。静图推拉、小幅呼吸和道具轻动效不表述为完整人物表演。

完整导出后需要修改，另建v2等新版本，保留先前成片及其输入，检查版本id对应关系。失败或未完成输出不作为成片交付；已有文件不靠覆盖修复。提交共享流程改动前运行模式检查、更新保护测试及Git文件范围检查。

## 6. 同步与本地资料

共享代码、预设、文档和测试经验证后，在用户明确要求时提交推送。成片、录音、模型、个人路径和本期工程仅留本地。音色预设随代码更新，参考资料需单独备份或迁移。

拉取更新仍只允许快进，不reset、不自动stash，不清理作品。ComfyUI节点代码更新后，用安装器的 `--update` 显式同步；如启动时自定义了user-directory，安装时传相同目录。保留受管文件的本地修改保护，不自动重启服务。
