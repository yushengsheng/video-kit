"""Check or fast-forward this checkout; never reset/stash local work."""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REMOTE='https://github.com/yushengsheng/video-kit.git'


def git(*args, root=ROOT):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def update(apply=False, root=ROOT):
    if git('status','--porcelain','--untracked-files=normal',root=root):
        raise ValueError('存在未提交的代码改动，已停止；不会自动丢弃或暂存。')
    if git('branch','--show-current',root=root)!='main':
        raise ValueError('只在 main 分支执行更新；其他分支请自行合并。')
    if git('remote','get-url','origin',root=root)!=REMOTE:
        raise ValueError('origin 不是约定的 video-kit 仓库，已停止。')
    git('fetch','origin','main',root=root)
    counts=git('rev-list','--left-right','--count','HEAD...refs/remotes/origin/main',root=root).split()
    ahead,behind=map(int,counts)
    if ahead:
        raise ValueError('本地有尚未同步的提交，已停止；不会重置本地历史。')
    if apply and behind:
        git('merge','--ff-only','refs/remotes/origin/main',root=root)
        print('代码已快进更新。请查看变更，依赖变化时重新 setup 对应模式。')
    else:
        print(f'可更新 {behind} 个提交。'+('运行 --apply 执行快进更新。' if behind else '当前已是最新。'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    try:update(a.apply)
    except (ValueError,subprocess.CalledProcessError) as error:raise SystemExit(str(error))
