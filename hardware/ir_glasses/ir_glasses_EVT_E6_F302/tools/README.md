# 检查与导出工具

交付工程、库、模型和CAM可独立使用。Python检查脚本需要sexpdata、gerbonara；模拟需要numpy/ngspice，PDF示意需要reportlab。via_assembly检查使用本机KiCad pcbnew Python。KiCad CLI路径在脚本中按本机安装配置，换机需调整。

- export_manufacturing.py：先由release_gate.py run重新检查ERC、主板/载框DRC并绑定设计输入哈希；导出和打包时自动拒绝过期证据。release_gate.py selftest验证修改/缺失输入的拒绝路径。
- validate_manufacturing.py / validate_via_assembly.py / validate_bom.py：对CAM、CPL、本地库、近孔间距和价格公式核验。
- validate_design.py / validate_carrier.py：对照上级目录原P3工程；离线独立解压包无P3时不能运行这两项比较，已完成结果及基准哈希随包交付。
- simulate_frontend.py：TI典型模型与敏感度分析，不能替代首板。
- draw_assembly.py：使用项目中的实际KiCad渲染PNG和坐标生成4页装配PDF。

实验性布线与中间修改脚本不属于发布包。固件头文件只定义接口，不能烧录。
