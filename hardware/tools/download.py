from pathlib import Path
import requests
import zipfile

root = Path('hardware/tools')
s = requests.Session()
for repo, match, dest in [
    ('freerouting/freerouting', '.jar', 'freerouting.jar'),
    ('adoptium/temurin25-binaries', 'jre_x64_windows_hotspot', 'java.zip'),
]:
    data = s.get(f'https://api.github.com/repos/{repo}/releases/latest',
                 timeout=30).json()
    asset = next(a for a in data['assets'] if match in a['name']
                 and a['name'].endswith(('.jar', '.zip')))
    r = s.get(asset['url'] + '?download=1',
              headers={'Accept': 'application/octet-stream'}, timeout=45)
    r.raise_for_status()
    print(dest, r.headers.get('Content-Type'), len(r.content), flush=True)
    (root / dest).write_bytes(r.content)
with zipfile.ZipFile(root / 'java.zip') as archive:
    archive.extractall(root / 'java')
