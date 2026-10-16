import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from install_handdraw_comfy import install
from media_tools import probe_command


def comfy_module():
    mocks = {'folder_paths':types.ModuleType('folder_paths'), 'comfy':types.ModuleType('comfy'), 'comfy.model_management':types.ModuleType('comfy.model_management')}
    mocks['comfy.model_management'].throw_exception_if_processing_interrupted = lambda: None
    with patch.dict(sys.modules, mocks):
        spec = importlib.util.spec_from_file_location('handdraw_platform_test', ROOT/'comfyui/handdraw_video/__init__.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class Platform(unittest.TestCase):
    def test_explicit_ffprobe_path(self):
        with patch.dict(os.environ, {'FFPROBE_EXECUTABLE':'custom-ffprobe'}):
            self.assertEqual(probe_command()[0], 'custom-ffprobe')

    def test_windows_bundled_ffprobe(self):
        with patch.dict(os.environ, {}, clear=True), patch('media_tools.shutil.which', return_value=None), patch('media_tools.platform.system', return_value='Windows'), patch('media_tools.platform.machine', return_value='AMD64'), patch.object(Path, 'is_file', return_value=True):
            executable, _ = probe_command()
            self.assertTrue(executable.endswith('ffprobe.exe'))
            self.assertIn('compositor-win32-x64-msvc', executable)

    def test_comfy_custom_user_directory_and_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            comfy = base/'comfy'
            comfy.mkdir()
            (comfy/'main.py').touch()
            (comfy/'custom_nodes').mkdir()
            import install_handdraw_comfy as module
            with patch.object(module, 'ROOT', base/'module'):
                install(comfy, user_directory=base/'user')
            workflow = next((base/'user/default/workflows/手绘故事').glob('*.json'))
            graph = json.loads(workflow.read_text(encoding='utf-8'))
            self.assertEqual(graph['nodes'][0]['type'], 'HanddrawLoadStory')

    def test_comfy_python_matches_platform(self):
        module = comfy_module()
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            suffix = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
            executable = project/'.cache/moon-tools-venv'/suffix
            executable.parent.mkdir(parents=True)
            executable.touch()
            self.assertEqual(module.python_for(project), str(executable))

    def test_windows_stop_kills_tree_with_bounded_wait(self):
        module=comfy_module();process=Mock(pid=1234)
        with patch.object(module.subprocess,'run') as run:
            module.stop_windows_process(process)
        run.assert_called_once_with(['taskkill','/PID','1234','/T','/F'],capture_output=True,timeout=10)
        process.wait.assert_called_once_with(timeout=5)
        process.kill.assert_not_called()

    def test_windows_stop_falls_back_when_taskkill_times_out(self):
        module=comfy_module();process=Mock(pid=1234)
        with patch.object(module.subprocess,'run',side_effect=subprocess.TimeoutExpired('taskkill',10)):
            module.stop_windows_process(process)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_windows_stop_falls_back_when_process_does_not_exit(self):
        module=comfy_module();process=Mock(pid=1234)
        process.wait.side_effect=[subprocess.TimeoutExpired('process',5),0]
        with patch.object(module.subprocess,'run'):
            module.stop_windows_process(process)
        process.kill.assert_called_once_with()
        self.assertEqual([call.kwargs for call in process.wait.call_args_list],[{'timeout':5},{'timeout':5}])


if __name__ == '__main__':
    unittest.main()
