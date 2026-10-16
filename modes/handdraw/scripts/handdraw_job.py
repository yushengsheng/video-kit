"""Prepare immutable ComfyUI jobs and verify the video produced by Remotion."""
import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from create_moon_voice import create_narration

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
JOBS = PUBLIC / "comfyui-handdraw"
ENGINE_FILES = ["src/handdraw-moon/Video.tsx", "src/handdraw-moon/comfy.tsx", "scripts/render-handdraw-job.mjs", "scripts/create_moon_voice.py", "scripts/handdraw_job.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contained(path, parent):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError(f"路径必须位于 {parent}")
    return path


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2))


def validate(story, art):
    if (story["width"], story["height"], story["fps"]) != (1920,1080,30):
        raise ValueError("当前手绘画布固定为 1920×1080、30fps；720p 在渲染节点选择缩放。")
    ids = [scene["id"] for scene in story["scenes"]]
    if not ids or len(set(ids)) != len(ids) or ids != [scene["id"] for scene in art]:
        raise ValueError("文案与画面的场景编号必须相同、顺序一致且不重复。")
    for scene in story["scenes"]:
        if not scene["captions"] or any(not isinstance(text,str) or not text.strip() for text in scene["captions"]):
            raise ValueError("每个场景需要非空的口播句子。")
    for scene in art:
        if not scene["shapes"]:
            raise ValueError("每个场景需要实际画面路径，不能只有说明文字。")
        for shape in scene["shapes"]:
            if not shape["d"] or len(shape["bounds"]) != 4 or not all(np.isfinite(shape["bounds"])):
                raise ValueError("插画路径或范围无效。")


def prepare(request_path):
    request = read_json(request_path)
    story_path = contained(ROOT / request["story_file"],ROOT)
    art_path = contained(ROOT / request["art_file"],ROOT)
    story, art = read_json(story_path), read_json(art_path)
    validate(story, art)
    if request["speech_mode"] not in ("cached", "generate_missing"):
        raise ValueError("未知配音模式")
    source_assets = PUBLIC / "handdraw-moon-v1"
    files = [story_path,art_path,*[ROOT / name for name in ENGINE_FILES],source_assets/"paper.jpg",source_assets/"drawing-hand.png",PUBLIC/"fonts/NotoSerifSC-Regular.ttf"]
    fingerprint = hashlib.sha256("".join(digest(path) for path in files).encode()).hexdigest()
    job = JOBS / fingerprint[:20]
    job.mkdir(parents=True,exist_ok=True)
    manifest_path = job / "job.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        for name, expected in manifest["input_hashes"].items():
            if digest(contained(job / name,job)) != expected:
                raise ValueError("已保存的任务素材发生改变。请重新准备任务，不覆盖旧成片。")
        print(json.dumps({"job":str(manifest_path),"reused":True},ensure_ascii=False))
        return manifest_path
    write_json(job/"story.json",story)
    write_json(job/"art.json",art)
    for name in ["paper.jpg","drawing-hand.png","drawing-hand-LICENSE.txt"]:
        shutil.copy2(source_assets/name,job/name)
    shutil.copy2(PUBLIC/"fonts/NotoSerifSC-Regular.ttf",job/"font.woff2")
    (job/"audio").mkdir(exist_ok=True)
    source_timeline = story_path.parent/"timeline.json"
    source_record = story_path.parent/"narration-record.json"
    if source_timeline.is_file() and source_record.is_file():
        cached = read_json(source_timeline)
        source_audio = contained(PUBLIC / cached["audio"],PUBLIC)
        if source_audio.is_file() and digest(source_audio) == cached["audioSha256"]:
            shutil.copy2(source_audio,job/"audio/narration.mp3")
            shutil.copy2(source_record,job/"narration-record.json")
    relative = job.relative_to(PUBLIC).as_posix()
    timeline = asyncio.run(create_narration(story,job,job,relative+"/audio/narration.mp3",job/"captions.srt",request["speech_mode"]=="generate_missing"))
    inputs = ["story.json","art.json","timeline.json","narration-record.json","audio/narration.mp3","paper.jpg","drawing-hand.png","font.woff2"]
    manifest = {"version":1,"fingerprint":fingerprint,"job_directory":str(job),"duration_seconds":timeline["durationSeconds"],
                "assets":{"paper":relative+"/paper.jpg","hand":relative+"/drawing-hand.png","font":relative+"/font.woff2"},
                "input_hashes":{name:digest(job/name) for name in inputs},"source_story":str(story_path),"source_art":str(art_path),
                "visual_and_voice_acceptance":"not_assumed","engine_files":{name:digest(ROOT/name) for name in ENGINE_FILES}}
    write_json(manifest_path,manifest)
    print(json.dumps({"job":str(manifest_path),"reused":False},ensure_ascii=False))
    return manifest_path


