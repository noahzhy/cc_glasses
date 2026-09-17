# 工具使用范围

主工程中的 PCB 是布线权威文件。`build_e6.py`、`build_pcb.py`、`place_e6.py` 为初始工程/布局生成器，**重新运行会覆盖设计内容或布线**，只可在另存副本中使用；它们不是已布线工程的一键构建命令。

发布检查顺序：更新原理图 netlist → `sync_placement.py` → `validate_design.py` → KiCad ERC/裸板 DRC（重新铺铜、原理图一致性）→ `validate_via_assembly.py`（KiCad Python）→ `build_carrier.py` → `localize_carrier_fixtures.py` → 载框 DRC → `validate_carrier.py` → `export_manufacturing.py` → `validate_manufacturing.py` → PDF/CAM 人工视觉复核 → `finalize_release.py`。

`design_validation.json` 只证明网络表、几何及接口参考模型，不能替代 PCB 物理连通性 DRC 或首板测试。`visual_review.json` 必须由真实视觉复核产生，不能自动视为通过。

需要 KiCad 10 pcbnew Python 和 kicad-cli；普通 Python 依赖 sexpdata、shapely、numpy、Pillow、reportlab、gerbonara。PCB 编辑工具通过 KiCad 自带 Python 运行，其他脚本使用普通 Python。`export_manufacturing.py` 可通过环境变量 KICAD_CLI 指定 CLI 路径。

历史比对脚本需要同级原始 E4 工程和 `source_hashes.json` 所记录的基线；打开、检查和生产 E6 工程使用包内本地库，不依赖 E4 库。

P3模拟验证：`simulate_tlv9062.py`使用ngspice 47 PSpice兼容模式和包内TI模型，生成环路/瞬态/噪声证据；`validate_analog.py`在最终PCB检查后刷新板哈希并检查仿真目标。噪声验收和首板实测不能由该脚本判定通过。
