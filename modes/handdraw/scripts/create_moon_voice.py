"""Create one continuous narration and bind every caption to returned word timings."""
import asyncio
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content/handdraw-moon-v1"
ASSETS = ROOT / "public/handdraw-moon-v1"


def normalized(text):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", text)


async def create_narration(story, content=CONTENT, assets=ASSETS,
                           audio_relative="handdraw-moon-v1/audio/narration.mp3",
                           srt_path=ROOT / "out/handdraw-moon-v1/井里的月亮-v1.srt", allow_generate=True):
    content, assets, srt_path = Path(content), Path(assets), Path(srt_path)
    content.mkdir(parents=True, exist_ok=True)
    (assets / "audio").mkdir(parents=True, exist_ok=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    narration = "".join(caption for scene in story["scenes"] for caption in scene["captions"])
    (content / "narration.txt").write_text(narration + "\n", encoding='utf-8')
    voice = story["voice"]
    signature = hashlib.sha256(json.dumps({"text": narration, "voice": voice}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    audio = assets / "audio/narration.mp3"
    record_path = content / "narration-record.json"
    if audio.is_file() and record_path.is_file() and json.loads(record_path.read_text(encoding='utf-8')).get("signature") == signature:
        boundaries = json.loads(record_path.read_text(encoding='utf-8'))["boundaries"]
    else:
        if not allow_generate:
            raise ValueError("当前文案或音色没有匹配的配音缓存。请切换为“缺失时生成配音（联网）”，或准备正确的音频与时码。")
        boundaries = []
        temporary = audio.with_suffix(".part.mp3")
        communicate = edge_tts.Communicate(narration, voice["name"], rate=voice["rate"], pitch=voice["pitch"], boundary="WordBoundary")
        with temporary.open("wb") as stream:
            async for event in communicate.stream():
                if event["type"] == "audio":
                    stream.write(event["data"])
                elif event["type"] == "WordBoundary":
                    boundaries.append({"text": event["text"], "start": event["offset"] / 10_000_000, "end": (event["offset"] + event["duration"]) / 10_000_000})
        if not boundaries or temporary.stat().st_size < 1000:
            raise RuntimeError("Speech service returned incomplete data")
        temporary.replace(audio)
        record_path.write_text(json.dumps({"signature": signature, "voice": voice, "text": narration, "boundaries": boundaries, "subjectiveListening": "not_verified"}, ensure_ascii=False, indent=2), encoding='utf-8')
    if normalized("".join(item["text"] for item in boundaries)) != normalized(narration):
        raise RuntimeError("Returned speech timing text does not match this script")
    character_times = []
    for item in boundaries:
        count = len(normalized(item["text"]))
        for index in range(count):
            character_times.append((item["start"] + (item["end"] - item["start"]) * index / count,
                                    item["start"] + (item["end"] - item["start"]) * (index + 1) / count))
    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(audio)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError("Cannot measure narration duration")
    hours, minutes, seconds = map(float, match.groups())
    duration = hours * 3600 + minutes * 60 + seconds
    fps, lead = story["fps"], 0.65
    captions, scenes, cursor = [], [], 0
    for scene in story["scenes"]:
        scene_captions = []
        for text in scene["captions"]:
            count = len(normalized(text))
            start, end = character_times[cursor][0] + lead, character_times[cursor + count - 1][1] + lead
            caption = {"text": text, "startFrame": max(0, math.floor(start * fps) - 1), "endFrame": math.ceil(end * fps) + 3}
            captions.append(caption)
            scene_captions.append(caption)
            cursor += count
        scenes.append({"id": scene["id"], "from": scene_captions[0]["startFrame"], "captions": scene_captions})
    scenes[0]["from"] = 0
    for previous, following in zip(captions, captions[1:]):
        previous["endFrame"] = min(previous["endFrame"], following["startFrame"])
    total = math.ceil((lead + duration + 1.25) * fps)
    for index, scene in enumerate(scenes):
        scene["durationInFrames"] = (scenes[index + 1]["from"] if index + 1 < len(scenes) else total) - scene["from"]
    timeline = {"id": story["id"], "fps": fps, "audio": audio_relative, "audioLeadFrames": round(lead * fps), "audioDurationSeconds": duration,
                "durationInFrames": total, "durationSeconds": total / fps, "scenes": scenes, "captions": captions, "scriptSignature": signature,
                "audioSha256": hashlib.sha256(audio.read_bytes()).hexdigest()}
    (content / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding='utf-8')
    def srt_time(frame):
        milliseconds = round(frame * 1000 / fps)
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    srt = "\n\n".join(f"{i+1}\n{srt_time(c['startFrame'])} --> {srt_time(c['endFrame'])}\n{c['text']}" for i, c in enumerate(captions)) + "\n"
    srt_path.write_text(srt, encoding='utf-8')
    print(json.dumps({"durationSeconds": total / fps, "scenes": [{"id": s["id"], "seconds": s["durationInFrames"] / fps} for s in scenes], "voice": voice["name"]}, ensure_ascii=False, indent=2))
    return timeline


async def main():
    await create_narration(json.loads((CONTENT / "story.json").read_text(encoding='utf-8')))


if __name__ == "__main__":
    asyncio.run(main())