def verify(render_path):
    render_path = contained(render_path,ROOT/"out/comfyui-handdraw")
    render = read_json(render_path)
    manifest_path = contained(render["job"],JOBS)
    manifest = read_json(manifest_path)
    job = manifest_path.parent
    for name, expected in manifest["input_hashes"].items():
        if digest(contained(job/name,job)) != expected:
            raise ValueError("素材在渲染后发生改变，拒绝使用旧检查结果。")
    film = contained(render["film"],render_path.parent)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    compositor = ROOT/"node_modules/@remotion/compositor-darwin-arm64"
    probe = subprocess.run([str(compositor/"ffprobe"),"-v","error","-show_streams","-show_format","-of","json",str(film)],check=True,capture_output=True,text=True,
                           env={**os.environ,"DYLD_LIBRARY_PATH":str(compositor)})
    info = json.loads(probe.stdout)
    video = [s for s in info["streams"] if s["codec_type"]=="video"]
    audio = [s for s in info["streams"] if s["codec_type"]=="audio"]
    if len(video)!=1 or len(audio)!=1 or video[0]["codec_name"]!="h264" or audio[0]["codec_name"]!="aac":
        raise ValueError("输出必须包含一条 H.264 视频和一条 AAC 音轨。")
    if [video[0]["width"],video[0]["height"]] != render["dimensions"] or video[0]["r_frame_rate"]!="30/1":
        raise ValueError("输出尺寸或帧率不符。")
    decoded = subprocess.run([ffmpeg,"-v","error","-i",str(film),"-progress","pipe:1","-f","null","-"],check=True,capture_output=True,text=True)
    frames = int(re.findall(r"^frame=(\d+)$",decoded.stdout,re.M)[-1])
    if frames != render["frames"] or abs(float(info["format"]["duration"])-frames/30)>.1:
        raise ValueError("视频时长或解码帧数不符。")
    def waveform(path):
        decoded_audio = subprocess.run([ffmpeg,"-v","error","-i",str(path),"-map","0:a:0","-ar","24000","-ac","1","-f","s16le","-"],check=True,capture_output=True)
        return np.frombuffer(decoded_audio.stdout,dtype="<i2").astype(np.float32)/32768
    timeline = read_json(job/"timeline.json")
    source, encoded = waveform(job/"audio/narration.mp3"), waveform(film)
    offset = round(timeline["audioLeadFrames"]/30*24000)
    if render["mode"]=="full" and len(encoded) < offset+len(source)-1200:
        raise ValueError("旁白被截断。")
    source = source[:min(len(source),len(encoded)-offset-1200)]
    def correlation(shift):
        candidate = encoded[offset+shift:offset+shift+len(source):12]
        reference = source[::12][:len(candidate)]
        return float(np.dot(candidate,reference)/max(1e-9,np.linalg.norm(candidate)*np.linalg.norm(reference)))
    _, coarse = max((correlation(shift),shift) for shift in range(-600,601,12))
    match, shift = max((correlation(shift),shift) for shift in range(coarse-12,coarse+13))
    peak = float(np.max(np.abs(encoded)))
    if match < .97 or not 0 < peak < .999:
        raise ValueError(f"音频与源旁白不符或存在削波，相关性 {match:.4f}。")
    text = "".join(c for s in read_json(job/"story.json")["scenes"] for c in s["captions"])
    if text != "".join(c["text"] for c in timeline["captions"]):
        raise ValueError("字幕与文案不一致。")
    previous = 0
    for caption in timeline["captions"]:
        if not previous <= caption["startFrame"] < caption["endFrame"] <= timeline["durationInFrames"]:
            raise ValueError("字幕时间重叠或越界。")
        previous = caption["endFrame"]
    report = {"status":"technical_checks_passed","mode":render["mode"],"film":str(film),"duration_seconds":float(info["format"]["duration"]),
              "dimensions":render["dimensions"],"fps":30,"decoded_frames":frames,"film_sha256":digest(film),
              "audio_source_correlation":match,"audio_alignment_adjustment_ms":shift/24,"audio_peak":peak,
              "checks":["input hashes","full decode","H.264/AAC","duration","audio identity","caption text and times"],
              "subjective_listening":"not_performed","visual_acceptance":"not_assumed"}
    report_path = render_path.parent/"verification.json"
    write_json(report_path,report)
    print(json.dumps({"report":str(report_path),**report},ensure_ascii=False))
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","verify"])
    parser.add_argument("path",type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.path)
    else:
        verify(args.path)
