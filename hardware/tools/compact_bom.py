import csv
import json
from pathlib import Path

root = Path('hardware/ir_glasses/EVT_B')
parts = json.loads((root / 'parts.json').read_text())
with (root / 'bom.csv').open('w', newline='', encoding='utf-8-sig') as out:
    writer = csv.writer(out)
    writer.writerow(['Reference', 'Value', 'Footprint', 'Quantity',
                     'Populate', 'X_mm', 'Y_mm', 'Rotation_deg'])
    for ref, part in parts.items():
        populate = not (ref.startswith('TP') or ref in {'NT1', 'J2'})
        writer.writerow([ref, part['value'], part['footprint'], 1,
                         'Yes' if populate else 'PCB pads only',
                         part['xy'][0] + 110, part['xy'][1] + 85,
                         part['angle']])
with (root / 'optical_map.csv').open('w', newline='', encoding='utf-8-sig') as out:
    writer = csv.writer(out)
    writer.writerow(['Eye_front_view', 'Cell', 'LED', 'PD', 'Main_receiver_PD'])
    for offset, eye in [(0, 'left'), (8, 'right')]:
        for n in range(8):
            writer.writerow([eye, n + 1, f'D{offset+n+1}', f'PD{offset+n+1}',
                             f'PD{offset+(n+4)%8+1}'])
