from pathlib import Path
p=Path('hardware/tools/upper_finish_signals.py'); s=p.read_text()
s=s.replace('step = 0.05','step = 0.1')
s=s.replace('items = json.loads((root / "route_geometry.json").read_text())', '''items = json.loads((root / "route_geometry.json").read_text())
for region in json.loads((root / "filled_regions.json").read_text()):
    items.append({"kind": "zone", "net": region["net"], "coords": region["coords"], "layers": [["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"].index(region["layer"])]})''')
s=s.replace('def shape(item):\n', 'def shape(item):\n    if item["kind"] == "zone":\n        return Polygon(item["coords"]).buffer(0)\n')
a=s.index('for net in ['); z=s.index(']:',a)
s=s[:a]+'for net in ["GND"] * 6 + ["AGND"] * 5'+s[z:]
s=s.replace('assert len(groups) == 2, (net, len(groups))\n    source, target = groups', 'if len(groups) == 1:\n        continue\n    source = groups[0]\n    target = [i for group in groups[1:] for i in group]')
s=s.replace('if item["net"] != net]', 'if item["net"] != net and item["kind"] != "zone"]')
s=s.replace('manual_routes.json', 'ground_routes.json')
Path('hardware/tools/upper_finish_ground.py').write_text(s)
p=Path('hardware/tools/upper_add_routes.py'); s=p.read_text().replace('import json','import json\nimport sys').replace('root / "manual_routes.json"', 'root / (sys.argv[1] if len(sys.argv) > 1 else "manual_routes.json")'); p.write_text(s)
