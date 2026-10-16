"""ComfyUI front end for the local, versioned Remotion story renderer."""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import folder_paths
from comfy.model_management import throw_exception_if_processing_interrupted

CONFIG_FILE = Path(__file__).parent/"config.json"
CONFIG = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.is_file() else {}
DEFAULT_PROJECT = CONFIG.get("project_directory", "")
SPEECH_MODES = {"仅复用匹配缓存（离线）":"cached", "缺失时生成配音（联网）":"generate_missing"}
RENDER_MODES = {"首镜预览":"preview", "完整视频":"full"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(path, parent):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError("文件必须位于选定的项目目录内。")
    return path


def execute(project, command, log_name):
    directory = project/".cache/comfyui-handdraw-logs"
    directory.mkdir(parents=True,exist_ok=True)
    log = directory/log_name
    env = os.environ.copy()
    node = shutil.which("node")
    if node:
        env["PATH"] = str(Path(node).parent)+os.pathsep+env.get("PATH","")
    with log.open("w") as output:
        process = subprocess.Popen(command,cwd=project,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        deadline = time.monotonic()+1800
        try:
            while process.poll() is None:
                throw_exception_if_processing_interrupted()
                if time.monotonic()>deadline:
                    raise TimeoutError("运行超过 30 分钟；请查看日志："+str(log))
                time.sleep(.25)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
    lines = log.read_text().splitlines()
    if process.returncode:
        raise RuntimeError("执行失败，日志："+str(log)+"\n"+"\n".join(lines[-12:]))
    return json.loads(lines[-1])


def python_for(project):
    python = project/".cache/moon-tools-venv/bin/python"
    if not python.is_file():
        raise ValueError("视频工具环境缺失，请按手绘工作流说明建立 .cache/moon-tools-venv。")
    return str(python)


class HanddrawLoadStory:
    CATEGORY = "视频制作/手绘故事"
    FUNCTION = "load"
    RETURN_TYPES = ("HANDDRAW_SOURCE",)
    RETURN_NAMES = ("文案与画面",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "project_directory": ("STRING",{"default":DEFAULT_PROJECT}),
            "story_file": ("STRING",{"default":"content/handdraw-moon-v1/story.json"}),
            "art_file": ("STRING",{"default":"content/handdraw-moon-v1/art.json"}),
        }}

    @classmethod
    def IS_CHANGED(cls,project_directory,story_file,art_file):
        project = Path(project_directory).expanduser().resolve()
        files = [inside(project/story_file,project),inside(project/art_file,project),
                 *[project/name for name in ["scripts/handdraw_job.py","scripts/create_moon_voice.py","scripts/render-handdraw-job.mjs","src/handdraw-moon/Video.tsx","src/handdraw-moon/comfy.tsx",
                                            "public/handdraw-moon-v1/paper.jpg","public/handdraw-moon-v1/drawing-hand.png","public/fonts/NotoSerifSC-Regular.ttf"]]]
        return hashlib.sha256("".join(sha(path) for path in files).encode()).hexdigest()

    def load(self,project_directory,story_file,art_file):
        project = Path(project_directory).expanduser().resolve()
        story = inside(project/story_file,project)
        art = inside(project/art_file,project)
        if not story.is_file() or not art.is_file():
            raise ValueError("找不到文案或画面 JSON，请检查节点中的文件位置。")
        python_for(project)
        return ({"project":str(project),"story_file":story.relative_to(project).as_posix(),"art_file":art.relative_to(project).as_posix()},)


class HanddrawNarration:
    CATEGORY = "视频制作/手绘故事"
    FUNCTION = "prepare"
    RETURN_TYPES = ("HANDDRAW_JOB",)
    RETURN_NAMES = ("含配音字幕的任务",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{"source":("HANDDRAW_SOURCE",),"speech_mode":(list(SPEECH_MODES),)}}

    @classmethod
    def IS_CHANGED(cls,**kwargs):
        return float("nan")

    def prepare(self,source,speech_mode):
        if speech_mode not in SPEECH_MODES:
            raise ValueError("未知配音模式。")
        project = Path(source["project"])
        request = {"story_file":source["story_file"],"art_file":source["art_file"],"speech_mode":SPEECH_MODES[speech_mode]}
        request_dir = project/".cache/comfyui-handdraw-requests"
        request_dir.mkdir(parents=True,exist_ok=True)
        data = json.dumps(request,ensure_ascii=False,sort_keys=True)
        name = hashlib.sha256(data.encode()).hexdigest()[:20]
        request_path = request_dir/(name+".json")
        request_path.write_text(data)
        result = execute(project,[python_for(project),str(project/"scripts/handdraw_job.py"),"prepare",str(request_path)],name+"-prepare.log")
        return ({"project":str(project),"manifest":result["job"]},)


class HanddrawRender:
    CATEGORY = "视频制作/手绘故事"
    FUNCTION = "render"
    RETURN_TYPES = ("HANDDRAW_RENDER",)
    RETURN_NAMES = ("已导出视频",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{"job":("HANDDRAW_JOB",),"mode":(list(RENDER_MODES),),"resolution":(["720p","1080p"],)}}

    @classmethod
    def IS_CHANGED(cls,**kwargs):
        return float("nan")

    def render(self,job,mode,resolution):
        if mode not in RENDER_MODES or resolution not in ("720p","1080p"):
            raise ValueError("未知渲染模式或尺寸。")
        project = Path(job["project"])
        node = CONFIG.get("node_executable") or shutil.which("node") or ""
        if not Path(node).is_file():
            raise ValueError("找不到 Node.js，请重新安装此工作流以更新运行路径。")
        mode_key = RENDER_MODES[mode]
        log_name = Path(job["manifest"]).parent.name+f"-{mode_key}-{resolution}.log"
        result = execute(project,[node,str(project/"scripts/render-handdraw-job.mjs"),job["manifest"],mode_key,resolution],log_name)
        record = json.loads(Path(result["render"]).read_text())
        subfolder = "handdraw/"+Path(job["manifest"]).parent.name+f"/{mode_key}-{resolution}"
        destination = inside(Path(folder_paths.get_output_directory())/subfolder,folder_paths.get_output_directory())
        destination.mkdir(parents=True,exist_ok=True)
        for source,filename in [(Path(record["film"]),"film.mp4"),(Path(record["film"]).parent/"cover.png","cover.png"),(Path(job["manifest"]).parent/"captions.srt","captions.srt")]:
            target = destination/filename
            if target.exists() and sha(target)!=sha(source):
                raise ValueError("ComfyUI 输出中的文件被改动，已保留，请先移走："+str(target))
            if not target.exists():
                shutil.copy2(source,target)
        video = {"filename":"film.mp4","subfolder":subfolder,"type":"output"}
        message = f"{mode}已导出：{record['duration_seconds']:.2f} 秒，{resolution}\n{destination/'film.mp4'}\n字幕已保存；音色和画面仍需人工验收。"
        return {"ui":{"text":[message],"handdraw_video":[video]},"result":({"project":str(project),"record":result["render"],"output":str(destination)},)}


class HanddrawVerify:
    CATEGORY = "视频制作/手绘故事"
    FUNCTION = "verify"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("检查报告",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{"render":("HANDDRAW_RENDER",)}}

    @classmethod
    def IS_CHANGED(cls,**kwargs):
        return float("nan")

    def verify(self,render):
        project = Path(render["project"])
        result = execute(project,[python_for(project),str(project/"scripts/handdraw_job.py"),"verify",render["record"]],Path(render["record"]).parent.parent.name+"-verify.log")
        target = Path(render["output"])/"verification.json"
        shutil.copy2(result["report"],target)
        summary = (f"技术检查通过：{result['duration_seconds']:.2f} 秒，完整解码 {result['decoded_frames']} 帧。\n"
                   f"音频与源旁白相关性：{result['audio_source_correlation']:.5f}\n检查范围：输入版本、解码、时长、音轨、字幕文字和时码。\n"
                   "未代替人工试听或画面验收。\n"+str(target))
        return {"ui":{"text":[summary]},"result":(str(target),)}


NODE_CLASS_MAPPINGS = {"HanddrawLoadStory":HanddrawLoadStory,"HanddrawNarration":HanddrawNarration,"HanddrawRender":HanddrawRender,"HanddrawVerify":HanddrawVerify}
NODE_DISPLAY_NAME_MAPPINGS = {"HanddrawLoadStory":"手绘① 文案与分镜","HanddrawNarration":"手绘② 配音与字幕","HanddrawRender":"手绘③ 渲染视频","HanddrawVerify":"手绘④ 技术检查"}
WEB_DIRECTORY = "./web"
