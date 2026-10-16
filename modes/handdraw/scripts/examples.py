"""Seed editable local examples, build vector paths, and prepare continuous speech."""
import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXAMPLES={
 'moon':('handdraw-moon-v1','create_moon_art.py','render-moon.mjs','verify-moon.py'),
 'goji':('handdraw-goji-v1','create_goji_art.py','render-goji.mjs','verify-goji.py'),
 'comic':('handdraw-goji-comic-v1','create_goji_comic_art.py','render-goji-comic.mjs','verify-goji-comic.py'),
 'inkred':('handdraw-goji-inkred-v1','create_goji_inkred_art.py','render-goji-inkred.mjs','verify-goji-inkred.py')
}


def initialize():
    for folder,*_ in EXAMPLES.values():
        content=ROOT/'content'/folder;content.mkdir(parents=True,exist_ok=True)
        (ROOT/'public'/folder/'audio').mkdir(parents=True,exist_ok=True)
        for name in ['story.json','asset-sources.json','editorial-notes.md']:
            source=ROOT/'examples'/folder/name
            if source.is_file() and not (content/name).exists():shutil.copy2(source,content/name)
        if not (content/'timeline.json').exists():
            shutil.copy2(ROOT/'examples'/folder/'timeline-reference.json',content/'timeline.json')
    # Reference timelines support static preview/type-check only; they are not usable speech caches.


def draw(name):
    script=EXAMPLES[name][1]
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)


def prepare(name,offline=False):
    initialize()
    folder=EXAMPLES[name][0];content=ROOT/'content'/folder
    from create_moon_voice import create_narration
    story=json.loads((content/'story.json').read_text(encoding='utf-8'))
    asyncio.run(create_narration(story,content,ROOT/'public'/folder,folder+'/audio/narration.mp3',ROOT/'out'/folder/'captions.srt',not offline))
    draw(name)
    if name=='moon':
        from handdraw_job import prepare as prepare_job
        request=ROOT/'.cache/kit-jobs/moon-request.json';request.parent.mkdir(parents=True,exist_ok=True)
        request.write_text(json.dumps({'story_file':'content/'+folder+'/story.json','art_file':'content/'+folder+'/art.json','speech_mode':'cached'}), encoding='utf-8')
        manifest=prepare_job(request)
        (request.parent/'moon.json').write_text(json.dumps({'manifest':str(manifest)}), encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['initialize','prepare']);p.add_argument('--example',choices=list(EXAMPLES),default='moon');p.add_argument('--offline',action='store_true');a=p.parse_args()
    if a.action=='initialize':
        initialize()
        for name in EXAMPLES:draw(name)
    else:prepare(a.example,a.offline)
