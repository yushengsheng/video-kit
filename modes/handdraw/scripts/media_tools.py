"""Locate ffprobe from PATH or the installed Remotion platform package."""
import os
import platform
import shutil
from pathlib import Path


def probe_command():
    executable = os.environ.get('FFPROBE_EXECUTABLE') or shutil.which('ffprobe')
    if executable:
        return str(executable), os.environ.copy()
    system = {'Windows':'win32', 'Darwin':'darwin', 'Linux':'linux'}.get(platform.system())
    arch = 'arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x64'
    suffix = '-msvc' if system == 'win32' else ('-musl' if platform.libc_ver()[0] == 'musl' else '-gnu') if system == 'linux' else ''
    directory = Path(__file__).resolve().parents[1]/'node_modules/@remotion'/f'compositor-{system}-{arch}{suffix}'
    executable = directory/('ffprobe.exe' if system == 'win32' else 'ffprobe')
    if not executable.is_file():
        raise FileNotFoundError('找不到 ffprobe；请安装 FFmpeg 或设置 FFPROBE_EXECUTABLE。')
    env = os.environ.copy()
    if system == 'darwin':
        env['DYLD_LIBRARY_PATH'] = str(directory)
    return str(executable), env
