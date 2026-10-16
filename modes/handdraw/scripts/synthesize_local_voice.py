"""Optional Qwen worker, launched only by the configured isolated voice Python."""
import gc
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'


def main():
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    job=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    output=Path(job['output']); preset=job['preset']; text=job['text']
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if sha(job['reference_audio'])!=preset['reference_sha256']:
        raise ValueError('参考录音在启动后发生变化，停止生成。')
    ffmpeg=os.environ.get('FFMPEG_EXECUTABLE') or shutil.which('ffmpeg')
    if not ffmpeg:
        raise FileNotFoundError('本地声音运行环境需要FFmpeg或FFMPEG_EXECUTABLE。')
    torch.set_num_threads(8); torch.manual_seed(preset['seed'])
    device='cuda:0' if torch.cuda.is_available() else 'cpu'
    dtype=torch.bfloat16 if device.startswith('cuda') else torch.float32
    print('载入本地模型，调用音色：'+preset['label'],flush=True)
    model=Qwen3TTSModel.from_pretrained(job['runtime']['model_dir'],device_map=device,
        dtype=dtype,attn_implementation='sdpa',local_files_only=True)
    prompt=model.create_voice_clone_prompt(ref_audio=job['reference_audio'],
        ref_text=job['reference_text'],x_vector_only_mode=False)
    with torch.inference_mode():
        wavs,sr=model.generate_voice_clone(text=text,language=preset['language'],
            voice_clone_prompt=prompt,non_streaming_mode=True,max_new_tokens=2048,
            temperature=preset['temperature'],top_p=preset['top_p'])
    raw=np.asarray(wavs[0],dtype=np.float32)
    if not np.isfinite(raw).all() or not .3<len(raw)/sr<180 or np.max(np.abs(raw))>=1:
        raise ValueError('生成声音无效、过长或存在削波，未发布。')
    sf.write(output/'synthesis.wav',raw,sr,subtype='PCM_16')
    del model,prompt,wavs,raw
    gc.collect()
    if device.startswith('cuda'):torch.cuda.empty_cache()
    subprocess.run([ffmpeg,'-v','error','-i',str(output/'synthesis.wav'),'-af',
        'atempo='+str(preset['delivery_tempo']),'-ar','24000','-ac','1',
        str(output/'narration.wav')],check=True,timeout=45)
    subprocess.run([ffmpeg,'-v','error','-i',str(output/'narration.wav'),'-c:a',
        'libmp3lame','-q:a','2',str(output/'narration.mp3')],check=True,timeout=45)
    subprocess.run([ffmpeg,'-v','error','-i',str(output/'narration.mp3'),'-f','null','-'],
        check=True,capture_output=True,timeout=45)
    wave,sr=sf.read(output/'narration.wav',dtype='float32')
    duration=len(wave)/sr; peak=float(np.max(np.abs(wave)))
    if not np.isfinite(wave).all() or not 0<peak<.999:
        raise ValueError('交付音频存在无效采样或削波，未发布。')

    print('按实际旁白对齐字幕时码……',flush=True)
    from qwen_asr import Qwen3ForcedAligner
    aligner=Qwen3ForcedAligner.from_pretrained(job['runtime']['aligner_dir'],
        device_map=device,dtype=dtype,attn_implementation='sdpa',local_files_only=True)
    aligned=aligner.align(audio=str(output/'narration.wav'),text=text,language=preset['language'])[0]
    boundaries=[{'text':x.text,'start':x.start_time,'end':x.end_time} for x in aligned]
    normalized=lambda value:re.sub(r'[^\w\u4e00-\u9fff]','',value)
    if normalized(''.join(x['text'] for x in boundaries))!=normalized(text):
        raise ValueError('时码未覆盖原文，未发布。')
    if not all(0<=x['start']<=x['end']<=duration+.1 for x in boundaries):
        raise ValueError('时码越界，未发布。')
    if any(a['start']>b['start'] for a,b in zip(boundaries,boundaries[1:])):
        raise ValueError('时码顺序异常，未发布。')
    voice={k:preset[k] for k in ('provider','model','model_revision','reference_sha256',
        'language','seed','temperature','top_p','delivery_tempo')}
    voice.update({'name':preset['id'],'label':preset['label'],'rate':'preset',
                  'pitch':'+0Hz','reference_text':job['reference_text']})
    signature=hashlib.sha256(json.dumps({'text':text,'voice':voice},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    record={'signature':signature,'voice':voice,'text':text,'boundaries':boundaries,
        'audio_sha256':sha(output/'narration.mp3'),'duration_seconds':duration,'peak':peak,
        'alignment':'Qwen3-ForcedAligner-0.6B; final delivery waveform',
        'subjectiveListening':'not performed; technical success is not subjective approval',
        'disclosure':preset['disclosure']}
    (output/'narration-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'narration.txt').write_text(text+'\n',encoding='utf-8')
    if job['story'] is not None:
        story=job['story'];story['voice']=voice
        (output/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'voice':preset['label'],'seconds':duration,'peak':peak,'aligned_characters':len(boundaries)},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
