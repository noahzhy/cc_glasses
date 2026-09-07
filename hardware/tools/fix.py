from pathlib import Path
p = Path('hardware/tools/export_dsn.py')
s = p.read_text().replace('import json', 'import json\nimport sys')
s = s.replace("root = Path('hardware/ir_glasses')", "root = Path(sys.argv[1] if len(sys.argv) > 1 else 'hardware/ir_glasses')")
p.write_text(s)
