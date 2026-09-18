from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[1]
for p in R.glob('*.kicad_sch'):
 t=p.read_text().replace('DUAL SIMULTANEOUS 16-BIT ACQUISITION','F302 DUAL SIMULTANEOUS 12-BIT ACQUISITION').replace('Receive opposite cell: 1->5, 2->6, 3->7, 4->8 (and reverse).','Sample the two adjacent PDs: see led_pd_mapping.csv; odd to ADC1, even to ADC2.')
 p.write_text(t)
old=(R.parent/'ir_glasses_EVT_E6/firmware_interface.h').read_text()
old=old.replace('EVT_E6_INTERFACE_H','EVT_E6_F302_INTERFACE_H').replace('#define EVT_E6_SPI_SCLK_HZ 3000000u','#define EVT_E6_ADC_CLOCK_HZ 12000000u\n#define EVT_E6_ADC_MAX_CODE 4095u').replace('#define EVT_E6_SLOT_US 1250u','#define EVT_E6_DEFAULT_FPS 30u\n#define EVT_E6_MIN_FPS 24u\n#define EVT_E6_TIM2_ARR_30FPS 99999u\n#define EVT_E6_TIM2_ARR_24FPS 124999u').replace('0xE6','0xE7').replace('EVT_E6_FAULT_SPI','EVT_E6_FAULT_ADC').replace('EVT_E6_FAULT_PIPELINE','EVT_E6_FAULT_MISSING_SAMPLE').replace('actual light-sample edge','light-sample trigger time').replace('/* offset 24 */','/* offset 24, 0..4095 */').replace('/* offset 26 */','/* offset 26, 0..4095 */').replace('/* offset 28 */','/* offset 28, 0..4095 */').replace('/* offset 30 */','/* offset 30, 0..4095 */')
(R/'firmware_interface.h').write_text(old)
checks=[
('P01','采购','核对STM32F302CCT6实物型号、修订号、库存及批次；不得替代为单ADC型号'),
('P02','电源','限流上电；量测3V3、3V3_A、纹波、静态电流；确认无过热'),
('P03','启动','BOOT0下拉、复位和SWD可连接；复位全程LED灭灯'),
('P04','ADC','分别校准ADC1/ADC2；同一已知直流输入检查码值、偏置、增益与VDDA'),
('P05','同步','同一个快速变化信号输入两路；示波器/码值确认双ADC窗口对齐，禁止软件顺序启动'),
('P06','映射','逐个扫描16LED，核对led_pd_mapping.csv的两个相邻PD及奇偶A/B顺序'),
('P07','时序','同时观察LED电流、TIM触发标记和ADC输入；两次触发100/250us，LED请求200～300us'),
('P08','建立','最坏MUX满幅切换、50us亮态等待；实际采样误差目标小于VDDA/8192'),
('P09','串扰','单路强光另一暗态、左右侧轮换；记录串扰及地/电源耦合'),
('P10','背景','暗值与亮值同步配对；差分保留负值；测环境光变化和背景扣除效果'),
('P11','饱和','扫描到上下轨，测实际有效输入范围、饱和恢复及不会误配下一个时隙'),
('P12','噪声','记录两路暗/亮态原始序列、标准差、频谱、参考电源纹波；建立应用验收阈值'),
('P13','帧率','30fps及24fps各连续运行至少30分钟；计数丢帧、DMA/ADC溢出和样本错配'),
('P14','故障','ADC/DMA错误、缺样、非法配置立即灭灯，清有效位，禁止继续发光'),
('P15','停机','CPU在点灯期间暂停/死循环；示波器测独立硬件关断，不依赖调试器冻结定时器'),
('P16','温度','覆盖预期工作电压/温度及多块样板，复核偏置、噪声、LED电流和建立裕量'),
('P17','贴片','对照CPL与Pin1/极性，检查J1方向、全部光学器件方向、焊桥和空焊'),
('P18','保护','验证输入限流、过压监控、反接及断电行为；遵循限流测试条件')]
with (R/'first_board_tests.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['ID','Category','Test','Status','Measured result']);w.writerows([*r,'PENDING',''] for r in checks)
print('Interface and',len(checks),'pending bench checks generated')
