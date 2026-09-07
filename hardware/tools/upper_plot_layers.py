from pathlib import Path
p=Path('hardware/tools/upper_driver_plot.py')
s=p.read_text().replace('plt.subplots(1, 2, figsize=(14, 7))','plt.subplots(2, 2, figsize=(14, 14))').replace('zip([3, 0], axes)', 'zip([3, 0, 1, 2], axes.flat)')
p.write_text(s)
