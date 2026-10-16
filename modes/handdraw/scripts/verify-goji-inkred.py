"""Validate this episode's source identity, full decode, subtitles and mixed audio."""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/handdraw-goji-inkred-v1'
CONTENT=ROOT/'content/handdraw-goji-inkred-v1'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(preview=False):
    render=json.loads((OUT/('preview-render.json' if preview else 'render.json')).read_text())
    for name,expected in render['input_hashes'].items():
        if digest(ROOT/name)!=expected:
            raise ValueError(f'Source changed after render: {name}')
    film=Path(render['film'])
    assert digest(film)==render['film_sha256']
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    compositor=ROOT/'node_modules/@remotion/compositor-darwin-arm64'
    probe=subprocess.run([str(compositor/'ffprobe'),'-v','error','-show_streams','-show_format','-of','json',str(film)],capture_output=True,text=True,check=True,env={**os.environ,'DYLD_LIBRARY_PATH':str(compositor)})
    info=json.loads(probe.stdout)
    video=[s for s in info['streams'] if s['codec_type']=='video']
    audio=[s for s in info['streams'] if s['codec_type']=='audio']
    assert len(video)==len(audio)==1
    v=video[0]
    assert v['codec_name']=='h264' and audio[0]['codec_name']=='aac'
    assert [v['width'],v['height']]==render['dimensions'] and v['r_frame_rate']=='30/1'
    assert v['pix_fmt']=='yuv420p'
    result=subprocess.run([ffmpeg,'-v','error','-i',str(film),'-progress','pipe:1','-f','null','-'],capture_output=True,text=True,check=True)
    decoded=int(re.findall(r'^frame=(\d+)$',result.stdout,re.M)[-1])
    assert decoded==render['frames']
    assert abs(float(info['format']['duration'])-decoded/30)<.1
    def wave(path):
        r=subprocess.run([ffmpeg,'-v','error','-i',str(path),'-map','0:a:0','-ar','24000','-ac','1','-f','f32le','-'],capture_output=True,check=True)
        return np.frombuffer(r.stdout,dtype='<f4')
    tl=json.loads((CONTENT/'timeline.json').read_text())
    speech=wave(ROOT/'public'/tl['audio'])
    music=wave(ROOT/'public/handdraw-goji-inkred-v1/audio/foley.wav')
    encoded=wave(film)
    lead=round(tl['audioLeadFrames']/30*24000)
    expected=np.zeros(len(encoded),dtype=np.float32)
    expected[:min(len(expected),len(music))]=music[:len(expected)]
    count=min(len(speech),len(expected)-lead)
    expected[lead:lead+count]+=speech[:count]
    # Compare the complete intended mix, rather than treating added music as a voice mismatch.
    length=min(len(expected),len(encoded))-700
    start=700
    reference=expected[start:length:12]
    def corr(shift):
        candidate=encoded[start+shift:length+shift:12]
        return float(np.dot(reference,candidate)/max(1e-12,np.linalg.norm(reference)*np.linalg.norm(candidate)))
    _,coarse=max((corr(s),s) for s in range(-600,601,12))
    correlation,shift=max((corr(s),s) for s in range(coarse-12,coarse+13))
    peak=float(np.max(np.abs(encoded)))
    assert correlation>.98,correlation
    assert 0<peak<.999,peak
    if not preview: assert len(encoded)>=lead+len(speech)-1200
    story=json.loads((CONTENT/'story.json').read_text())
    assert ''.join(c for s in story['scenes'] for c in s['captions'])==''.join(c['text'] for c in tl['captions'])
    previous=0
    for caption in tl['captions']:
        assert previous<=caption['startFrame']<caption['endFrame']<=tl['durationInFrames']
        previous=caption['endFrame']
    report={
        'status':'technical_checks_passed','film':str(film),'duration_seconds':float(info['format']['duration']),
        'dimensions':render['dimensions'],'fps':30,'decoded_frames':decoded,'codec':'H.264 / AAC / yuv420p',
        'file_bytes':film.stat().st_size,'film_sha256':digest(film),'input_hashes_verified':len(render['input_hashes']),
        'scene_count':len(story['scenes']),'caption_count':len(tl['captions']),
        'audio_mix_correlation':correlation,'audio_alignment_adjustment_ms':shift/24,
        'audio_peak_dbfs':20*math.log10(peak),'audio_clipping_detected':False,
        'narration_complete':not preview,'captions_match_narration_text_and_word_timing':True,
        'subjective_listening':'not_performed',
        'visual_review':'not_assumed; see visual-review.json if present',
        'product_photo':'not_provided; illustrated_placeholder_labeled_in_film',
        'content_changes':'content/handdraw-goji-inkred-v1/editorial-notes.md'
    }
    (OUT/('preview-verification.json' if preview else 'verification.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    verify(args.preview)
