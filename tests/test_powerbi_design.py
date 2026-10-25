"""Design contracts: adaptive choice, binding preservation and layout safety."""
from copy import deepcopy
import csv
from pathlib import Path
import tempfile
import unittest

import yaml
from scripts.powerbi_design import prepare, audit
from scripts.generate_powerbi import generate, BIError
from test_powerbi import ROOT
from powerbi_fixture import create_run


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.plan=yaml.safe_load((ROOT/'examples/sql_pipeline_demo/powerbi_design_plan.yaml').read_text())
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.run=create_run(self.root/'run')

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
        with self.assertRaises(BIError):generate(self.run,p,self.root/'output')
        self.assertFalse((self.root/'output').exists())

    def test_project_has_theme_native_text_and_no_launcher(self):
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';manifest=generate(self.run,path,out,'D:/Example/data')
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

    def test_display_regressions_have_native_properties_and_room(self):
        import json
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';generate(self.run,path,out)
        visuals=[json.loads(p.read_text()) for p in out.rglob('visual.json')]
        by_type={v['visual']['visualType']:v for v in visuals}
        slicer=by_type['slicer']['visual']
        self.assertEqual(slicer['objects']['data'][0]['properties']['mode']['expr']['Literal']['Value'], "'Dropdown'")
        self.assertEqual(slicer['objects']['header'][0]['properties']['show']['expr']['Literal']['Value'],'false')
        line=by_type['lineChart']['visual']
        self.assertEqual(line['objects']['categoryAxis'][0]['properties']['axisType']['expr']['Literal']['Value'], "'Categorical'")
        table=by_type['tableEx']
        self.assertGreaterEqual(table['position']['height'],288)
        self.assertEqual(table['visual']['objects']['values'][0]['properties']['fontSize']['expr']['Literal']['Value'],'14D')
        self.assertEqual(line['visualContainerObjects']['subTitle'][0]['properties']['show']['expr']['Literal']['Value'],'false')

    def test_timestamp_column_does_not_lose_time_axis(self):
        import json
        self.plan['tables'][0]['column_types']={'记录日期':'datetime'}
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';generate(self.run,path,out)
        line=next(json.loads(p.read_text())['visual'] for p in out.rglob('visual.json') if json.loads(p.read_text())['visual']['visualType']=='lineChart')
        self.assertNotIn('axisType',line['objects']['categoryAxis'][0]['properties'])

    def test_new_layouts_keep_controls_and_sections_separate(self):
        for layout in ['overview','comparison']:
            self.plan['pages'][0]['layout']=layout
            after,_=prepare(self.plan);page=after['pages'][0];audit(page)
            table=next(v for v in page['visuals'] if v['type']=='table')
            self.assertGreaterEqual(table['position'][3],288)
            for chart in (v for v in page['visuals'] if v['type'] in {'line','bar','column'}):
                self.assertGreaterEqual(chart['position'][3],240)

    def test_semantic_colors_are_materialized_and_overrides_do_not_leak(self):
        import json
        self.plan['design']['colors']={'canvas':'#E8EEF6'}
        self.plan['pages'][0]['visuals'][0]['role']='negative'
        self.plan['pages'][0]['visuals'][1]['fill']='#FFF3DF'
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';generate(self.run,path,out)
        cards=[json.loads(p.read_text())['visual'] for p in out.rglob('visual.json') if json.loads(p.read_text())['visual']['visualType']=='card']
        fills={v['visualContainerObjects']['background'][0]['properties']['color']['solid']['color']['expr']['Literal']['Value'] for v in cards}
        self.assertEqual(fills,{"'#FBECE9'","'#FFF3DF'"})
        negative=next(v for v in cards if v['visualContainerObjects']['background'][0]['properties']['color']['solid']['color']['expr']['Literal']['Value']=="'#FBECE9'")
        self.assertEqual(negative['objects']['labels'][0]['properties']['color']['solid']['color']['expr']['Literal']['Value'],"'#C34C42'")
        baseline=yaml.safe_load((ROOT/'examples/sql_pipeline_demo/powerbi_design_plan.yaml').read_text())
        _,palette=prepare(baseline)
        self.assertNotEqual(palette['negative_tint'],'#FFF3DF')

    def test_invalid_color_cannot_silently_fall_back_to_white(self):
        self.plan['pages'][0]['visuals'][0]['fill']='blue'
        with self.assertRaisesRegex(ValueError,'RRGGBB'):prepare(self.plan)
        self.plan['pages'][0]['visuals'][0]['fill']='#FFFFFF'
        self.plan['design']['colors']={'not_a_role':'#FFFFFF'}
        with self.assertRaisesRegex(ValueError,'颜色角色'):prepare(self.plan)

    def test_line_labels_are_sparse_and_ranking_sorts_by_value(self):
        import json
        column=next(v for v in self.plan['pages'][0]['visuals'] if v['type']=='column')
        column['sort_by']='measure'
        path=self.root/'plan.yaml';path.write_text(yaml.safe_dump(self.plan,allow_unicode=True))
        out=self.root/'project';generate(self.run,path,out)
        visuals=[json.loads(p.read_text())['visual'] for p in out.rglob('visual.json')]
        line=next(v for v in visuals if v['visualType']=='lineChart')
        self.assertEqual(line['objects']['labels'][0]['properties']['show']['expr']['Literal']['Value'],'false')
        bar=next(v for v in visuals if v['visualType']=='clusteredColumnChart')
        order=bar['query']['sortDefinition']['sort'][0]
        self.assertIn('Measure',order['field'])
        self.assertEqual(order['direction'],'Descending')


if __name__=='__main__':unittest.main()
