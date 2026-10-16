"""Audit Git's staged/tracked paths; never read local ignored media or secrets."""
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BLOCKED={'.mp4','.mov','.mkv','.webm','.mp3','.wav','.flac','.png','.jpg','.jpeg','.ttf','.otf','.woff','.woff2','.safetensors','.ckpt','.pth'}


def main():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    count=size=0
    for name in filter(None,names):
        path=ROOT/name
        if path.suffix.lower() in BLOCKED:raise ValueError('媒体／大素材不入库：'+name)
        if any(part in {'.cache','.venv','node_modules','public','out','projects','assets-local','__pycache__'} for part in path.relative_to(ROOT).parts):raise ValueError('运行或个人目录不入库：'+name)
        if path.stat().st_size>1_000_000:raise ValueError('文件超过1MB，请先确认共享范围：'+name)
        data=path.read_text()
        if re.search(r'/(?:Users|home)/[A-Za-z0-9_.-]+/',data):raise ValueError('仍含作者本机路径：'+name)
        if re.search(r'gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',data):raise ValueError('疑似密钥：'+name)
        count+=1;size+=path.stat().st_size
    print(json.dumps({'tracked_text_files':count,'tracked_bytes':size,'media_assets':0,'author_absolute_paths':0,'recognizable_secret_patterns':0},ensure_ascii=False))


if __name__=='__main__':main()
