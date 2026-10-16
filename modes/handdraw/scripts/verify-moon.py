"""Check the actual encoded film, narration identity and current story timeline."""
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "out/handdraw-moon-v1"
CONTENT = ROOT / "content/handdraw-moon-v1"
FILM = OUTPUT / "井里的月亮-手绘故事-v1.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
COMPOSITOR = ROOT / "node_modules/@remotion/compositor-darwin-arm64"


def run(command, **kwargs):
    return subprocess.run(command, check=True, capture_output=True, **kwargs)


def waveform(path):
    result = run([FFMPEG, "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", "24000", "-f", "s16le", "-"])
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768


def main():
    story = json.loads((CONTENT / "story.json").read_text())
    timeline = json.loads((CONTENT / "timeline.json").read_text())
    narration = json.loads((CONTENT / "narration-record.json").read_text())
    audio = ROOT / "public" / timeline["audio"]
    text = "".join(c for scene in story["scenes"] for c in scene["captions"])
    assert narration["text"] == text
    assert timeline["scriptSignature"] == narration["signature"]
    assert timeline["audioSha256"] == hashlib.sha256(audio.read_bytes()).hexdigest()
    assert [s["id"] for s in story["scenes"]] == [s["id"] for s in timeline["scenes"]]
    assert "".join(c["text"] for c in timeline["captions"]) == text
    previous = 0
    for cue in timeline["captions"]:
        assert previous <= cue["startFrame"] < cue["endFrame"] <= timeline["durationInFrames"]
        previous = cue["endFrame"]
    probe_env = {**os.environ, "DYLD_LIBRARY_PATH": str(COMPOSITOR)}
    probe = json.loads(run([str(COMPOSITOR / "ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(FILM)], env=probe_env, text=True).stdout)
    videos = [s for s in probe["streams"] if s["codec_type"] == "video"]
    audios = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    assert len(videos) == len(audios) == 1
    video = videos[0]
    assert (video["width"], video["height"], video["codec_name"], audios[0]["codec_name"]) == (story["width"], story["height"], "h264", "aac")
    assert video["r_frame_rate"] == f"{story['fps']}/1"
    assert abs(float(probe["format"]["duration"])-timeline["durationSeconds"]) < .1
    decoded = run([FFMPEG, "-v", "error", "-i", str(FILM), "-map", "0:v:0", "-map", "0:a:0", "-progress", "pipe:1", "-f", "null", "-"], text=True)
    frame_counts = re.findall(r"^frame=(\d+)$", decoded.stdout, re.M)
    assert frame_counts and int(frame_counts[-1]) == timeline["durationInFrames"]
    original, encoded = waveform(audio), waveform(FILM)
    expected_offset = round(timeline["audioLeadFrames"] / story["fps"] * 24000)
    assert len(encoded) >= expected_offset + len(original) - 1200, "Encoded narration was truncated"
    def compare(shift):
        offset = expected_offset+shift
        candidate = encoded[offset:offset+len(original):12]
        reference = original[::12][:len(candidate)]
        return float(np.dot(reference,candidate)/max(1e-9,np.linalg.norm(reference)*np.linalg.norm(candidate)))
    _, coarse_shift = max((compare(shift), shift) for shift in range(-600,601,12))
    correlation, shift = max((compare(shift), shift) for shift in range(coarse_shift-12,coarse_shift+13))
    assert correlation > .97, f"Encoded narration differs from the current source: {correlation}"
    peak = float(np.max(np.abs(encoded)))
    assert 0 < peak < .999, "Audio is empty or clipped"
    review_frames = []
    for index, scene in enumerate(timeline["scenes"]):
        review_frames.append((f"scene-{index+1}-complete", scene["from"] + math.floor(scene["durationInFrames"]*.94)))
    review_frames.extend([
        ("first-ink",round(timeline["scenes"][0]["durationInFrames"]*.28)),
        ("first-colour",round(timeline["scenes"][0]["durationInFrames"]*.72)),
        ("sky-moon-early",timeline["scenes"][5]["from"]+round(timeline["scenes"][5]["durationInFrames"]*.28)),
        ("last-frame",timeline["durationInFrames"]-1),
    ])
    review_dir = OUTPUT / "encoded-review"
    review_dir.mkdir(exist_ok=True)
    sheet = Image.new("RGB",(1920,4*384),"#e4dece")
    draw = ImageDraw.Draw(sheet)
    for index,(name,frame) in enumerate(review_frames):
        image_path = review_dir / f"{name}.png"
        run([FFMPEG,"-v","error","-y","-ss",f"{frame/story['fps']:.6f}","-i",str(FILM),"-frames:v","1","-vf","scale=640:-1",str(image_path)])
        sheet.paste(Image.open(image_path),(index%3*640,index//3*384+24))
        draw.text((index%3*640+12,index//3*384+5),f"{name} / {frame/story['fps']:.2f}s",fill="#514538")
    sheet.save(OUTPUT / "encoded-review-contact.jpg",quality=92)
    report = {
        "status":"technical_checks_passed_pending_user_review", "film":str(FILM), "durationSeconds":float(probe["format"]["duration"]),
        "width":video["width"],"height":video["height"],"fps":video["r_frame_rate"],"videoCodec":video["codec_name"],"audioCodec":audios[0]["codec_name"],
        "decodedFrames":int(frame_counts[-1]),"fileBytes":FILM.stat().st_size,"filmSha256":hashlib.sha256(FILM.read_bytes()).hexdigest(),
        "checks":{"fullDecode":True,"scriptAndAudioHashMatch":True,"eightScenesInCorrectOrder":True,"sixteenCaptionsMatchCurrentScript":True,"nonOverlappingCaptions":True,
                  "sourceNarrationPresentInEncodedFilm":True,"completeNarrationDuration":True,"audioNotClipped":True},
        "audioSourceCorrelation":correlation,"audioAlignmentAdjustmentMs":shift/24,"peakDbfs":20*math.log10(max(1e-9,peak)),
        "preparedEncodedReviewFrames":len(review_frames),"subjectiveVoiceListening":"not_performed", "continuousHumanPlayback":"not_performed",
        "production":{"artwork":"original vector illustrations", "animation":"actual SVG path tracing and local paint masks; pen tip follows current path", "tts":"edge-tts 7.3.1 / zh-CN-XiaoyiNeural", "renderer":"Remotion / Brave headless"},
        "limitations":["This is an independent hand-drawing story trial, not a replacement for the herbal-series character and voice template.","No full character locomotion or lip sync.","Voice timbre and word-by-word pronunciation await listening acceptance."]
    }
    (OUTPUT / "verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
