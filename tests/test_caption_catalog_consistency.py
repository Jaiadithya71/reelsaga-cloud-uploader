import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CaptionCatalogConsistency(unittest.TestCase):
    def test_recipe_catalog_and_held_candidate_agree(self):
        recipe = json.loads((ROOT/'soldier-caption-repair-recipe.json').read_text())
        catalog = json.loads((ROOT/'soldier-prepared-catalog.json').read_text())
        gates = json.loads((ROOT/'soldier-subtitle-quality-gates.json').read_text())
        for fix in recipe['fixes']:
            episode, part = map(int, fix['part'].replace('ep','').replace('part','').split('-'))
            item = next(x for x in catalog['items'] if x['episode']==episode and x['part']==part)
            candidate = gates['parts'][item['id']]['candidate']
            with self.subTest(part=fix['part']):
                self.assertEqual(item['sha256'], fix['new_sha256'])
                self.assertEqual(item['bytes'], fix['bytes'])
                self.assertEqual(candidate['new_sha256'], fix['new_sha256'])
                self.assertEqual(candidate['timing'], fix['timing'])
                self.assertEqual(candidate.get('patches'), fix.get('patches'))
                self.assertEqual(candidate['source_sha256'], gates['parts'][item['id']]['original_render_sha256'])
