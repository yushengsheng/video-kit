"""Handdraw-only command adapter. Other modes need not import this module."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(args):subprocess.run([str(x) for x in args],cwd=ROOT,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['initialize','prepare','render','verify','check','install-comfy']);p.add_argument('--example',choices=['moon','goji','comic','inkred'],default='moon');p.add_argument('--offline',action='store_true');p.add_argument('--preview',action='store_true');p.add_argument('--comfy-directory',type=Path);p.add_argument('--update',action='store_true');a=p.parse_args()
    py=sys.executable
    if a.action=='initialize':run([py,'scripts/examples.py','initialize']);return
    if a.action=='check':
        run(['npm','run','typecheck']);run([py,'-m','unittest','discover','-s','tests','-v']);return
    if a.action=='prepare':
        run([py,'scripts/examples.py','prepare','--example',a.example,*(['--offline'] if a.offline else [])]);return
    if a.action=='install-comfy':
        if not a.comfy_directory:p.error('install-comfy 需要 --comfy-directory 指定 ComfyUI 根目录')
        run([py,'scripts/install_handdraw_comfy.py','--comfy-directory',a.comfy_directory,*(['--update'] if a.update else [])]);return
    from examples import EXAMPLES
    if a.example=='moon':
        job=Path(json.loads((ROOT/'.cache/kit-jobs/moon.json').read_text())['manifest'])
        kind='preview' if a.preview else 'full';resolution='720p' if a.preview else '1080p'
        if a.action=='render':run(['node','scripts/render-handdraw-job.mjs',job,kind,resolution])
        else:
            directory=ROOT/'out/comfyui-handdraw'/job.parent.name/f'{kind}-{resolution}'
            run([py,'scripts/handdraw_job.py','verify',directory/'render.json'])
    else:
        command=['node','scripts/'+EXAMPLES[a.example][2]] if a.action=='render' else [py,'scripts/'+EXAMPLES[a.example][3]]
        run([*command,*(['--preview'] if a.preview else [])])


if __name__=='__main__':main()
