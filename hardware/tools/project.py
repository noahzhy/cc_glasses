import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'hardware/ir_glasses')
config = json.loads(Path('D:/kicad_pcb/test/test.kicad_pro').read_text())
config['meta']['filename'] = 'ir_glasses.kicad_pro'
config['board']['design_settings']['rules'].update({
    'min_clearance': 0.15, 'min_track_width': 0.15,
    'min_via_diameter': 0.6, 'min_through_hole_diameter': 0.3,
    'min_via_annular_width': 0.1, 'min_copper_edge_clearance': 0.3,
})
config['net_settings'] = {
    'meta': {'version': 4},
    'classes': [{'name': 'Default', 'description': 'EVT signals',
                 'clearance': 0.15, 'track_width': 0.18,
                 'via_diameter': 0.6, 'via_drill': 0.3,
                 'microvia_diameter': 0.3, 'microvia_drill': 0.1,
                 'diff_pair_width': 0.18, 'diff_pair_gap': 0.2,
                 'diff_pair_via_gap': 0.25}],
    'netclass_assignments': {}, 'netclass_patterns': [],
}
config['board']['design_settings']['drc_exclusions'] = []
(root / 'ir_glasses.kicad_pro').write_text(json.dumps(config, indent=2))
