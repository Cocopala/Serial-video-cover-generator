"""打包生成器：catalog.json + assets/ + 模板 → 封面生成器.html + data/。

图片不再内嵌进 HTML。每张底图生成两个按需加载的脚本（file:// 下也能用，且不会污染 canvas）：
  data/thumb/<id>.js  页面缩略图（高 540 的 JPG）
  data/full/<id>.js   下载时才加载的原图
HTML 与 data/ 必须放在同一目录。

用法：python -X utf8 build.py [--catalog catalog.json] [--assets assets] [--out 封面生成器.html]
"""
from pathlib import Path
import argparse, base64, hashlib, io, json, struct, sys

try:
    from PIL import Image
except ImportError:
    sys.exit('需要 Pillow：python -m pip install Pillow')

root = Path(__file__).parent
RATIOS = {'16:9': 16 / 9, '4:3': 4 / 3}
THUMB_HEIGHT, THUMB_QUALITY = 540, 85

ap = argparse.ArgumentParser()
ap.add_argument('--catalog', default=root / 'catalog.json', type=Path)
ap.add_argument('--assets', default=root / 'assets', type=Path)
ap.add_argument('--out', default=root / '封面生成器.html', type=Path)
args = ap.parse_args()


def png_size(path):
    head = path.read_bytes()[:24]
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        sys.exit(f'不是 PNG：{path}')
    return struct.unpack('>II', head[16:24])


def check_catalog(catalog):
    used = set()
    for series in catalog['series']:
        seen = set()
        for entry in series['entries']:
            where = f"{series['id']}/{entry.get('id')}"
            if not entry.get('id') or entry['id'] in seen:
                sys.exit(f'款式 id 为空或重复：{where}')
            seen.add(entry['id'])
            if entry.get('renderer') == 'legacy':
                if not (args.assets / entry['asset']).exists():
                    sys.exit(f"缺少素材：{args.assets / entry['asset']}（{where}）")
                used.add(entry['asset'])
                continue
            covers = entry.get('covers') or {}
            if not covers or set(covers) - set(RATIOS):
                sys.exit(f'covers 只能是 16:9 / 4:3：{where}')
            for ratio, cover in covers.items():
                path = args.assets / cover['asset']
                if not path.exists():
                    sys.exit(f'缺少素材：{path}（{where} {ratio}）')
                w, h = png_size(path)
                if abs(w / h - RATIOS[ratio]) > 0.06:
                    sys.exit(f'{where} {ratio} 素材比例不对：{w}x{h}')
                n = cover.get('number') or {}
                for key in ('x', 'y', 'fontSize', 'maxWidth'):
                    if not isinstance(n.get(key), (int, float)):
                        sys.exit(f'{where} {ratio} 缺少编号定位 number.{key}')
                if not (0 <= n['x'] <= w and 0 <= n['y'] <= h):
                    sys.exit(f'{where} {ratio} 编号坐标超出图片 {w}x{h}')
                used.add(cover['asset'])
    return used


def write_js(path, kind, asset_id, data_url):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'__assetLoaded("{kind}","{asset_id}","{data_url}");', encoding='utf-8')


catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
used = check_catalog(catalog)
out_dir = args.out.parent
manifest, written = {}, 0
for name in sorted(used):
    raw = (args.assets / name).read_bytes()
    asset_id = hashlib.sha256(raw).hexdigest()[:16]  # 文件名即内容哈希：已存在就不必重写
    w, h = png_size(args.assets / name)
    manifest[name] = {'id': asset_id, 'w': w, 'h': h}
    full = out_dir / 'data' / 'full' / f'{asset_id}.js'
    thumb = out_dir / 'data' / 'thumb' / f'{asset_id}.js'
    if not full.exists():
        write_js(full, 'full', asset_id, 'data:image/png;base64,' + base64.b64encode(raw).decode())
        written += 1
    if not thumb.exists():
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        im = im.resize((round(w * THUMB_HEIGHT / h), THUMB_HEIGHT), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=THUMB_QUALITY, optimize=True)
        write_js(thumb, 'thumb', asset_id, 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode())
        written += 1

html = (root / 'studio.template.html').read_text(encoding='utf-8')
html = html.replace('__CATALOG_JSON__', json.dumps(catalog['series'], ensure_ascii=False))
html = html.replace('__MANIFEST_JSON__', json.dumps(manifest, ensure_ascii=False))
html = html.replace('__LEGACY_RENDERER__', (root / 'legacy-render.js').read_text(encoding='utf-8'))
args.out.write_text(html, encoding='utf-8')
counts = ', '.join(f"{s['id']}={len(s['entries'])}" for s in catalog['series'])
print('Built', args.out, args.out.stat().st_size, 'bytes;', counts, f'; new data files: {written}')
