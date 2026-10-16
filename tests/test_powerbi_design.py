"""Design contracts: adaptive choice, binding preservation and layout safety."""
from copy import deepcopy
import csv
from pathlib import Path
import tempfile
import unittest

import yaml
from scripts.powerbi_design import prepare, audit
from scripts.generate_powerbi import generate, BIError
from test_powerbi import ROOT, RUN


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.plan=yaml.safe_load((ROOT/'examples/sql_pipeline_demo/powerbi_design_plan.yaml').read_text())
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def test_design_does_not_change_original_or_data_bindings(self):
        before=deepcopy(self.plan)
        after,palette=prepare(self.plan)
        self.assertEqual(self.plan,before)
        original=[(v.get('table'),v.get('column'),v.get('measure')) for v in before['pages'][0]['visuals']]
        final=[(v.get('table'),v.get('column'),v.get('measure')) for v in after['pages'][0]['visuals'] if v['type']!='text']
        self.assertEqual(original,final)
        audit(after['pages'][0])

    def test_layout_variants_differ_and_have_no_overlaps(self):
        results=[]
        for layout in ['overview','comparison']:
            self.plan['pages'][0]['layout']=layout
            after,_=prepare(self.plan);audit(after['pages'][0])
            results.append(after['pages'][0]['visuals'][3]['position'])
        self.assertNotEqual(results[0],results[1])

    def test_detail_layout_gives_table_more_space(self):
        self.plan['pages'][0]['layout']='detail'
        self.plan['pages'][0]['visuals']=[v for v in self.plan['pages'][0]['visuals'] if v['type'] not in {'column','line'}]
        after,_=prepare(self.plan);audit(after['pages'][0])
        table=next(v for v in after['pages'][0]['visuals'] if v['type']=='table')
        self.assertGreater(table['position'][3],500)

    def test_auto_adapts_to_actual_long_categories(self):
        self.plan['pages'][0]['layout']='auto'
        file=self.root/'source.csv';file.write_text('类别\n这是一个超过十二个字符的实际类别名称\n',encoding='utf-8')
        after,_=prepare(self.plan,{'清洗明细':{'csv_path':file,'columns':[{'name':'类别','type':'text'}]}})
        self.assertIn('bar',[v['type'] for v in after['pages'][0]['visuals']])
        self.assertEqual(after['design_profile']['清洗明细']['rows'],1)

    def test_overlapping_manual_elements_are_rejected(self):
        self.plan['pages'][0]['layout']='manual'
        self.plan['pages'][0]['visuals'][0]['position']=[32,64,300,100]
        with self.assertRaisesRegex(ValueError,'重叠'):prepare(self.plan)

    def test_too_dense_pages_are_rejected(self):
        self.plan['pages'][0]['visuals']+=deepcopy(self.plan['pages'][0]['visuals'])
        with self.assertRaises(ValueError):prepare(self.plan)

    def test_unsupported_theme_fails_before_output(self):
        self.plan['design']['palette']='unknown'
        p=self.root/'plan.yaml';p.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        with self.assertRaises(BIError):generate(RUN,p,self.root/'output')
        self.assertFalse((self.root/'output').exists())

    def test_project_has_theme_native_text_and_no_launcher(self):
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';manifest=generate(RUN,path,out,'D:/Example/data')
        self.assertFalse(manifest['desktop_validated'])
        self.assertFalse(list(out.rglob('*.cmd')))
        self.assertFalse(list(out.rglob('*.ps1')))
        import json
        report=json.loads(next(out.rglob('report.json')).read_text())
        self.assertIn('customTheme',report['themeCollection'])
        visuals=[json.loads(p.read_text()) for p in out.rglob('visual.json')]
        self.assertEqual(sum(v['visual']['visualType']=='textbox' for v in visuals),7)
        self.assertIn('D:/Example/data',next(out.rglob('expressions.tmdl')).read_text())
        self.assertEqual(manifest['fields'],4)


if __name__=='__main__':unittest.main()
