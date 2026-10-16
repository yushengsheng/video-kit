"""Named local voice references. Registry travels with Git; recordings stay local."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODE = Path(__file__).resolve().parents[1]
ROOT = MODE.parents[1]
REGISTRY = MODE / 'voices/presets.json'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def presets():
    return read_json(REGISTRY)['presets']


def find_preset(name):
    matches=[p for p in presets() if name.casefold() in
             [n.casefold() for n in (p['id'],p['label'],*p.get('aliases',[]))]]
    if len(matches)!=1:
        raise ValueError('找不到唯一音色：'+name+'；先运行 voice handdraw list。')
    return matches[0]


def profile_directory(preset):
    return ROOT/'projects/voices'/preset['id']


def validate_reference(preset, audio, text):
    if not Path(audio).is_file() or Path(audio).stat().st_size > 10_000_000:
        raise ValueError('参考音频缺失或超过10MB。')
    if sha(audio)!=preset['reference_sha256']:
        raise ValueError('参考音频与此版本预设的SHA-256不符；不会替换或降级音色。')
    if hashlib.sha256(text.strip().encode('utf-8')).hexdigest()!=preset['reference_text_sha256']:
        raise ValueError('参考台词与此版本预设不符。')


def load_profile(preset):
    directory=profile_directory(preset)
    path=directory/'profile.json'
    if not path.is_file():
        raise ValueError('「'+preset['label']+'」未导入本地参考资料；请按 voices/README.md 导入。')
    profile=read_json(path)
    if profile.get('id')!=preset['id']:
        raise ValueError('本地音色ID与预设不符。')
    audio=directory/'reference.wav'
    validate_reference(preset,audio,profile['reference_text'])
    return profile,audio


def publish_directory(staging, destination):
    destination=Path(destination)
    if destination.exists():
        raise FileExistsError('保留已有文件，请另选新目录：'+str(destination))
    # The staging directory is a sibling on the same filesystem.
    Path(staging).rename(destination)


def import_profile(preset, audio, text):
    validate_reference(preset,audio,text)
    destination=profile_directory(preset)
    if destination.exists():
        load_profile(preset)
        return destination
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.voice-import-',dir=destination.parent) as temporary:
        staging=Path(temporary)/'profile';staging.mkdir()
        shutil.copy2(audio,staging/'reference.wav')
        (staging/'reference.txt').write_text(text.strip()+'\n',encoding='utf-8')
        write_json(staging/'profile.json',{
            'schema_version':1,'id':preset['id'],'label':preset['label'],
            'reference_text':text.strip(),'reference_sha256':preset['reference_sha256'],
            'source':'user-supplied reference excerpt',
            'reuse_note':'用户要求以玄骨为名，供后续明确指定时复用；无量化相似度评分。'})
        publish_directory(staging,destination)
    return destination


def local_path(value):
    path=Path(value).expanduser()
    return (ROOT/path).resolve() if not path.is_absolute() else path.resolve()


def portable_path(path):
    path=local_path(path)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def configure_runtime(python, model, aligner):
    python,model,aligner=map(local_path,(python,model,aligner))
    if not python.is_file() or not all((p/'config.json').is_file() for p in (model,aligner)):
        raise ValueError('本地Python或模型目录无效；本命令不下载模型或安装依赖。')
    config_path=ROOT/'projects/config.local.json'
    config=read_json(config_path) if config_path.exists() else {}
    config.setdefault('handdraw',{})['voice_runtime']={
        'python':portable_path(python),'model_dir':portable_path(model),'aligner_dir':portable_path(aligner)}
    config_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=config_path.parent,delete=False,suffix='.tmp') as file:
        temporary=Path(file.name)
        json.dump(config,file,ensure_ascii=False,indent=2)
    try:
        os.replace(temporary,config_path)
    finally:
        temporary.unlink(missing_ok=True)


def runtime():
    path=ROOT/'projects/config.local.json'
    value=read_json(path).get('handdraw',{}).get('voice_runtime',{}) if path.exists() else {}
    if not all(k in value for k in ('python','model_dir','aligner_dir')):
        raise ValueError('未配置本地声音运行环境；先运行 voice handdraw configure。')
    result={k:str(local_path(value[k])) for k in ('python','model_dir','aligner_dir')}
    if not Path(result['python']).is_file() or not all((Path(result[k])/'config.json').is_file() for k in ('model_dir','aligner_dir')):
        raise ValueError('配置的本地声音运行环境已移动或缺失，请重新configure；不会静默改用其他声音。')
    return result


def synthesize(preset, text, output, story=None, timeout=900):
    profile,audio=load_profile(preset)
    environment=runtime()
    text=text.strip()
    if not text or len(text)>600:
        raise ValueError('连续旁白应为1—600个字符，较长稿件请拆分后由助手排镜。')
    output=local_path(output)
    if not output.is_relative_to(ROOT/'projects') or output==ROOT/'projects':
        raise ValueError('配音输出必须放在本仓库忽略的projects目录内。')
    if output.exists():
        raise FileExistsError('保留已有配音，请另建输出目录：'+str(output))
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.voice-generate-',dir=output.parent) as temporary:
        staging=Path(temporary)/'output';staging.mkdir()
        job=Path(temporary)/'job.json'
        write_json(job,{'preset':preset,'reference_audio':str(audio),'reference_text':profile['reference_text'],
                        'runtime':environment,'text':text,'story':story,'output':str(staging)})
        subprocess.run([environment['python'],'-X','utf8',str(MODE/'scripts/synthesize_local_voice.py'),str(job)],
                       check=True,timeout=timeout)
        record=read_json(staging/'narration-record.json')
        if record['text']!=text or record['audio_sha256']!=sha(staging/'narration.mp3'):
            raise ValueError('生成结果身份不匹配，不发布未完成配音。')
        publish_directory(staging,output)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    commands.add_parser('list')
    info=commands.add_parser('info');info.add_argument('name')
    imp=commands.add_parser('import');imp.add_argument('name');imp.add_argument('--audio',type=Path,required=True);imp.add_argument('--text-file',type=Path,required=True)
    configure=commands.add_parser('configure')
    configure.add_argument('--python',required=True);configure.add_argument('--model-dir',required=True);configure.add_argument('--aligner-dir',required=True)
    generate=commands.add_parser('synthesize');generate.add_argument('name')
    source=generate.add_mutually_exclusive_group(required=True)
    source.add_argument('--text-file',type=Path);source.add_argument('--story',type=Path)
    generate.add_argument('--output-dir',required=True);generate.add_argument('--timeout',type=int,default=900,choices=range(60,1801),metavar='60..1800')
    args=parser.parse_args()
    if args.action=='configure':
        configure_runtime(args.python,args.model_dir,args.aligner_dir)
        print('本地声音环境已配置；原默认音色保留。');return
    if args.action=='list':
        rows=[]
        for preset in presets():
            try:
                load_profile(preset);runtime();status='ready'
            except (ValueError,FileNotFoundError,KeyError) as error:
                status=str(error)
            rows.append({'id':preset['id'],'label':preset['label'],'aliases':preset['aliases'],'status':status})
        print(json.dumps(rows,ensure_ascii=False,indent=2));return
    preset=find_preset(args.name)
    if args.action=='info':
        profile,audio=load_profile(preset)
        print(json.dumps({'preset':preset,'local_profile':profile,'audio':str(audio),'runtime':runtime()},ensure_ascii=False,indent=2));return
    if args.action=='import':
        output=import_profile(preset,local_path(args.audio),local_path(args.text_file).read_text(encoding='utf-8-sig'))
    else:
        story=read_json(local_path(args.story)) if args.story else None
        text=''.join(c for s in story['scenes'] for c in s['captions']) if story else local_path(args.text_file).read_text(encoding='utf-8-sig')
        output=synthesize(preset,text,args.output_dir,story,args.timeout)
    print(json.dumps({'label':preset['label'],'output':str(output)},ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
