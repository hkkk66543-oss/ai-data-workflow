"""PBIP generation contract tests; no Desktop rendering is simulated."""
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml
from scripts.generate_powerbi import BIError, generate, validate_value
from powerbi_fixture import create_run

ROOT = Path(__file__).resolve().parents[1]


class PowerBITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / 'run'
        create_run(self.run)
        self.plan = yaml.safe_load((ROOT / 'examples/sql_pipeline_demo/powerbi_plan.yaml').read_text())
        self.plan_path = self.root / 'plan.yaml'
        self.output = self.root / '中文 sample'

    def build(self):
        self.plan_path.write_text(yaml.safe_dump(self.plan, allow_unicode=True))
        return generate(self.run, self.plan_path, self.output)

    def change_csv(self, content):
        p = self.run / 'tables/清洗明细.csv'
        p.write_text(content, encoding='utf-8-sig')
        manifest_path = self.run / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest:
            if entry['path'] == 'tables/清洗明细.csv':
                entry['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))

    def test_complete_project_preserves_source_and_identifiers(self):
        original = (self.run / 'tables/清洗明细.csv').read_bytes()
        result = self.build()
        self.assertEqual((result['fields'], result['measures'], result['visuals']), (4, 2, 6))
        self.assertFalse(result['desktop_validated'])
        self.assertEqual((self.output / 'data/清洗明细.csv').read_bytes(), original)
        with (self.output / 'data/清洗明细.csv').open(encoding='utf-8-sig') as f:
            self.assertEqual(next(csv.DictReader(f))['记录编号'], '001')
        tmdl = next(self.output.rglob('table_001.tmdl')).read_text()
        self.assertIn('sourceColumn: "记录编号"', tmdl)
        self.assertIn("SUM('清洗明细'[数值])", tmdl)
        self.assertFalse(any(p.name in {'.pbi', '.platform', 'cache.abf'} for p in self.output.rglob('*')))
        self.assertEqual((self.run / 'tables/清洗明细.csv').read_bytes(), original)

    def test_reject_failed_run(self):
        p = self.run / 'run.json'
        r = json.loads(p.read_text()); r['status'] = 'failed'; p.write_text(json.dumps(r))
        with self.assertRaises(BIError): self.build()
        self.assertFalse(self.output.exists())

    def test_reject_tampered_csv(self):
        with (self.run / 'tables/清洗明细.csv').open('a') as f: f.write('tampered')
        with self.assertRaises(BIError): self.build()

    def test_reject_unfinished_cleanup(self):
        p = self.run / 'run.json'
        r = json.loads(p.read_text()); r['runtime']['cleanup'] = 'failed'; p.write_text(json.dumps(r))
        with self.assertRaises(BIError): self.build()

    def test_reject_unknown_field_and_remove_partial_output(self):
        self.plan['pages'][0]['visuals'][2]['column'] = '不存在'
        with self.assertRaises(BIError): self.build()
        self.assertFalse(self.output.exists())

    def test_reject_output_overwrite(self):
        self.output.mkdir(); (self.output / 'keep.txt').write_text('keep')
        with self.assertRaises(BIError): self.build()
        self.assertEqual((self.output / 'keep.txt').read_text(), 'keep')

    def test_reject_out_of_bounds(self):
        self.plan['pages'][0]['visuals'][0]['position'] = [1900,0,500,100]
        with self.assertRaises(BIError): self.build()

    def test_reject_sum_of_identifier(self):
        self.plan['measures'][1]['column'] = '记录编号'
        with self.assertRaises(BIError): self.build()

    def test_reject_export_traversal(self):
        self.plan['tables'][0]['export'] = '../other'
        with self.assertRaises(BIError): self.build()

    def test_numeric_ranges(self):
        for value, kind in [('922337203685477.5808','decimal'), ('0.00001','decimal'), ('9223372036854775808','int64'), ('nan','double'), ('1.1','int64')]:
            with self.subTest(value=value), self.assertRaises(BIError): validate_value(value, kind)
        validate_value('-922337203685477.5808', 'decimal')
        validate_value('9223372036854775807', 'int64')

    def test_relationship_duplicate_one_side_is_rejected(self):
        self.plan['tables'].append({**copy.deepcopy(self.plan['tables'][0]), 'name': '维度'})
        self.plan['relationships'] = [{'from': {'table':'清洗明细','column':'类别'}, 'to': {'table':'维度','column':'类别'}}]
        with self.assertRaisesRegex(BIError, '唯一'): self.build()

    def test_display_unit_scales_numeric_measure_and_retains_source(self):
        self.plan['measures'][1]['display_unit']='万'
        original=(self.run/'tables/清洗明细.csv').read_bytes()
        self.build()
        tmdl=next(self.output.rglob('table_001.tmdl')).read_text()
        self.assertIn("DIVIDE(SUM('清洗明细'[数值]), 10000)",tmdl)
        self.assertIn('formatString: #,0.00" 万"',tmdl)
        self.assertNotIn('FORMAT(',tmdl)
        self.assertEqual((self.output/'data/清洗明细.csv').read_bytes(),original)

    def test_unit_scaling_rejects_percent_or_unknown_unit(self):
        for unit,fmt in [('万','0.00%'),('百万','#,0.00'),(['万'],'#,0.00')]:
            with self.subTest(unit=unit,fmt=fmt):
                self.plan['measures'][1].update(display_unit=unit,format=fmt)
                with self.assertRaisesRegex(BIError,'display_unit'):self.build()
                self.assertFalse(self.output.exists())

    @unittest.skipUnless(os.environ.get('POWERSHELL_BIN'), 'Portable PowerShell optional')
    def test_launcher_prepares_unicode_path_and_is_idempotent(self):
        self.build()
        for _ in range(2):
            subprocess.run([os.environ['POWERSHELL_BIN'], '-NoProfile', '-File', str(self.output / 'PrepareAndOpen.ps1'), '-PrepareOnly'], check=True, capture_output=True)
        expression = next(self.output.rglob('expressions.tmdl')).read_text()
        self.assertIn(str(self.output / 'data').replace('\\','/'), expression)
        self.assertNotIn('__SET_DATA_ROOT__', expression)


if __name__ == '__main__': unittest.main()
