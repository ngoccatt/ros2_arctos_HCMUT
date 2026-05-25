"""One-shot helper: print all labeled cells from Thesis.drawio"""
import xml.etree.ElementTree as ET, zlib, base64, sys, os

fp = os.path.join(os.path.dirname(__file__), '..', 'Thesis.drawio')
tree = ET.parse(fp)
root = tree.getroot()

for diag in root.findall('diagram'):
    name = diag.get('name', '')
    print(f'\n{"="*60}')
    print(f'DIAGRAM: {name}')
    print('='*60)
    model = diag.find('mxGraphModel')
    if model is None:
        content = diag.text.strip() if diag.text else ''
        decoded = base64.b64decode(content)
        raw = zlib.decompress(decoded, -15).decode('utf-8')
        model = ET.fromstring(raw)
    cells = model.findall('.//mxCell')
    for c in cells:
        val = c.get('value', '')
        if not val or not val.strip():
            continue
        geo = c.find('mxGeometry')
        x = geo.get('x','?') if geo is not None else '?'
        y = geo.get('y','?') if geo is not None else '?'
        w = geo.get('width','?') if geo is not None else '?'
        h = geo.get('height','?') if geo is not None else '?'
        # skip html noise
        clean = val.replace('<br>','|').replace('<b>','').replace('</b>','')
        clean = clean[:120]
        print(f'  ({x:>6},{y:>6}) {w:>5}x{h:<5} | {clean}')
