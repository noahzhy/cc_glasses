"""Generate the editable KiCad EVT schematic and placed two-layer board."""

import copy
import json
import math
import re
import shutil
import sys
import uuid
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'tools' / 'pylib'))
import sexpdata as sx

LIB = Path('D:/Program Files/KiCad/10.0/share/kicad')
NAME = 'ir_glasses'
SYMBOLS = {}
PARTS = {}
LIB_DATA = {}
PAGES = {}
ROOT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, 'cc_glasses/evt'))


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'cc_glasses/' + key))


def children(node, tag):
    return [x for x in node if isinstance(x, list) and str(x[0]) == tag]


def read_symbol(lib, name):
    if lib not in LIB_DATA:
        LIB_DATA[lib] = sx.loads(
            (LIB / 'symbols' / f'{lib}.kicad_sym').read_text())
    data = LIB_DATA[lib]
    entries = {x[1]: x for x in children(data, 'symbol')}

    def flatten(key):
        node = copy.deepcopy(entries[key])
        base = children(node, 'extends')
        if base:
            parent = flatten(base[0][1])
            props = {x[1] for x in children(node, 'property')}
            node = [x for x in node if not isinstance(x, list)
                    or str(x[0]) != 'extends']
            node.extend(copy.deepcopy(x) for x in parent[2:]
                        if isinstance(x, list)
                        and (str(x[0]) != 'property' or x[1] not in props))
        return node

    node = flatten(name)
    node[1] = name
    for sub in children(node, 'symbol'):
        sub[1] = name + '_' + '_'.join(sub[1].split('_')[-2:])
    SYMBOLS[name] = node
    return name


def box_symbol(name, pins):
    count = math.ceil(len(pins) / 2)
    half = (count + 1) * 1.27
    strings = []
    for index, (num, label, kind) in enumerate(pins):
        side = 0 if index < count else 1
        row = index % count
        x, angle = (-12.7, 0) if side == 0 else (12.7, 180)
        y = half - (row + 1) * 2.54
        strings.append(
            f'(pin {kind} line (at {x} {y} {angle}) (length 2.54)'
            f' (name "{label}" (effects (font (size 1 1))))'
            f' (number "{num}" (effects (font (size 1 1)))))')
    node = sx.loads(
        f'(symbol "{name}" (pin_names (offset 0.5)) (in_bom yes)'
        f' (on_board yes) (property "Reference" "U" (at 0 {half + 2.54} 0)'
        ' (effects (font (size 1.27 1.27))))'
        f' (property "Value" "{name}" (at 0 {half + 5.08} 0)'
        ' (effects (font (size 1.27 1.27))))'
        f' (symbol "{name}_0_1" (rectangle (start -10.16 {half})'
        f' (end 10.16 {-half}) (stroke (width 0.254) (type default))'
        ' (fill (type background))))'
        f' (symbol "{name}_1_1" {" ".join(strings)}))')
    SYMBOLS[name] = node
    return name


def add(ref, symbol, value, footprint, nets, xy, page, sch, angle=0):
    PARTS[ref] = dict(symbol=symbol, value=value, footprint=footprint,
                      nets={str(k): v for k, v in nets.items()}, xy=xy,
                      angle=angle, page=page, sch=sch)


R = read_symbol('Device', 'R')
C = read_symbol('Device', 'C')
LED = read_symbol('Device', 'LED')
for sub in children(SYMBOLS[LED], 'symbol'):
    for pin in children(sub, 'pin'):
        num = children(pin, 'number')[0]
        num[1] = '2' if num[1] == '1' else '1'
