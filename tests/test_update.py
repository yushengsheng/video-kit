import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('updater',ROOT/'tools/update.py');updater=importlib.util.module_from_spec(spec);spec.loader.exec_module(updater)


def command(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()


class SafeUpdate(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();base=Path(self.temp.name)
        self.remote=base/'remote.git';subprocess.run(['git','init','--bare',str(self.remote)],check=True,capture_output=True)
        self.author=base/'author';self.author.mkdir();command(self.author,'init','-b','main');command(self.author,'config','user.name','test');command(self.author,'config','user.email','test@example.invalid')
        (self.author/'code.txt').write_text('v1');(self.author/'.gitignore').write_text('projects/\nout/\n');command(self.author,'add','.');command(self.author,'commit','-m','first');command(self.author,'remote','add','origin',str(self.remote));command(self.author,'push','-u','origin','main')
        self.copy=base/'copy';subprocess.run(['git','clone','-b','main',str(self.remote),str(self.copy)],check=True,capture_output=True)
        self.patch=patch.object(updater,'REMOTE',str(self.remote));self.patch.start()

    def tearDown(self):self.patch.stop();self.temp.cleanup()

    def test_fast_forward_preserves_ignored_work(self):
        local=self.copy/'projects/story.txt';local.parent.mkdir();local.write_text('private work')
        (self.author/'code.txt').write_text('v2');command(self.author,'add','.');command(self.author,'commit','-m','second');command(self.author,'push')
        updater.update(True,self.copy)
        self.assertEqual((self.copy/'code.txt').read_text(),'v2');self.assertEqual(local.read_text(),'private work')

    def test_dirty_code_stops_without_reset(self):
        (self.copy/'code.txt').write_text('local edits')
        with self.assertRaises(ValueError):updater.update(True,self.copy)
        self.assertEqual((self.copy/'code.txt').read_text(),'local edits')

    def test_untracked_source_stops_update(self):
        (self.copy/'new-code.py').write_text('keep')
        with self.assertRaises(ValueError):updater.update(True,self.copy)


if __name__=='__main__':unittest.main()
