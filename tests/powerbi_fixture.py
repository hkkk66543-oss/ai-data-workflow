"""Synthetic unit-test input; not evidence of a real MySQL execution."""
import csv
import hashlib
import json


def create_run(root):
    (root/'tables').mkdir(parents=True)
    (root/'model').mkdir()
    with (root/'tables/清洗明细.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['记录编号','类别','数值','记录日期'])
        writer.writerows([['001','A','10.50','2026-01-01'],['002','A','20.00','2026-01-02'],['003','B','30.00','2026-01-02']])
    fields=[{'table_name':'清洗_记录','field_name':name,'field_type':kind,'comment':'合成单元测试字段'}
            for name,kind in [('记录编号','varchar(10)'),('类别','varchar(10)'),('数值','decimal(12,2)'),('记录日期','date')]]
    (root/'model/model.json').write_text(json.dumps({'fields':fields},ensure_ascii=False),encoding='utf-8')
    (root/'run.json').write_text(json.dumps({'status':'passed','run_id':'synthetic-unit-fixture','runtime':{'mode':'temporary','cleanup':'completed'},'note':'Synthetic unit fixture; no MySQL execution claimed.'}),encoding='utf-8')
    entries=[{'path':str(p.relative_to(root)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in [root/'tables/清洗明细.csv',root/'model/model.json']]
    (root/'manifest.json').write_text(json.dumps(entries,ensure_ascii=False),encoding='utf-8')
    return root