OP = read_symbol('Amplifier_Operational', 'TLV9064')
BUF = read_symbol('Amplifier_Operational', 'TLV9061xDBV')
MCU = read_symbol('MCU_ST_STM32C0', 'STM32C031C6Tx')
FB = read_symbol('Device', 'FerriteBead')
TP = read_symbol('Connector', 'TestPoint')
FLAG = read_symbol('power', 'PWR_FLAG')
NT = read_symbol('Device', 'NetTie_2')
J5 = read_symbol('Connector_Generic', 'Conn_01x05')
J10 = read_symbol('Connector_Generic', 'Conn_02x05_Odd_Even')
TVS = read_symbol('Device', 'D_TVS')
PD = box_symbol('PD15_22B', [('1', 'K1', 'passive'),
                           ('4', 'K4', 'passive'),
                           ('2', 'A2', 'passive'),
                           ('3', 'A3', 'passive')])
DRIVER = box_symbol('TLC59283RGE',
                    [('1', 'LAT', 'input')]
                    + [(str(i + 2), f'OUT{i}', 'open_collector')
                       for i in range(16)]
                    + [('18', 'BLANK', 'input'), ('19', 'SOUT', 'output'),
                       ('20', 'IREF', 'passive'), ('21', 'VCC', 'power_in'),
                       ('22', 'GND', 'power_in'), ('23', 'SIN', 'input'),
                       ('24', 'SCLK', 'input'), ('25', 'EP', 'power_in')])
MUX = box_symbol('TMUX1308PW', [(str(i), n, t) for i, n, t in [
    (1, 'S4', 'passive'), (2, 'S6', 'passive'), (3, 'D', 'passive'),
    (4, 'S7', 'passive'), (5, 'S5', 'passive'), (6, '~{EN}', 'input'),
    (7, 'NC', 'no_connect'), (8, 'GND', 'power_in'), (9, 'A2', 'input'),
    (10, 'A1', 'input'), (11, 'A0', 'input'), (12, 'S3', 'passive'),
    (13, 'S0', 'passive'), (14, 'S1', 'passive'), (15, 'S2', 'passive'),
    (16, 'VDD', 'power_in')]])
IMU = box_symbol('LSM6DS3TR_C', [(str(i), n, t) for i, n, t in [
    (1, 'SA0', 'input'), (2, 'SDx', 'input'), (3, 'SCx', 'input'),
    (4, 'INT1', 'output'), (5, 'VDDIO', 'power_in'),
    (6, 'GND', 'power_in'), (7, 'GND', 'power_in'),
    (8, 'VDD', 'power_in'), (9, 'INT2', 'output'),
    (10, 'NC', 'no_connect'), (11, 'NC', 'no_connect'),
    (12, 'CS', 'input'), (13, 'SCL', 'input'),
    (14, 'SDA', 'bidirectional')]])
ESD = box_symbol('PESD3V3L2BT', [('1', 'IO1', 'passive'),
                               ('2', 'IO2', 'passive'),
                               ('3', 'GND', 'passive')])
RFP = 'Resistor_SMD:R_0402_1005Metric'
CFP = 'Capacitor_SMD:C_0402_1005Metric'

add('U9', MCU, 'STM32C031C6T6', 'Package_QFP:LQFP-48_7x7mm_P0.5mm',
    {5: '3V3_A', 6: '3V3', 7: 'GND', 10: 'NRST', 11: 'ADC_L',
     12: 'ADC_R', 13: 'UART_TX', 14: 'UART_RX', 15: 'MUX_A0',
     16: 'LED_SCLK', 17: 'MUX_A1', 18: 'LED_SIN', 19: 'MUX_A2',
     20: 'LED_LAT', 21: 'LED_BLANK', 29: 'BOOT_TX_PA9',
     32: 'BOOT_RX_PA10', 35: 'SWDIO', 36: 'SWCLK_BOOT0',
     42: 'IMU_INT', 45: 'I2C_SCL', 46: 'I2C_SDA'},
    (0, -30), 'control', (60, 88))
add('U1', DRIVER, 'TLC59283RGER',
    'Package_DFN_QFN:Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm',
    {**{i + 2: f'LED_K{i + 1}' for i in range(16)},
     1: 'LED_LAT', 18: 'LED_BLANK', 20: 'IREF', 21: '3V3',
     22: 'GND', 23: 'LED_SIN', 24: 'LED_SCLK', 25: 'GND'},
    (0, -14), 'power', (65, 75))
