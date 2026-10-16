import asyncio
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from create_moon_voice import create_narration
from handdraw_job import contained,validate
from install_handdraw_comfy import install


class Boundaries(unittest.TestCase):
    def test_scene_order_must_match(self):
        story=json.loads((ROOT/'content/handdraw-moon-v1/story.json').read_text(encoding='utf-8'))
        art=json.loads((ROOT/'content/handdraw-moon-v1/art.json').read_text(encoding='utf-8'))
        validate(story,art)
        with self.assertRaises(ValueError):validate(story,list(reversed(art)))

    def test_project_path_escape(self):
        with self.assertRaises(ValueError):contained(ROOT/'../outside.json',ROOT)

    def test_changed_copy_never_reuses_stale_voice_offline(self):
        story=json.loads((ROOT/'content/handdraw-moon-v1/story.json').read_text(encoding='utf-8'))
        story['scenes'][0]['captions'][0]='新稿，不能沿用旧音频。'
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp);(path/'audio').mkdir()
            (path/'audio/narration.mp3').write_bytes(b'not current speech')
            (path/'narration-record.json').write_text(json.dumps({'signature':'old'}), encoding='utf-8')
            with patch('create_moon_voice.edge_tts.Communicate',side_effect=AssertionError('must not call online service')):
                with self.assertRaises(ValueError):asyncio.run(create_narration(story,path,path,'unused.mp3',path/'captions.srt',False))

    def test_comfy_install_preserves_unmanaged_node(self):
        with tempfile.TemporaryDirectory() as temp:
            comfy=Path(temp);(comfy/'main.py').touch();node=comfy/'custom_nodes/handdraw_video';node.mkdir(parents=True)
            original=node/'my-code.py';original.write_text('keep', encoding='utf-8')
            with self.assertRaises(FileExistsError):install(comfy,True)
            self.assertEqual(original.read_text(encoding='utf-8'),'keep')

    def test_comfy_managed_update_refuses_modified_node(self):
        with tempfile.TemporaryDirectory() as temp:
            comfy=Path(temp);(comfy/'main.py').touch();(comfy/'custom_nodes').mkdir()
            # Avoid touching the real module's local workflow output during this test.
            import install_handdraw_comfy as module
            root=comfy/'module';(root/'comfyui').mkdir(parents=True)
            with patch.object(module,'ROOT',root):
                install(comfy)
                init=comfy/'custom_nodes/handdraw_video/__init__.py';init.write_text(init.read_text(encoding='utf-8')+'\n# local edit', encoding='utf-8')
                with self.assertRaises(ValueError):install(comfy,True)
                self.assertTrue(init.read_text(encoding='utf-8').endswith('# local edit'))


if __name__=='__main__':unittest.main()
