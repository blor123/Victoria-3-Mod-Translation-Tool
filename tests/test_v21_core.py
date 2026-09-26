import json
import tempfile
import unittest
from pathlib import Path

from app.ai.batch_manager import BatchManager
from app.ai.conflict_ai_service import ConflictAIService
from app.ai.localization_parser import parse_file
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.token_protector import TokenProtector
from app.ai.translation_service import AITranslationService
from app.conflicts import ConflictAnalyzer,ConflictMod,ConflictReportManager
from app.conflicts.paradox_parser import parse_definitions
from app.i18n.language_definition import LANGUAGES


class FakeProvider:
    model="fake-model"
    def __init__(self):self.translation_requests=[];self.conflict_requests=[];self.cancelled=False
    def translate_batch(self,entries,target):
        self.translation_requests.append((entries,target));return [{"id":e["id"],"text":"번역 "+e["text"]} for e in entries]
    def analyze_conflict(self,payload):
        self.conflict_requests.append(payload);return {"summary":"summary","interaction_type":"overwrite","overwrite_risk":"possible","important_differences":[],"possible_effects":[],"compatibility_patch_needed":"possible","uncertainties":["other files unknown"],"recommended_checks":["test in game"]}
    def cancel(self):self.cancelled=True
    def reset_cancel(self):self.cancelled=False


class V21CoreTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def _mod(self,name,building,loc,shared="same"):
        root=self.root/name;(root/'common/buildings').mkdir(parents=True);(root/'localization/english').mkdir(parents=True)
        (root/'common/buildings/shared.txt').write_text(shared,encoding='utf-8');(root/'common/buildings'/f'{name}.txt').write_text(f'# comment\nquoted = "{{ ignored }}"\n{building} = {{ nested = {{ value = 1 }} }}\n',encoding='utf-8')
        (root/'localization/english'/f'{name}_english.yml').write_text(f'\ufeffl_english:\n bank_name:0 "{loc}"\n',encoding='utf-8');(root/'descriptor.mod').write_text('replace_path="common/buildings"\n',encoding='utf-8');return root

    def test_token_protection_and_batch_limits(self):
        protector=TokenProtector();protected,mapping=protector.protect('Gain $MONEY$ [Concept(\'concept\')] @gold! £money£ #bold')
        self.assertNotIn('$MONEY$',protected);self.assertEqual(protector.restore(protected,mapping),'Gain $MONEY$ [Concept(\'concept\')] @gold! £money£ #bold')
        self.assertEqual([len(x) for x in BatchManager(2,1000).split([{'id':str(i),'text':'x'} for i in range(5)])],[2,2,1])

    def test_localization_translation_rebuilds_without_changing_key(self):
        source=self.root/'localization/english/test_english.yml';source.parent.mkdir(parents=True);source.write_text('\ufeffl_english:\n key_one:0 "Gain $MONEY$"\n',encoding='utf-8')
        provider=FakeProvider();service=AITranslationService(provider,batch_size=2,max_retries=0);output=self.root/'out';session=service.translate([source.parent],LANGUAGES['ko-KR'],output)
        result=(output/'localization/korean/test_korean.yml').read_text(encoding='utf-8-sig');self.assertIn('l_korean:',result);self.assertIn('key_one:0',result);self.assertIn('$MONEY$',result);self.assertEqual(session.succeeded,1)
        destination=self.root/'installed';target=destination/'localization/korean/test_korean.yml';target.parent.mkdir(parents=True);target.write_text('old',encoding='utf-8');backup=self.root/'backup';count=service.apply_preview(output,destination,backup);self.assertEqual(count,1);self.assertEqual((backup/'localization/korean/test_korean.yml').read_text(encoding='utf-8'),'old');self.assertIn('key_one:0',target.read_text(encoding='utf-8-sig'))

    def test_paradox_parser_nested_comments_and_warning(self):
        definitions,warnings=parse_definitions('a = { x = { y = 1 } }\n# b = {}\nc = "{"\nd = { z=2')
        self.assertEqual([x.name for x in definitions],['a']);self.assertTrue(warnings)

    def test_local_conflicts_evidence_report_and_parser_isolation(self):
        a=self._mod('A','building_bank','Bank','same');b=self._mod('B','building_bank','Different Bank','same')
        report=ConflictAnalyzer().analyze([ConflictMod.from_folder(a),ConflictMod.from_folder(b)]);categories={c.category for c in report.conflicts}
        self.assertTrue({'file','definition','localization','replace_path'}.issubset(categories));definition=next(c for c in report.conflicts if c.category=='definition');self.assertEqual(definition.subject,'building_bank');self.assertTrue(definition.snippet_a)
        path=self.root/'report.json';ConflictReportManager().save(report,path);loaded=ConflictReportManager().load(path);self.assertEqual(len(loaded.conflicts),len(report.conflicts));self.assertNotIn('api_key',path.read_text(encoding='utf-8').casefold())

    def test_ai_conflict_sends_only_snippets_and_caches(self):
        a=self._mod('A','building_bank','Bank');b=self._mod('B','building_bank','Different');conflict=next(c for c in ConflictAnalyzer().analyze([ConflictMod.from_folder(a),ConflictMod.from_folder(b)]).conflicts if c.category=='definition')
        provider=FakeProvider();service=ConflictAIService(provider,self.root/'cache.json');first=service.analyze(conflict);second=service.analyze(conflict)
        self.assertEqual(first,second);self.assertEqual(len(provider.conflict_requests),1);payload=provider.conflict_requests[0];self.assertNotIn('root_path',payload);self.assertLess(len(json.dumps(payload)),30000)

    def test_config_and_reports_never_receive_api_key(self):
        from app.config.config_manager import DEFAULT_CONFIG
        self.assertFalse(any('key' in name.casefold() and 'api' in name.casefold() for name in DEFAULT_CONFIG))

    def test_gemini_interactions_payload_and_response(self):
        class RecordingProvider(GeminiProvider):
            def __init__(self):
                super().__init__('not-a-real-key')
                self.request = None
            def _request(self, path, payload=None):
                self.request = (path, payload)
                return {
                    'steps': [{
                        'type': 'model_output',
                        'content': [{'type': 'text', 'text': '{"ok": true}'}],
                    }],
                }

        provider = RecordingProvider()
        self.assertTrue(provider.test_connection())
        path, payload = provider.request
        self.assertEqual(path, 'interactions')
        self.assertEqual(payload['model'], 'gemini-3.8-flash')
        self.assertFalse(payload['store'])
        self.assertEqual(payload['response_format']['mime_type'], 'application/json')
        self.assertIn('schema', payload['response_format'])


if __name__=='__main__':unittest.main()