add('U10', IMU, 'LSM6DS3TR-C',
    'Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y',
    {1: 'GND', 2: 'GND', 3: 'GND', 4: 'IMU_INT', 5: '3V3',
     6: 'GND', 7: 'GND', 8: '3V3', 12: '3V3', 13: 'I2C_SCL',
     14: 'I2C_SDA'}, (12, -33), 'control', (160, 60))
add('U6', BUF, 'TLV9061IDBVR', 'Package_TO_SOT_SMD:SOT-23-5',
    {1: 'VREF_BUF', 2: 'AGND', 3: 'VREF_DIV', 4: 'VREF_BUF',
     5: '3V3_A'}, (-13, -33), 'power', (220, 70))
add('J1', J5, 'TE 0-1734839-5',
    'Connector_FFC-FPC:TE_0-1734839-5_1x05-1MP_P0.5mm_Horizontal',
    {1: '3V3', 2: 'GND', 3: 'HOST_TX', 4: 'HOST_RX', 5: 'NRST'},
    (25, -34), 'control', (260, 60))
add('J2', J10, 'TC2050-IDC-NL / ARM2010',
    'Connector:Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical',
    {1: '3V3', 2: 'SWDIO', 3: 'GND', 4: 'SWCLK_BOOT0', 10: 'NRST'},
    (-27, -34), 'control', (260, 115))
add('U11', ESD, 'PESD3V3L2BT', 'Package_TO_SOT_SMD:SOT-23',
    {1: 'HOST_TX', 2: 'HOST_RX', 3: 'GND'},
    (17, -26), 'control', (335, 60))
add('D17', TVS, 'PESD3V3S1BA', 'Diode_SMD:D_SOD-323',
    {1: '3V3', 2: 'GND'}, (31, -38), 'power', (35, 155))
add('FB1', FB, '600R@100MHz 500mA',
    'Inductor_SMD:L_0603_1608Metric', {1: '3V3', 2: '3V3_A'},
    (-10, -25), 'power', (155, 60))
add('NT1', NT, 'AGND-GND star',
    'NetTie:NetTie-2_SMD_Pad0.5mm', {1: 'AGND', 2: 'GND'},
    (-10, -22), 'power', (155, 95))

