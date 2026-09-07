from pathlib import Path
p=Path('hardware/tools/upper_finish_signals.py'); s=p.read_text(); a=s.index('for net in ['); b=s.index(']:',a); s=s[:a]+'for net in ["LED_LAT", "LED_K9", "I2C_SDA", "IMU_INT", "3V3_A", "I2C_SCL"'+s[b:]; p.write_text(s)
p=Path('hardware/tools/upper_finish_ground.py'); s=p.read_text().replace('["AGND"] * 5]:','["AGND"] * 5:'); p.write_text(s)
