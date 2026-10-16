import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import voice_profiles as voices


class VoiceProfiles(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.audio=self.root/'source.wav';self.audio.write_bytes(b'reference fixture')
        self.text='参考台词。'
        self.preset={'id':'test-v1','label':'测试','reference_sha256':voices.sha(self.audio),
                     'reference_text_sha256':hashlib.sha256(self.text.encode()).hexdigest()}
        self.root_patch=patch.object(voices,'ROOT',self.root);self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_alias_resolves_to_same_version(self):
        self.assertEqual(voices.find_preset('玄骨')['id'],'xuangu-v1')
        self.assertEqual(voices.find_preset('xiaocha-reference-v1'),voices.find_preset('玄骨'))
        with self.assertRaises(ValueError):voices.find_preset('未定义音色')

    def test_reference_tamper_rejected_before_copy(self):
        self.audio.write_bytes(b'changed')
        with self.assertRaises(ValueError):voices.import_profile(self.preset,self.audio,self.text)
        self.assertFalse(voices.profile_directory(self.preset).exists())

    def test_wrong_transcript_rejected(self):
        with self.assertRaises(ValueError):voices.import_profile(self.preset,self.audio,'另一个人的话')

    def test_import_is_repeatable_but_never_replaces_edited_reference(self):
        directory=voices.import_profile(self.preset,self.audio,self.text)
        self.assertEqual(voices.import_profile(self.preset,self.audio,self.text),directory)
        (directory/'reference.wav').write_bytes(b'modified locally')
        with self.assertRaises(ValueError):voices.import_profile(self.preset,self.audio,self.text)
        self.assertEqual((directory/'reference.wav').read_bytes(),b'modified locally')

    def test_runtime_configuration_preserves_default_and_other_keys(self):
        path=self.root/'projects/config.local.json';path.parent.mkdir()
        voices.write_json(path,{'other':{'keep':True},'handdraw':{'default_voice':{'name':'personal'}}})
        python=self.root/'runtime/python';python.parent.mkdir();python.touch()
        model=self.root/'models/tts';aligner=self.root/'models/aligner'
        for directory in (model,aligner):
            directory.mkdir(parents=True);(directory/'config.json').write_text('{}')
        voices.configure_runtime(python,model,aligner)
        result=voices.read_json(path)
        self.assertEqual(result['handdraw']['default_voice'],{'name':'personal'})
        self.assertTrue(result['other']['keep'])
        self.assertEqual(result['handdraw']['voice_runtime']['python'],'runtime/python')
        self.assertEqual(voices.runtime()['python'],str(python))

    def test_generation_failure_leaves_no_output_and_cleans_staging(self):
        voices.import_profile(self.preset,self.audio,self.text)
        output=self.root/'projects/failed-job'
        with patch.object(voices,'runtime',return_value={'python':'test'}), patch.object(
                voices.subprocess,'run',side_effect=subprocess.TimeoutExpired('test',1)):
            with self.assertRaises(subprocess.TimeoutExpired):voices.synthesize(self.preset,'新文案',output)
        self.assertFalse(output.exists())
        self.assertFalse(list(output.parent.glob('.voice-generate-*')))

    def test_existing_output_and_outside_path_refused_before_generation(self):
        voices.import_profile(self.preset,self.audio,self.text)
        output=self.root/'projects/existing';output.mkdir();(output/'keep').write_text('old')
        with patch.object(voices,'runtime',return_value={'python':'test'}), patch.object(voices.subprocess,'run') as run:
            with self.assertRaises(FileExistsError):voices.synthesize(self.preset,'新文案',output)
            with self.assertRaises(ValueError):voices.synthesize(self.preset,'新文案',self.root/'tracked-output')
            run.assert_not_called()
        self.assertEqual((output/'keep').read_text(),'old')

    def test_publish_never_overwrites_an_existing_directory(self):
        source=self.root/'stage';source.mkdir();(source/'new').touch()
        target=self.root/'old';target.mkdir();(target/'keep').write_text('old')
        with self.assertRaises(FileExistsError):voices.publish_directory(source,target)
        self.assertEqual((target/'keep').read_text(),'old')


if __name__=='__main__':
    unittest.main()