resistors = [
    ('R1', '2.65k', 'IREF', 'GND', (-3.5, -11)),
    ('R2', '10k', '3V3_A', 'VREF_DIV', (-16, -35)),
    ('R3', '10k', 'VREF_DIV', 'AGND', (-16, -31)),
    ('R4', '10k', '3V3', 'NRST', (-7, -31)),
    ('R5', '100k', 'SWCLK_BOOT0', 'GND', (7.5, -27)),
    ('R6', '4.7k', '3V3', 'I2C_SCL', (10, -36)),
    ('R7', '4.7k', '3V3', 'I2C_SDA', (13, -36)),
    ('R8', '22', 'UART_TX', 'HOST_TX', (21, -27)),
    ('R9', '22', 'HOST_RX', 'UART_RX', (21, -24)),
    ('R10', '10k', '3V3', 'LED_BLANK', (4, -16)),
    ('R11', '100', 'MUX_L', 'ADC_L', (-5, -3)),
    ('R12', '100', 'MUX_R', 'ADC_R', (5, -3)),
    ('R13', '47', 'VREF_BUF', 'VREF_1V65', (-13, -29)),
]
for i, (ref, val, n1, n2, xy) in enumerate(resistors):
    page = 'control' if ref in {'R4', 'R5', 'R6', 'R7', 'R8', 'R9'} else 'power'
    sch = (35 + (i % 7) * 50, 205 + (i // 7) * 40)
    if page == 'control':
        sch = (35 + ['R4', 'R5', 'R6', 'R7', 'R8', 'R9'].index(ref) * 42, 232)
    add(ref, R, val, RFP, {1: n1, 2: n2}, xy, page, sch)

optical = [(10, -13), (26, -23), (47, -22), (63, -12),
           (66, 9), (50, 23), (27, 23), (5, 9)]
for eye, sign in [('left', -1), ('right', 1)]:
    offset = 0 if eye == 'left' else 8
    amps = [2, 3] if eye == 'left' else [4, 5]
    for half, amp in enumerate(amps):
        nets = {4: '3V3_A', 11: 'AGND'}
        for local, pins in enumerate([(1, 2, 3), (7, 6, 5),
                                       (8, 9, 10), (14, 13, 12)]):
            channel = offset + half * 4 + local + 1
            out, minus, plus = pins
            nets.update({out: f'TIA{channel}', minus: f'PD_IN{channel}',
                         plus: 'VREF_1V65'})
        add(f'U{amp}', OP, 'TLV9064IDR',
            'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm', nets,
            (sign * 39, -31 if half == 0 else 32), eye, (0, 0))
    for local, (x, y) in enumerate(optical):
        n = offset + local + 1
        col, row = local % 4, local // 4
        sch_x, sch_y = 40 + col * 98, 65 + row * 105
        add(f'PD{n}', PD, 'PD15-22B/TR8', 'IR_Glasses:Everlight_PD15_22B',
            {1: f'PD_IN{n}', 4: f'PD_IN{n}', 2: 'AGND', 3: 'AGND'},
            (sign * x, y), eye, (sch_x, sch_y))
        led_y = y - 3.5 if local < 4 else y + 3.5
        add(f'D{n}', LED, 'IR11-21C/TR8', 'IR_Glasses:Everlight_IR11_21C',
            {1: '3V3', 2: f'LED_K{n}'},
            (sign * x, led_y), eye, (sch_x, sch_y - 33))
        amp = amps[local // 4]
        ax, ay = PARTS[f'U{amp}']['xy']
        dx = -5.2 if local % 4 < 2 else 5.2
        dy = -3.1 if local % 2 == 0 else 2
        for prefix, sym, val, dy2 in [('RF', R, '100k', 0),
                                     ('CF', C, '22p C0G', 1.6)]:
            add(f'{prefix}{n}', sym, val, RFP if sym == R else CFP,
                {1: f'TIA{n}', 2: f'PD_IN{n}'},
                (ax + dx, ay + dy + dy2), eye,
                (sch_x + 10 if sym == R else sch_x + 35, sch_y + 44))
    mux_n = 7 if eye == 'left' else 8
    nets = {6: 'AGND', 8: 'AGND', 9: 'MUX_A2', 10: 'MUX_A1',
            11: 'MUX_A0', 16: '3V3_A', 3: 'MUX_L' if sign < 0 else 'MUX_R'}
    for ch, pin in enumerate([13, 14, 15, 12, 1, 5, 2, 4]):
        nets[pin] = f'TIA{offset + ch + 1}'
    add(f'U{mux_n}', MUX, 'TMUX1308PWR',
        'Package_SO:TSSOP-16_4.4x5mm_P0.65mm', nets,
        (sign * 4.5, 23), eye, (245, 260))

caps = [
    ('1u', 'VREF_DIV', 'AGND', (-19, -32)),
    ('100n', '3V3', 'GND', (1, -18)),
    ('100n', '3V3_A', 'AGND', (-43, -25.5)),
    ('100n', '3V3_A', 'AGND', (-43, 26.5)),
    ('100n', '3V3_A', 'AGND', (35, -25.5)),
    ('100n', '3V3_A', 'AGND', (35, 26.5)),
    ('100n', '3V3_A', 'AGND', (-10, -34)),
    ('100n', '3V3_A', 'AGND', (-7, 4)),
    ('100n', '3V3_A', 'AGND', (7, 4)),
    ('100n', '3V3', 'GND', (-7.5, -33.5)),
    ('100n', '3V3_A', 'GND', (-6, -36)),
    ('100n', '3V3', 'GND', (15, -32)),
    ('100n', '3V3', 'GND', (10, -30)),
    ('100n', '3V3', 'GND', (29, -29)),
    ('100n', '3V3_A', 'AGND', (-19, -27)),
    ('100n', '3V3', 'GND', (0, -21)),
    ('100n', '3V3', 'GND', (7, -33)),
    ('1u', '3V3', 'GND', (2, -23)),
    ('1u', '3V3', 'GND', (-2, -37)),
    ('1u', '3V3', 'GND', (16, -35)),
    ('1u', '3V3_A', 'AGND', (-13, -24)),
    ('1u', '3V3_A', 'AGND', (-39, -24.5)),
    ('1u', '3V3_A', 'AGND', (39, -24.5)),
    ('1u', '3V3', 'GND', (30, -25)),
    ('10u', '3V3', 'GND', (35, -38)),
    ('10u', '3V3', 'GND', (4, -11)),
    ('10u', '3V3_A', 'AGND', (-17, -24)),
    ('47u 6.3V X5R', '3V3', 'GND', (6, -20)),
    ('1n', 'ADC_L', 'AGND', (-5, 0)),
    ('1n', 'ADC_R', 'AGND', (5, 0)),
    ('100n', 'VREF_1V65', 'AGND', (-16, -28)),
]
for index, (val, net, ground, xy) in enumerate(caps, 1):
    footprint = CFP
    if index in [25, 26, 27]:
        footprint = 'Capacitor_SMD:C_0603_1608Metric'
    if index == 28:
        footprint = 'Capacitor_SMD:C_1210_3225Metric'
    add(f'C{index}', C, val, footprint, {1: net, 2: ground}, xy,
        'decoupling', (30 + ((index - 1) % 8) * 48,
                       50 + ((index - 1) // 8) * 58))

for i, net in enumerate(['3V3', 'GND', 'UART_TX', 'UART_RX',
                         'BOOT_TX_PA9', 'BOOT_RX_PA10', 'SWCLK_BOOT0',
                         'NRST', 'VREF_1V65', '3V3', 'IMU_INT', '3V3_A'], 1):
    add(f'TP{i}', TP, net, 'TestPoint:TestPoint_Pad_D1.0mm', {1: net},
        (-21 + (i - 1) * 3.5, -39), 'control',
        (30 + ((i - 1) % 4) * 60, 155 + ((i - 1) // 4) * 22))


def pin_data(name, unit):
    result = []
    for sub in children(SYMBOLS[name], 'symbol'):
        section = int(sub[1].split('_')[-2])
        if section not in (0, unit):
            continue
        for pin in children(sub, 'pin'):
            at = children(pin, 'at')[0]
            result.append((children(pin, 'number')[0][1], *at[1:4]))
    return result


def text(value, x, y, size=1.6):
    return (f'(text {json.dumps(value)} (at {x} {y} 0)'
            f' (effects (font (size {size} {size})) (justify left))'
            f' (uuid "{uuid.uuid4()}"))')


def instance(ref, part, x, y, unit, path):
    x = round(x / 1.27) * 1.27
    y = round(y / 1.27) * 1.27
    name = part['symbol']
    ident = uid(f'{ref}/{unit}')
    in_bom = 'no' if ref.startswith('TP') or ref in {'NT1', 'J2'} else 'yes'
    result = [f'(symbol (lib_id "IR_Glasses:{name}") (at {x} {y} 0)'
              f' (unit {unit}) (in_bom {in_bom}) (on_board yes) (dnp no)'
              f' (uuid "{ident}")']
    for key, val in [('Reference', ref), ('Value', part['value']),
                     ('Footprint', part['footprint'])]:
        props = [p for p in children(SYMBOLS[name], 'property') if p[1] == key]
        at = children(props[0], 'at')[0][1:3] if props else [0, 0]
        hidden = ' hide' if key == 'Footprint' else ''
        justify = ''
        if name in {R, C, FB}:
            at = [2.54, 1.27 if key == 'Reference' else -1.27]
            justify = ' (justify left)'
        if name == TP and key == 'Value':
            hidden = ' hide'
        result.append(f'(property "{key}" {json.dumps(val)}'
                      f' (at {x + float(at[0])} {y - float(at[1])} 0)'
                      f' (effects (font (size 1.0 1.0)){justify}{hidden}))')
    for num, _, _, _ in pin_data(name, unit):
        result.append(f'(pin "{num}" (uuid "{uid(ref + "/pin/" + num)}"))')
    result.append(f'(instances (project "{NAME}" (path "{path}"'
                  f' (reference "{ref}") (unit {unit})))))')
    for num, px, py, angle in pin_data(name, unit):
        px, py = x + float(px), y - float(py)
        net = part['nets'].get(str(num))
        if net is None:
            result.append(f'(no_connect (at {px} {py})'
                          f' (uuid "{uuid.uuid4()}"))')
            continue
        rad = math.radians(float(angle))
        ex = round(px - 3.81 * math.cos(rad), 4)
        ey = round(py + 3.81 * math.sin(rad), 4)
        result.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey}))'
                      ' (stroke (width 0) (type default))'
                      f' (uuid "{uuid.uuid4()}"))')
        label_justify = 'right' if float(angle) in (0, 90) else 'left'
        result.append(f'(global_label "{net}" (shape passive)'
                      f' (at {ex} {ey} {(float(angle) + 180) % 360})'
                      f' (effects (font (size 0.95 0.95)) (justify {label_justify}))'
                      f' (uuid "{uuid.uuid4()}"))')
    return '\n'.join(result)


def make_schematics():
    pages = ['control', 'power', 'left', 'right', 'decoupling']
    library = '\n'.join(sx.dumps(s) for s in SYMBOLS.values())
    (ROOT / 'IR_Glasses.kicad_sym').write_text(
        '(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")'
        + library + ')', encoding='utf-8')
    (ROOT / 'sym-lib-table').write_text(
        '(sym_lib_table (version 7) (lib (name "IR_Glasses")'
        ' (type "KiCad") (uri "${KIPRJMOD}/IR_Glasses.kicad_sym")'
        ' (options "") (descr "Project-local symbols")))')
    embedded = []
    for symbol in SYMBOLS.values():
        symbol = copy.deepcopy(symbol)
        symbol[1] = 'IR_Glasses:' + symbol[1]
        embedded.append(sx.dumps(symbol))
    embedded_library = '\n'.join(embedded)
    for page in pages:
        page_id = ROOT_ID if page == 'control' else uid(page)
        path = f'/{ROOT_ID}' if page == 'control' else f'/{ROOT_ID}/{uid("sheet/" + page)}'
        body = []
        for ref, part in PARTS.items():
            if part['page'] != page:
                continue
            if ref in {'U2', 'U3', 'U4', 'U5'}:
                half = 0 if ref in {'U2', 'U4'} else 1
                for unit in range(1, 5):
                    x, y = 40 + (unit - 1) * 98, 65 + half * 105
                    body.append(instance(ref, part, x + 35, y + 16, unit, path))
                body.append(instance(ref, part, 50 + half * 90, 270, 5, path))
            else:
                body.append(instance(ref, part, *part['sch'], 1, path))
        if page == 'control':
            for i, child in enumerate(pages[1:]):
                x, y = 295, 150 + i * 24
                body.append(
                    f'(sheet (at {x} {y}) (size 80 16)'
                    ' (stroke (width 0.1524) (type default))'
                    ' (fill (color 0 0 0 0))'
                    f' (uuid "{uid("sheet/" + child)}")'
                    f' (property "Sheetname" "{child}" (at {x} {y - 1} 0)'
                    ' (effects (font (size 1.27 1.27)) (justify left bottom)))'
                    f' (property "Sheetfile" "{child}.kicad_sch"'
                    f' (at {x} {y + 17} 0)'
                    ' (effects (font (size 1.27 1.27)) (justify left top)))'
                    f' (instances (project "{NAME}" (path "/{ROOT_ID}"'
                    f' (page "{i + 2}")))))')
        if page == 'power':
            for i, net in enumerate(['3V3', 'GND', '3V3_A', 'AGND']):
                p = dict(symbol=FLAG, value='PWR_FLAG', footprint='', nets={'1': net})
                body.append(instance(f'#FLG0{i + 1}', p, 265 + i * 35, 150, 1, path))
            body.append(text('20 mA/ch; one LED at a time. BLANK pulled high during reset.', 20, 20))
            body.append(text('TIA: PD cathode at virtual ground, anode at AGND; output rises with light.', 20, 28))
        elif page in {'left', 'right'}:
            body.append(text(f'{page.upper()} EYE - 8 optical cells / 8 independent TIAs', 20, 16, 2))
            body.append(text('Receive opposite cell: 1->5, 2->6, 3->7, 4->8 (and reverse).', 20, 23))
        else:
            body.append(text('IR GLASSES EVT A - ' + page.upper(), 20, 18, 2))
        header = (
            '(kicad_sch (version 20250114) (generator "eeschema")'
            f' (uuid "{page_id}") (paper "A3")'
            f' (title_block (title "IR Glasses - {page}") (date "2026-09-06")'
            ' (rev "EVT A") (company "cc_glasses")'
            ' (comment 1 "Prototype - mechanical and optical validation required"))'
            f' (lib_symbols {embedded_library})')
        fname = NAME if page == 'control' else page
        (ROOT / f'{fname}.kicad_sch').write_text(
            header + '\n'.join(body) + '\n(embedded_fonts no))', encoding='utf-8')


def mm(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))


def custom_footprints():
    folder = ROOT / 'IR_Glasses.pretty'
    folder.mkdir(exist_ok=True)
    for name, pads, body in [
        ('Everlight_IR11_21C', [('1', 1.25, 0, .9, 1.3),
                              ('2', -1.25, 0, .9, 1.3)], (3, 1.5)),
        ('Everlight_PD15_22B', [('1', -1.65, -.7, 1.2, 1),
                              ('4', -1.65, .7, 1.2, 1),
                              ('2', 1.65, -.7, 1.2, 1),
                              ('3', 1.65, .7, 1.2, 1)], (3.2, 2.7)),
    ]:
        fp = pcb.FOOTPRINT(None)
        fp.SetReference('REF**')
        fp.SetValue(name)
        fp.SetAttributes(pcb.FP_SMD)
        fp.SetFPID(pcb.LIB_ID('IR_Glasses', name))
        for num, x, y, w, h in pads:
            pad = pcb.PAD(fp)
            pad.SetNumber(num)
            pad.SetShape(pcb.PAD_SHAPE_RECT)
            pad.SetAttribute(pcb.PAD_ATTRIB_SMD)
            layers = pcb.LSET()
            for layer in (pcb.F_Cu, pcb.F_Paste, pcb.F_Mask):
                layers.AddLayer(layer)
            pad.SetLayerSet(layers)
            pad.SetPosition(mm(x, y))
            pad.SetSize(mm(w, h))
            fp.Add(pad)
        for layer, dx, dy in [(pcb.F_Fab, body[0] / 2, body[1] / 2),
                              (pcb.F_CrtYd, max(x[1] + x[3] / 2 for x in pads) + .25,
                               max(body[1] / 2, max(x[2] + x[4] / 2 for x in pads)) + .25)]:
            shape = pcb.PCB_SHAPE(fp)
            shape.SetShape(pcb.SHAPE_T_RECT)
            shape.SetStart(mm(-dx, -dy))
            shape.SetEnd(mm(dx, dy))
            shape.SetLayer(layer)
            shape.SetWidth(pcb.FromMM(.05))
            fp.Add(shape)
        pcb.PCB_IO_KICAD_SEXPR().FootprintSave(str(folder), fp)
    (ROOT / 'fp-lib-table').write_text(
        '(fp_lib_table (version 7) (lib (name "IR_Glasses")'
        ' (type "KiCad") (uri "${KIPRJMOD}/IR_Glasses.pretty")'
        ' (options "") (descr "Everlight datasheet land patterns")))')


def make_board():
    board = pcb.BOARD()
    board.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.6))
    board.SetCopperLayerCount(2)
    all_nets = sorted({n for p in PARTS.values() for n in p['nets'].values()})
    nets = {}
    for n in all_nets:
        net = pcb.NETINFO_ITEM(board, n)
        board.Add(net)
        nets[n] = net
    for ref, part in PARTS.items():
        lib, name = part['footprint'].split(':')
        folder = ROOT / f'{lib}.pretty' if lib == 'IR_Glasses' else LIB / 'footprints' / f'{lib}.pretty'
        fp = pcb.PCB_IO_KICAD_SEXPR().FootprintLoad(str(folder), name)
        if fp is None:
            raise ValueError(part['footprint'])
        fp.SetReference(ref)
        fp.SetValue(part['value'])
        fp.SetFPID(pcb.LIB_ID(lib, name))
        fp.SetPosition(mm(110 + part['xy'][0], 85 + part['xy'][1]))
        fp.SetOrientationDegrees(part['angle'])
        path = pcb.KIID_PATH()
        path.push_back(pcb.KIID(ROOT_ID))
        if part['page'] != 'control':
            path.push_back(pcb.KIID(uid('sheet/' + part['page'])))
        path.push_back(pcb.KIID(uid(f'{ref}/1')))
        fp.SetPath(path)
        fp.Reference().SetLayer(pcb.F_Fab)
        fp.Reference().SetTextSize(mm(.8, .8))
        fp.Reference().SetTextThickness(pcb.FromMM(.1))
        fp.Value().SetVisible(False)
        for pad in fp.Pads():
            n = part['nets'].get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
        board.Add(fp)
    geometry = json.loads((ROOT.parent / 'tools' / 'geometry.json').read_text())
    for loop in [geometry['outer'], *geometry['holes']]:
        for a, b in zip(loop, loop[1:]):
            line = pcb.PCB_SHAPE()
            line.SetShape(pcb.SHAPE_T_SEGMENT)
            line.SetStart(mm(110 + a[0], 85 + a[1]))
            line.SetEnd(mm(110 + b[0], 85 + b[1]))
            line.SetLayer(pcb.Edge_Cuts)
            line.SetWidth(pcb.FromMM(.05))
            board.Add(line)
    for value, xy in [('IR GLASSES / EVT A', (-62, -37)),
                       ('3V3 ONLY', (55, -37)), ('EYE-FACING SIDE', (-15, 36))]:
        label = pcb.PCB_TEXT(board)
        label.SetText(value)
        label.SetPosition(mm(110 + xy[0], 85 + xy[1]))
        label.SetTextSize(mm(1, 1))
        label.SetTextThickness(pcb.FromMM(.15))
        label.SetLayer(pcb.F_SilkS)
        board.Add(label)
    pcb.SaveBoard(str(ROOT / f'{NAME}.kicad_pcb'), board)
    print('Parts:', len(PARTS), 'Nets:', len(nets), flush=True)


if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    custom_footprints()
    for part in PARTS.values():
        lib, name = part['footprint'].split(':')
        if lib != 'IR_Glasses':
            source = LIB / 'footprints' / f'{lib}.pretty' / f'{name}.kicad_mod'
            shutil.copy2(source, ROOT / 'IR_Glasses.pretty' / source.name)
            part['footprint'] = 'IR_Glasses:' + name
    make_schematics()
    make_board()
    (ROOT / 'parts.json').write_text(json.dumps(PARTS, indent=2), encoding='utf-8')

