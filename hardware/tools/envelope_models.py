from pathlib import Path

root = Path('hardware/ir_glasses/refinement')
models = root / 'models'
models.mkdir(exist_ok=True)
for name, dimensions, color in [
    ('Everlight_IR11_21C', (3, 1.5, 1.5), '.25 .35 .45'),
    ('Everlight_PD15_22B', (3.2, 2.7, 1.1), '.08 .08 .1'),
]:
    x, y, z = (n / 2.54 for n in dimensions)
    model = (
        '#VRML V2.0 utf8\n'
        '# Mechanical envelope only; not a manufacturer model.\n'
        f'Transform {{ translation 0 0 {z / 2} children [ Shape {{ '
        f'appearance Appearance {{ material Material {{ diffuseColor {color} }} }} '
        f'geometry Box {{ size {x} {y} {z} }} }} ] }}\n')
    (models / f'{name}.wrl').write_text(model)
    fp = root / 'IR_Glasses.pretty' / f'{name}.kicad_mod'
    content = fp.read_text().rstrip()
    addition = (
        f'(model "${{KIPRJMOD}}/models/{name}.wrl"'
        ' (offset (xyz 0 0 0)) (scale (xyz 1 1 1))'
        ' (rotate (xyz 0 0 0)))')
    fp.write_text(content[:-1] + addition + '\n)')
