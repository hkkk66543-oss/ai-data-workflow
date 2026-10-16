"""Data-aware page composition and editable native Power BI design elements.

Original implementation; design principles informed by microsoft/skills-for-fabric.
No external executables, installers, custom visuals, or network requests.
"""
from copy import deepcopy
import math
import csv

PALETTES = {
    'ocean': {'accent':'#126DFF','secondary':'#00A896','ink':'#152841','muted':'#60748C','canvas':'#F2F5FA','surface':'#FFFFFF','edge':'#DCE5F0'},
    'forest': {'accent':'#087F70','secondary':'#C67B27','ink':'#173C36','muted':'#61776F','canvas':'#F1F6F2','surface':'#FFFFFF','edge':'#D8E6DE'},
    'plum': {'accent':'#7554C9','secondary':'#D47B49','ink':'#302944','muted':'#766C85','canvas':'#F5F3F9','surface':'#FFFFFF','edge':'#E2DCED'},
}


def prepare(spec, tables=None):
    """Apply opt-in layout recipes, using only explicitly bound existing visuals."""
    spec = deepcopy(spec)
    design = spec.get('design')
    if not design:
        return spec, None
    palette_name = design.get('palette','ocean')
    if palette_name not in PALETTES:
        raise ValueError('design.palette 请选择 ocean、forest 或 plum。')
    palette = PALETTES[palette_name]
    # Inspect actual exported distributions; these are hints, never new metrics.
    profiles = {}
    for name, table in (tables or {}).items():
        columns = {c['name']:{'type':c['type'],'values':set(),'max_length':0} for c in table['columns']}
        count = 0
        with table['csv_path'].open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                count += 1
                for key, info in columns.items():
                    value = row[key]
                    if value and len(info['values']) < 1001:info['values'].add(value)
                    info['max_length']=max(info['max_length'],len(value))
        profiles[name]={'rows':count,'columns':{key:{'type':info['type'],'distinct_up_to_1001':len(info['values']),'max_length':info['max_length']} for key,info in columns.items()}}
    spec['design_profile']=profiles
    for page in spec['pages']:
        page.setdefault('width',1920); page.setdefault('height',1080)
        # Recipes have a tested FHD geometry; preserve arbitrary manual canvases.
        layout = page.get('layout','auto')
        if layout not in {'auto','overview','comparison','detail','manual'}:
            raise ValueError('不支持的页面布局。')
        source = page['visuals']
        for v in source:
            profile=profiles.get(v.get('table'),{}).get('columns',{}).get(v.get('column'),{})
            if layout=='auto' and v['type']=='column' and (profile.get('distinct_up_to_1001',0)>8 or profile.get('max_length',0)>12):
                v['type']='bar'
                v['design_reason']='类别较多或名称较长，改用横向条形图提高可读性。'
        if layout != 'manual' and (page['width'],page['height']) != (1920,1080):
            raise ValueError('自动布局当前使用 1920x1080；其他画布请指定 manual 布局。')
        if any(v['type']=='text' for v in source) and layout != 'manual':
            raise ValueError('手动文本请使用 manual 布局或 page.subtitle。')
        cards=[v for v in source if v['type']=='card']
        slicers=[v for v in source if v['type']=='slicer']
        charts=[v for v in source if v['type'] in {'column','bar','line'}]
        tables=[v for v in source if v['type']=='table']
        if layout=='auto':
            layout='detail' if tables and not charts else ('comparison' if charts and not any(v['type']=='line' for v in charts) else 'overview')
        page['resolved_layout']=layout
        if layout != 'manual':
            if len(cards)>4 or len(slicers)>2 or len(charts)>4 or len(tables)>1:
                raise ValueError('自动布局每页最多 4 指标卡、2 筛选、4 图表、1 明细表；请拆页。')
            if len(cards)+len(slicers)+len(charts)+len(tables)!=len(source):
                raise ValueError('自动布局包含尚未支持的组件。')
            if layout=='detail' and (not tables or charts):
                raise ValueError('detail 布局用于明细表页面；分析图请放到 overview/comparison。')
            for i,v in enumerate(slicers):v['position']=[1408+i*248,48,232,120]
            top=216
            if cards:
                width=math.floor(((1856-24*(len(cards)-1))/len(cards))/8)*8
                for i,v in enumerate(cards):v['position']=[32+i*(width+24),216,width,144]
                top=408
            if charts:
                bottom=744 if tables else 984
                rows=math.ceil(len(charts)/2)
                h=math.floor(((bottom-top-24*(rows-1))/rows)/8)*8
                if h < 240:
                    raise ValueError("图表高度不足，请拆成多个页面。")
                for i,v in enumerate(charts):
                    if layout=='overview' and len(charts)==2:
                        x,w=(32,1128) if i==0 else (1184,704)
                    else:x,w=(32+(i%2)*944,912 if len(charts)>1 else 1856)
                    v['position']=[x,top+(i//2)*(h+24),w,h]
                top=792 if tables else 1032
            if tables:tables[0]['position']=[32,top,1856,984-top]
        def label(content,pos,size=12,color=None,bold=False,fill=None):
            return {'type':'text','text':content,'position':pos,'font_size':size,'color':color or palette['ink'],'bold':bold,'fill':fill}
        extras=[
            label(design.get('eyebrow','DATA / INSIGHTS'),[32,24,1200,32],11,palette['accent'],True),
            label(page['title'],[32,64,1320,64],28,bold=True),
            label(page.get('subtitle',design.get('subtitle','按业务问题组织页面 · 数据来自本次 SQL 校验结果')),[32,136,1320,40],12,palette['muted']),
            label(page.get('footer','来源：本次 SQL 导出 CSV · 点击筛选器查看联动 · 指标口径见报表说明'),[32,1016,1856,40],10,palette['muted']),
        ]
        if cards:extras.append(label('01  /  核心指标',[32,176,1320,32],11,palette['muted'],True))
        if charts:extras.append(label('02  /  '+('对比与结构' if layout=='comparison' else '分布与趋势'),[32,368 if cards else 176,1320,32],11,palette['muted'],True))
        if tables and charts:extras.append(label('03  /  明细核查',[32,752,1320,32],11,palette['muted'],True))
        page['visuals']=source+extras
        audit(page)
    return spec, palette


def audit(page):
    """Check bounds/overlap for interactive visuals and native text alike."""
    rectangles=[]
    for item in page['visuals']:
        box=item.get('position')
        if not isinstance(box,list) or len(box)!=4 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in box):
            raise ValueError('组件位置必须是 4 个有限数值。')
        x,y,w,h=box
        if min(x,y)<0 or min(w,h)<=0 or x+w>page['width'] or y+h>page['height']:
            raise ValueError('组件超出画布。')
        for left,top,width,height in rectangles:
            if x<left+width and x+w>left and y<top+height and y+h>top:
                raise ValueError('组件重叠，请拆页或调整位置。')
        rectangles.append(box)


def theme(palette,name):
    """Original theme values validated against Microsoft's monthly theme schema."""
    solid=lambda c:{'solid':{'color':c}}
    common={
        'background':[{'show':True,'color':solid(palette['surface']),'transparency':0}],
        'border':[{'show':True,'color':solid(palette['edge']),'radius':12}],
        'padding':[{'top':16,'bottom':16,'left':16,'right':16}],
        'title':[{'show':True,'fontSize':13,'fontColor':solid(palette['ink']),'fontFamily':'Segoe UI Semibold'}],
        'visualHeader':[{'show':False}],
    }
    styles={'*':{'*':common},'textbox':{'*':{
        'background':[{'show':False}],'border':[{'show':False}],
        'padding':[{'top':0,'bottom':0,'left':0,'right':0}], 'title':[{'show':False}]}},
        'card':{'*':{'labels':[{'fontSize':32,'color':solid(palette['accent'])}],
                     'categoryLabels':[{'show':False}]}},
        'tableEx':{'*':{
            'columnHeaders':[{'fontSize':12,'fontColor':solid(palette['ink']),'backColor':solid(palette['canvas']),'bold':True,'autoSizeColumnWidth':True,'columnAdjustment':'growToFit'}],
            'values':[{'fontSize':12,'fontColorPrimary':solid(palette['ink']),'fontColorSecondary':solid(palette['ink']),'backColorPrimary':solid('#FFFFFF'),'backColorSecondary':solid(palette['canvas'])}]}}
    }
    for kind in ['clusteredColumnChart','clusteredBarChart','lineChart']:
        styles[kind]={'*':{
            'labels':[{'show':True,'fontSize':11,'color':solid(palette['ink'])}],
            'categoryAxis':[{'fontSize':11,'labelColor':solid(palette['muted']),'showAxisTitle':False}],
            'valueAxis':[{'fontSize':10,'labelColor':solid(palette['muted']),'showAxisTitle':False,'gridlineColor':solid(palette['edge'])}],
            'legend':[{'show':False}],
        }}
    styles['lineChart']['*']['lineStyles']=[{'strokeWidth':3,'showMarker':True}]
    return {'name':name,'dataColors':[palette['accent'],palette['secondary'],'#D59B33','#8A6BD1','#D65C6C'],
            'background':palette['surface'],'foreground':palette['ink'],'tableAccent':palette['accent'],
            'textClasses':{'title':{'fontSize':14,'fontFace':'Segoe UI Semibold','color':palette['ink']},
                           'label':{'fontSize':11,'fontFace':'Segoe UI','color':palette['muted']}},'visualStyles':styles}
