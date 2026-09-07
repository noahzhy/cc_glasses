import hashlib
import zipfile
from pathlib import Path
p=Path('hardware/ir_glasses/ir_glasses_EVT_D.zip')
with zipfile.ZipFile(p) as z:
    lines=z.read('EVT_D/SHA256SUMS.txt').decode().splitlines()
    for line in lines:
        digest,name=line.split('  ',1)
        assert hashlib.sha256(z.read('EVT_D/'+name)).hexdigest()==digest
print('Verified archive checksums:',len(lines))
