"""Build a local PBIP/PBIR draft from a passed SQL run and explicit report plan."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import math
import hashlib
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/powerbi_blank"
SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/"
TYPES = {
    "text": ("string", "type text"), "int64": ("int64", "Int64.Type"),
    "decimal": ("decimal", "Currency.Type"), "double": ("double", "type number"),
    "date": ("dateTime", "type date"), "datetime": ("dateTime", "type datetime"),
    "boolean": ("boolean", "type logical"),
}


class BIError(ValueError):
    pass


def text(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise BIError("名称必须是非空单行字符串。")
    return value


def tq(value):
    return "'" + text(value).replace("'", "''") + "'"


def mq(value):
    return '"' + str(value).replace('"', '""').replace('\r', '#(cr)').replace('\n', '#(lf)') + '"'


def dax_column(table, column):
    return tq(table) + "[" + column.replace("]", "]]") + "]"


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha(path):
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def sql_type(field):
    value = field["field_type"].lower()
    if re.match(r"(tinyint|smallint|mediumint|int|bigint)\b", value):
        return "int64"
    if re.match(r"(float|double|real)\b", value):
        return "double"
    decimal = re.match(r"decimal\((\d+),(\d+)\)", value)
    if decimal:
        # Currency is fixed-point with four fractional digits. Do not silently
        # coerce arbitrary MySQL DECIMAL to a lossy BI numeric representation.
        if int(decimal[1]) <= 18 and int(decimal[2]) <= 4:
            return "decimal"
        raise BIError("高精度 DECIMAL 需明确选用 text/double 等映射并评估精度，不自动舍入。")
    if value == "date":
        return "date"
    if value.startswith(("datetime", "timestamp")):
        return "datetime"
    if value.startswith(("varchar", "char", "text", "longtext", "mediumtext", "tinytext", "enum")):
        return "text"
    raise BIError(f"需显式指定 Power BI 字段类型：{field['field_name']}")


def validate_value(value, kind):
    if value == "" or kind == "text":
        return
    try:
        if kind == "int64":
            number = Decimal(value)
            if not number.is_finite() or number != number.to_integral_value() or not -(2**63) <= number < 2**63:
                raise ValueError()
        elif kind == "decimal":
            number = Decimal(value)
            if not number.is_finite() or not Decimal("-922337203685477.5808") <= number <= Decimal("922337203685477.5807") or number != number.quantize(Decimal("0.0001")):
                raise ValueError()
        elif kind == "double" and not math.isfinite(float(value)):
            raise ValueError()
        elif kind == "date":
            date.fromisoformat(value)
        elif kind == "datetime":
            datetime.fromisoformat(value)
        elif kind == "boolean" and value.lower() not in {"true", "false"}:
            raise ValueError()
    except (ValueError, InvalidOperation, OverflowError):
        raise BIError(f"CSV 值不能无损映射为 {kind}；请检查类型和数值范围。") from None


def load_inputs(run_dir, spec_path):
    report = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if report.get("status") != "passed":
        raise BIError("只能使用 status: passed 的 SQL 运行结果。")
    if report.get("runtime", {}).get("mode") == "temporary" and report["runtime"].get("cleanup") != "completed":
        raise BIError("临时 SQL 环境尚未清理完成。")
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    approved = {entry["path"]: entry for entry in manifest}
    for relative in ["model/model.json"]:
        if relative not in approved or sha(run_dir / relative) != approved[relative]["sha256"]:
            raise BIError("SQL 模型产物与清单不一致。")
    model = json.loads((run_dir / "model/model.json").read_text(encoding="utf-8"))
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,60}", spec.get("project", "")):
        raise BIError("project 请使用以字母开头的 ASCII 名称。")
    tables = {}
    for item in spec.get("tables", []):
        name = text(item["name"])
        if name in tables:
            raise BIError("模型表名重复。")
        export = text(item["export"])
        if any(c in export for c in '/\\:') or export in {".", ".."}:
            raise BIError("export 必须是本次 CSV 的文件名。")
        relative = f"tables/{export}.csv"
        path = run_dir / relative
        if relative not in approved or not path.is_file() or sha(path) != approved[relative]["sha256"]:
            raise BIError("CSV 不存在、不是本次交付产物或校验和变化。")
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), None)
        if not header or len(header) != len(set(header)):
            raise BIError("CSV 表头为空或有重复列。")
        fields = {f["field_name"]: f for f in model["fields"] if f["table_name"] == item["source_table"]}
        overrides = item.get("column_types", {})
        if set(overrides) - set(header):
            raise BIError("类型覆盖包含不存在的 CSV 字段。")
        columns = []
        for column in header:
            text(column)
            if column not in fields and column not in overrides:
                raise BIError(f"导出字段 {column} 缺少来源类型；聚合/表达式别名需显式 column_types。")
            kind = overrides[column] if column in overrides else sql_type(fields[column])
            if kind not in TYPES:
                raise BIError("不支持的字段类型映射。")
            columns.append({"name": column, "type": kind, "description": fields.get(column, {}).get("comment", "")})
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                if None in row or any(value is None for value in row.values()):
                    raise BIError("CSV 行宽与表头不一致。")
                for col in columns:
                    validate_value(row[col["name"]], col["type"])
        tables[name] = {**item, "columns": columns, "csv_path": path, "csv_sha256": sha(path)}
    if not tables:
        raise BIError("至少声明一张真实结果表。")
    measures = {}
    for item in spec.get("measures", []):
        name = text(item["name"])
        table = item["table"]
        if table not in tables or name in measures or name in {c["name"] for c in tables[table]["columns"]}:
            raise BIError("度量值名称重复、与列冲突或表不存在。")
        aggregation = item["aggregation"]
        if aggregation == "countrows":
            expression = f"COUNTROWS({tq(table)})"
        elif aggregation in {"sum", "average", "min", "max", "distinctcount"}:
            col = next((c for c in tables[table]["columns"] if c["name"] == item.get("column")), None)
            if not col:
                raise BIError("度量值引用了不存在的列。")
            if aggregation in {"sum", "average"} and col["type"] not in {"int64", "decimal", "double"}:
                raise BIError("SUM/AVERAGE 只能用于显式数值列。")
            expression = f"{aggregation.upper()}({dax_column(table, col['name'])})"
        else:
            raise BIError("首版仅支持 countrows/sum/average/min/max/distinctcount。")
        measures[name] = {**item, "expression": expression}
    # Relationships are never inferred from names. Validate declared cardinality
    # and keys against actual CSVs before writing the model.
    for rel in spec.get("relationships", []):
        for side in ("from", "to"):
            if rel[side]["table"] not in tables:
                raise BIError("关联表不存在。")
            table = tables[rel[side]["table"]]
            if rel[side]["column"] not in {c["name"] for c in table["columns"]}:
                raise BIError("关联字段不存在。")
        left, right = rel["from"], rel["to"]
        left_type = next(c['type'] for c in tables[left['table']]['columns'] if c['name'] == left['column'])
        right_type = next(c['type'] for c in tables[right['table']]['columns'] if c['name'] == right['column'])
        if left_type != right_type:
            raise BIError("关联字段类型不一致。")
        values = set()
        with tables[right['table']]['csv_path'].open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                value = row[right['column']]
                if value == '' or value in values:
                    raise BIError("关联一端必须非空且唯一。")
                values.add(value)
        with tables[left['table']]['csv_path'].open(encoding='utf-8-sig', newline='') as stream:
            if any(row[left['column']] not in values for row in csv.DictReader(stream)):
                raise BIError("关联多端存在未匹配的键。")
    return report, spec, tables, measures


def table_tmdl(table, measures):
    name = table["name"]
    lines = [f"table {tq(name)}", f"\tlineageTag: {uuid.uuid4()}", ""]
    if table.get("hidden", False):
        lines += ["\tisHidden", ""]
    for column in table["columns"]:
        dtype, _ = TYPES[column["type"]]
        if column["description"]:
            lines += ["\t/// " + line for line in column["description"].splitlines()]
        lines += [f"\tcolumn {tq(column['name'])}", f"\t\tdataType: {dtype}",
                  f"\t\tlineageTag: {uuid.uuid4()}", f"\t\tsummarizeBy: none", f"\t\tsourceColumn: {mq(column['name'])}"]
        if column["type"] == "date":
            lines += ["\t\tformatString: yyyy-MM-dd"]
        lines += [""]
    for measure in measures.values():
        if measure["table"] == name:
            lines += ["\t/// " + line for line in measure.get("description", measure["name"]).splitlines()]
            lines += [f"\tmeasure {tq(measure['name'])} = {measure['expression']}",
                      f"\t\tformatString: {measure.get('format', '#,0.00')}",
                      f"\t\tlineageTag: {uuid.uuid4()}", ""]
    mapping = ", ".join("{" + mq(c["name"]) + ", " + TYPES[c["type"]][1] + "}" for c in table["columns"])
    lines += [f"\tpartition {tq(name)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              f"\t\t\t\t    Source = Csv.Document(File.Contents(DataRoot & {mq('/' + table['export'] + '.csv')}), [Delimiter=\",\", Columns={len(table['columns'])}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),",
              "\t\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
              f"\t\t\t\t    Typed = Table.TransformColumnTypes(Headers, {{{mapping}}}, \"zh-CN\")",
              "\t\t\t\tin", "\t\t\t\t    Typed", ""]
    return "\n".join(lines)


def projection(table, name, measure=False):
    field = {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}
    return {"field": field, "queryRef": table + "." + name, "nativeQueryRef": name, "active": True}


def literal(value):
    return {"expr": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}


def visual_definition(item, tables, measures, index, page):
    kind = item["type"]
    roles = {}
    if kind in {"card", "column", "line"}:
        name = item["measure"]
        if name not in measures:
            raise BIError("图表引用了不存在的度量值。")
        metric = measures[name]
        roles["Values" if kind == "card" else "Y"] = {"projections": [projection(metric["table"], name, True)]}
    if kind in {"column", "line", "table", "slicer"}:
        table = item["table"]
        if table not in tables:
            raise BIError("图表引用了不存在的表。")
        fields = item.get("columns", []) if kind == "table" else [item["column"]]
        if not fields or any(field not in {c["name"] for c in tables[table]["columns"]} for field in fields):
            raise BIError("图表引用了不存在的列。")
        if kind == 'line' and next(c['type'] for c in tables[table]['columns'] if c['name'] == fields[0]) not in {'date','datetime','int64','double','decimal'}:
            raise BIError("趋势图横轴需明确日期或数值类型。")
        roles["Category" if kind in {"column", "line"} else "Values"] = {"projections": [projection(table, field) for field in fields]}
    if kind not in {"card", "column", "line", "table", "slicer"}:
        raise BIError("首版只支持指标卡、柱状图、折线图、表格和筛选器。")
    x, y, width, height = item["position"]
    if any(not isinstance(v, (int, float)) for v in (x, y, width, height)) or min(x, y) < 0 or min(width, height) < 50 or x + width > page["width"] or y + height > page["height"]:
        raise BIError("图表位置超出页面或尺寸无效。")
    query = {"queryState": roles}
    if kind in {'column','line'}:
        query['sortDefinition'] = {'sort': [{'field': roles['Category']['projections'][0]['field'], 'direction': 'Ascending'}], 'isDefaultSort': True}
    return {"$schema": SCHEMA_BASE + "item/report/definition/visualContainer/2.7.0/schema.json",
            "name": f"visual{index:014x}", "position": {"x": x, "y": y, "width": width, "height": height, "z": index, "tabOrder": index},
            "visual": {"visualType": {"card": "card", "column": "clusteredColumnChart", "line": "lineChart", "table": "tableEx", "slicer": "slicer"}[kind],
                       "query": query, "drillFilterOtherVisuals": True,
                       "visualContainerObjects": {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": literal(item.get("title", kind))}}]}}}


def generate(run_dir, spec_path, output):
    report, spec, tables, measures = load_inputs(run_dir, spec_path)
    if output.exists():
        raise BIError("输出目录已存在；为避免覆盖，请选择新目录。")
    if output.resolve().is_relative_to(run_dir.resolve()):
        raise BIError("报表工程应放在 SQL 运行目录外，避免修改原始交付产物。")
    output.mkdir(parents=True)
    try:
        project = spec["project"]
        report_name, model_name = project + ".Report", project + ".SemanticModel"
        shutil.copytree(TEMPLATE / "Blank.Report", output / report_name)
        shutil.copytree(TEMPLATE / "Blank.SemanticModel", output / model_name)
        pbip = json.loads((TEMPLATE / "Blank.pbip").read_text())
        pbip["artifacts"][0]["report"]["path"] = report_name
        dump(output / (project + ".pbip"), pbip)
        pbir = json.loads((output / report_name / "definition.pbir").read_text())
        pbir["datasetReference"]["byPath"]["path"] = "../" + model_name
        dump(output / report_name / "definition.pbir", pbir)
        model_path = output / model_name / "definition"
        (model_path / "tables").mkdir()
        model_text = (model_path / "model.tmdl").read_text(encoding="utf-8-sig")
        model_text += "\n" + "\n".join("ref table " + tq(t) for t in tables) + "\nref expression DataRoot\n"
        (model_path / "model.tmdl").write_text(model_text, encoding="utf-8")
        (model_path / "expressions.tmdl").write_text('expression DataRoot = "__SET_DATA_ROOT__" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\tlineageTag: ' + str(uuid.uuid4()) + '\n', encoding="utf-8")
        for index, table in enumerate(tables.values(), 1):
            (model_path / "tables" / f"table_{index:03}.tmdl").write_text(table_tmdl(table, measures), encoding="utf-8")
            (output / "data").mkdir(exist_ok=True)
            shutil.copy2(table["csv_path"], output / "data" / (table["export"] + ".csv"))
        if spec.get("relationships"):
            lines = []
            for rel in spec["relationships"]:
                lines += [f"relationship {uuid.uuid4()}", "\tfromColumn: " + tq(rel['from']['table']) + "." + tq(rel['from']['column']),
                          "\ttoColumn: " + tq(rel['to']['table']) + "." + tq(rel['to']['column']),
                          "\tfromCardinality: many", "\ttoCardinality: one", "\tcrossFilteringBehavior: oneDirection", ""]
            (model_path / "relationships.tmdl").write_text("\n".join(lines), encoding="utf-8")
        pages = output / report_name / "definition/pages"
        shutil.rmtree(pages)
        pages.mkdir()
        page_ids = []
        total_visuals = 0
        for index, page_spec in enumerate(spec.get("pages", []), 1):
            page_id = f"page{index:016x}"
            page_ids.append(page_id)
            page = {"$schema": SCHEMA_BASE + "item/report/definition/page/2.1.0/schema.json", "name": page_id,
                    "displayName": text(page_spec["title"]), "displayOption": "FitToPage", "width": page_spec.get("width", 1920), "height": page_spec.get("height", 1080)}
            dump(pages / page_id / "page.json", page)
            for visual_index, visual in enumerate(page_spec.get("visuals", []), 1):
                v = visual_definition(visual, tables, measures, visual_index, page)
                dump(pages / page_id / "visuals" / v["name"] / "visual.json", v)
                total_visuals += 1
        if not page_ids or not total_visuals:
            raise BIError("至少需要一个页面和一个数据图表。")
        dump(pages / "pages.json", {"$schema": SCHEMA_BASE + "item/report/definition/pagesMetadata/1.1.0/schema.json", "pageOrder": page_ids, "activePageName": page_ids[0]})
        manifest = {"status": "draft", "desktop_validated": False, "projectFile": project + ".pbip",
                    "modelDirectory": model_name, "sql_run_id": report["run_id"],
                    "tables": len(tables), "fields": sum(len(t["columns"]) for t in tables.values()), "measures": len(measures),
                    "pages": len(page_ids), "visuals": total_visuals, "business_purpose": spec.get("business_purpose", "待确认"),
                    "source_csv_sha256": {t["export"]: t["csv_sha256"] for t in tables.values()}}
        dump(output / "project-manifest.json", manifest)
        dump(output / "report-plan.json", spec)
        write_launcher(output)
        (output / "README.txt").write_text("Power BI 可编辑工程草稿（尚未在 Desktop 验证）\n\n" +
            spec.get('business_purpose', '') + "\n\n1. 解压完整文件夹。\n2. Windows 双击 OpenReport.cmd，自动配置 CSV 路径并打开 PBIP。\n" +
            "3. 在 Power BI Desktop 中点击刷新，检查字段、DAX、筛选和图表。\n" +
            "4. 文件夹移动后重新运行 OpenReport.cmd。也可手动将 DataRoot 参数设置为 data 文件夹的绝对路径。\n" +
            "不包含 PBIX 二进制缓存。CSV 是 SQL 运行结果的副本，不需要重新连接已经删除的临时 MySQL。\n" +
            "合成演示不能作为真实业务成果。Desktop 打开/刷新是最终验证，静态检查不能替代。\n", encoding="utf-8")
        return manifest
    except BaseException:
        # Only remove this newly created output, never the input run or template.
        shutil.rmtree(output)
        raise


def write_launcher(output):
    script = r'''param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $root 'project-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$path = Join-Path $root ($manifest.modelDirectory + '/definition/expressions.tmdl')
$data = (Join-Path $root 'data').Replace('\','/')
$value = [IO.File]::ReadAllText($path)
$pattern = '(?m)^(expression DataRoot = )"(?:[^"]|"")*"'
if (-not [regex]::IsMatch($value, $pattern)) { throw 'DataRoot parameter not found.' }
$value = [regex]::Replace($value, $pattern, {param($m) $m.Groups[1].Value + [char]34 + $data.Replace([string][char]34,([string][char]34+[char]34)) + [char]34})
[IO.File]::WriteAllText($path, $value, (New-Object Text.UTF8Encoding($false)))
if (-not $PrepareOnly) { Start-Process -FilePath (Join-Path $root $manifest.projectFile) }
'''
    (output / "PrepareAndOpen.ps1").write_text(script, encoding="utf-8-sig")
    (output / "OpenReport.cmd").write_bytes(b'@echo off\r\npowershell -NoProfile -File "%~dp0PrepareAndOpen.ps1"\r\nif errorlevel 1 pause\r\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = generate(args.run_dir.resolve(), args.plan.resolve(), args.output.resolve())
    except Exception as exc:
        print(str(exc) if isinstance(exc, BIError) else type(exc).__name__, file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
