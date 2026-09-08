"""Export a PCB import copy with plain package fields and embedded geometry."""

import ast
import hashlib
import json
import re
import shutil
from pathlib import Path


ROOT = Path("hardware/ir_glasses/EVT_E3")
OUT = ROOT.parent / "EVT_E3_JLC_IMPORT"
tree = ast.parse(Path("hardware/tools/e3_bom.py").read_text(encoding="utf-8"))
packages = next(
    ast.literal_eval(node.value)
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "PACKAGES" for t in node.targets)
)
OUT.mkdir(exist_ok=True)
sources = [
    *ROOT.glob("*.kicad_sch"),
    ROOT / "ir_glasses.kicad_pcb",
    ROOT / "ir_glasses.kicad_pro",
    ROOT / "IR_Glasses.kicad_sym",
    ROOT / "sym-lib-table",
    ROOT / "netlist.xml",
]
board_text = (ROOT / "ir_glasses.kicad_pcb").read_text(encoding="utf-8")
ids = set(re.findall(r'\(footprint\s+"([^"]+)"', board_text))
mapping = {
    old: packages.get(old.split(":")[-1], old.split(":")[-1]) for old in ids
}
mapping.update({
    old: "TC2050" if "Tag-Connect" in old else "TestPoint"
    for old in ids if "Tag-Connect" in old or "TestPoint" in old
})
changes = {}
for source in sources:
    text = source.read_text(encoding="utf-8")
    original = text
    for old, short in mapping.items():
        text = re.sub(
            r'(\(footprint\s+|\(property\s+"Footprint"\s+)"'
            + re.escape(old) + r'"',
            lambda match: match[1] + f'"{short}"',
            text,
        )
        text = text.replace(f">{old}<", f">{short}<")
    text = re.sub(
        r'(\(property\s+"Footprint"\s+)"([^"]*)"',
        lambda match: match[1] + '"' + packages.get(
            match[2].split(":")[-1], match[2].split(":")[-1]
        ) + '"',
        text,
    )
    text = text.replace("C16745", "C19269752")
    target = OUT / source.name
    target.write_text(text, encoding="utf-8")
    changes[source.name] = {
        "source_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "import_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
models = set(re.findall(r'\(model\s+"\$\{KIPRJMOD\}/([^"]+)"', board_text))
for name in models:
    destination = OUT / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, destination)
for name, source in {
    "BOM.csv": ROOT / "material_freeze/bom_smt_all.csv",
    "CPL.csv": ROOT / "manufacturing/positions_jlc.csv",
}.items():
    shutil.copy2(source, OUT / name)
result = (OUT / "ir_glasses.kicad_pcb").read_text(encoding="utf-8")
assert all(":" not in item for item in re.findall(
    r'\(footprint\s+"([^"]+)"', result
))
for source in OUT.glob("*.kicad_sch"):
    assert all(":" not in item for item in re.findall(
        r'\(property\s+"Footprint"\s+"([^"]*)"',
        source.read_text(encoding="utf-8"),
    ))
(OUT / "import_changes.json").write_text(
    json.dumps(changes, indent=2), encoding="utf-8"
)
(OUT / "README.md").write_text(
    "# 嘉立创工程导入版\n\n"
    "导入本目录的 ir_glasses.kicad_pcb；其真实封装字段已使用简短规格，"
    "不是仅修改 BOM。原理图 Footprint 同步修改，焊盘和布线保留。\n\n"
    "这是制造导入副本，封装无库前缀，使用 PCB 内嵌的完整几何；"
    "不要对本副本执行从库更新封装。0402/0603/1206 等同名规格可以"
    "对应不同器件的独立内嵌焊盘，不能按名称相互替换。\n\n"
    "持续编辑请使用随包的 KiCad 原生工程，其中库关联完整保留。"
    "IR LED 采购编码为 C19269752。平台最终匹配和贴装方向仍须审核。\n",
    encoding="utf-8",
)
print(f"Exported {len(ids)} footprint IDs to {OUT}")
