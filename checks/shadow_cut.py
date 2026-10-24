#MC 2026-10-24 Living Shadows, part 1: each Shytoshi Shadow cut out of its background once, so the game can lift the
#   figure off its square and animate it playing a card (assets/shadowplay.js). Runs on GitHub's machines because the
#   art lives on pinit.io and the cutting model needs real CPU; the site never does this work.
#   sample mode: python3 shadow_cut.py sample  (reads checks/cut-sample.txt "n aura url", writes checks/cut-sample/)
#   live mode:   python3 shadow_cut.py live    (asks shyonsol.io which Shadows still need a cut, uploads each one)
#   For each Shadow it keeps: the cutout (webp with transparency), the hoodie colour (the rig's arms are dressed in it)
#   and where the shoulders end, so the arms attach at the right place.
import sys, os, io, json, hmac, hashlib, time, urllib.request, urllib.parse
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from rembg import remove, new_session

SESS = new_session('isnet-general-use')
UA = {'User-Agent': 'Mozilla/5.0 (shyonsol shadow cut)'}

def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=dict(UA, **(headers or {})))
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def cut(raw):
    im = Image.open(io.BytesIO(raw)).convert('RGB').resize((768, 768), Image.LANCZOS)
    out = remove(im, session=SESS, post_process_mask=True)
    al = np.array(out)[:, :, 3]
    # tidy the mask: keep the figure and anything big touching it (drop stray sparks, coins and specks), and fill
    # anything the figure encloses, so a white or patterned mask inside the hood never gets cut out as background
    solid = al > 100
    lab, k = ndimage.label(solid)
    if k:
        sizes = ndimage.sum(solid, lab, range(1, k + 1)); big = sizes.max()
        keep = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v >= big * .06])
        keep = ndimage.binary_fill_holes(keep)
        soft = ndimage.binary_dilation(keep, iterations=2)
        al = np.where(keep, np.maximum(al, 255), np.where(soft, al, 0)).astype(np.uint8)
    out = Image.fromarray(np.dstack([np.array(im), al]), 'RGBA')
    a = np.array(out)
    ys, xs = np.where(al > 40)
    if len(xs) < 2000:
        raise ValueError('nothing cut out')
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out = out.crop((x0, y0, x1, y1))
    b = np.array(out); h, w = b.shape[:2]
    # the hoodie: the colour of the outer band of the figure (hood sides and shoulders), below the top third, so the
    # mask and goggles in the middle never decide it
    m = b[:, :, 3] > 200
    band = m & ~ndimage.binary_erosion(m, iterations=max(4, w // 14))
    band[: h // 3, :] = False
    px = b[band][:, :3]
    if len(px) < 200:
        reg = b[int(h * .8):, :, :]; px = reg[reg[:, :, 3] > 200][:, :3]
    col = np.median(px, axis=0) if len(px) else np.array([40, 40, 48])
    dark = np.percentile(px, 20, axis=0) if len(px) else col * .6
    # the shoulders: how far the figure reaches left and right, 90% of the way down
    row = b[int(h * .9), :, 3] > 120
    xs2 = np.where(row)[0]
    sl, sr = (xs2.min() / w, xs2.max() / w) if len(xs2) else (.1, .9)
    if out.height > 640:
        out = out.resize((int(out.width * 640 / out.height), 640), Image.LANCZOS)
    buf = io.BytesIO(); out.save(buf, 'WEBP', quality=86, method=6)
    hx = lambda c: '#%02x%02x%02x' % tuple(int(v) for v in c)
    return buf.getvalue(), {'col': hx(col), 'dark': hx(dark), 'sl': round(float(sl), 3), 'sr': round(float(sr), 3), 'ar': round(out.width / out.height, 4)}, out

def sample():
    here = os.path.dirname(os.path.abspath(__file__)); od = os.path.join(here, 'cut-sample'); os.makedirs(od, exist_ok=True)
    rows = [l.split() for l in open(os.path.join(here, 'cut-sample.txt')) if l.strip()]
    info = {}; tiles = []
    for r in rows:
        n, url = r[0], r[-1]
        try:
            data, meta, im = cut(get(url))
            open(os.path.join(od, n + '.webp'), 'wb').write(data); info[n] = meta; tiles.append((n, im, meta))
            print('cut', n, meta, len(data))
        except Exception as e:
            print('FAIL', n, e)
    json.dump(info, open(os.path.join(od, 'info.json'), 'w'), indent=1)
    # a contact sheet to look at: each cutout on a dark table with its hoodie colour beside it
    W = 6; cw, ch = 220, 260
    sheet = Image.new('RGB', (cw * W, ch * ((len(tiles) + W - 1) // W)), (18, 12, 36))
    for i, (n, im, meta) in enumerate(tiles):
        t = im.copy(); t.thumbnail((cw - 20, ch - 40))
        x, y = (i % W) * cw, (i // W) * ch
        sheet.paste(t, (x + (cw - t.width) // 2, y + 10), t)
        d = ImageDraw.Draw(sheet); d.rectangle((x + 10, y + ch - 26, x + 40, y + ch - 8), fill=meta['col']); d.text((x + 50, y + ch - 24), '#' + n, fill=(240, 236, 250))
    sheet.save(os.path.join(od, 'sheet.jpg'), quality=85)

def curl(args):
    # Hostinger's CDN answers unknown callers with a 307 back to itself and a cookie check, the same thing the deploy
    # job works around: keep its cookie and follow the redirect
    import subprocess
    return subprocess.run(['curl', '-s', '-L', '--max-redirs', '5', '-c', '/tmp/cj', '-b', '/tmp/cj', '-A', UA['User-Agent']] + args, capture_output=True, timeout=120).stdout

def live():
    key = os.environ.get('DEPLOY_KEY', '')
    if not key: print('no key'); return
    k = hmac.new(key.encode(), b'shadow-cut', hashlib.sha256).hexdigest()
    base = 'https://shyonsol.io/api/shadowcut.php'
    raw = curl([base + '?a=todo&k=' + k])
    try: todo = json.loads(raw)
    except Exception: print('todo said', raw[:300]); return
    rows = todo.get('rows', []); print('to cut:', len(rows))
    for r in rows[:300]:
        try:
            data, meta, _ = cut(get(r['img']))
            open('/tmp/cut.webp', 'wb').write(data)
            print(r['n'], curl(['-F', 'a=put', '-F', 'k=' + k, '-F', 'n=' + r['n'], '-F', 'meta=' + json.dumps(meta), '-F', 'img=@/tmp/cut.webp;type=image/webp', base])[:120])
        except Exception as e:
            print('FAIL', r.get('n'), e)

if __name__ == '__main__':
    (sample if sys.argv[1:] == ['sample'] else live)()
