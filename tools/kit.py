"""Small mode-aware CLI. Media/runtime data stays local and ignored by Git."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import venv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(args,cwd):
    command=[str(x) for x in args]
    command[0]=shutil.which(command[0]) or command[0]
    subprocess.run(command,cwd=cwd,check=True)


def mode_path(name):
    registry=json.loads((ROOT/'modes.json').read_text(encoding='utf-8'))
    if name not in registry:raise ValueError(f'未实现的模式：{name}；可用模式：'+', '.join(registry))
    path=(ROOT/registry[name]['directory']).resolve()
    if not path.is_relative_to(ROOT/'modes'):raise ValueError('模式目录越界')
    return path


def python_for(mode):
    path=mode/configuration(mode)['python_environment']/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not path.is_file():raise ValueError('先运行 setup 建立此模式的独立环境。')
    return path


def download_assets(mode):
    for item in json.loads((mode/'assets.json').read_text(encoding='utf-8')):
        target=(mode/'public'/item['destination']).resolve()
        if not target.is_relative_to(mode/'public'):raise ValueError('素材目录越界')
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError(f'现有素材被修改，已保留，请先移走再下载：{target}')
            continue
        temporary=target.with_suffix(target.suffix+'.download')
        try:
            with urllib.request.urlopen(item['url'],timeout=60) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response,output)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('素材校验失败：'+item['name'])
            temporary.replace(target)
        finally:temporary.unlink(missing_ok=True)
    for item in json.loads((mode/'licenses.json').read_text(encoding='utf-8')):
        destination=mode/'public'/item['destination'];destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'licenses'/item['source'],destination)



def setup(mode):
    if sys.version_info<(3,10):raise ValueError('需要 Python 3.10 或更新版本。')
    if not shutil.which('node') or not shutil.which('npm'):raise ValueError('请先安装 Node.js 22+（含 npm）。')
    major=int(subprocess.check_output(['node','--version'],text=True).lstrip('v').split('.')[0])
    if major<22:raise ValueError('需要 Node.js 22 或更新版本。')
    environment=mode/configuration(mode)['python_environment']
    if not environment.exists():venv.EnvBuilder(with_pip=True).create(environment)
    run([python_for(mode),'-m','pip','install','-r',configuration(mode)['requirements']],mode)
    run(['npm','ci','--no-audit','--no-fund'],mode)
    download_assets(mode)
    run([python_for(mode),cli_for(mode),'initialize'],mode)
    print('环境与基础素材已准备。新旁白仍需运行 prepare（联网）。')


def configuration(mode):
    return next(value for value in json.loads((ROOT/'modes.json').read_text(encoding='utf-8')).values() if (ROOT/value['directory']).resolve()==mode)


def cli_for(mode):
    path=(mode/configuration(mode)['cli']).resolve()
    if not path.is_relative_to(mode) or not path.is_file():raise ValueError('模式入口无效')
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['list','setup','prepare','render','verify','check','install-comfy','voice']);p.add_argument('mode',nargs='?',default='handdraw');a,remaining=p.parse_known_args()
    if a.action=='list':print((ROOT/'modes.json').read_text(encoding='utf-8'));return
    mode=mode_path(a.mode)
    if a.action=='setup':
        if remaining:p.error('setup 不接受额外参数')
        setup(mode);return
    run([python_for(mode),cli_for(mode),a.action,*remaining],mode)


if __name__=='__main__':
    try:main()
    except (ValueError,subprocess.CalledProcessError,FileNotFoundError) as error:raise SystemExit(str(error))
