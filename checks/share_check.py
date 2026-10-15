#MC 2026-10-15 fetches each link the way X, Telegram, Facebook, Discord and WhatsApp do (their own user agents, from
#   outside the site's network), finds the preview picture in the page, and fetches that too. Writes one line per link
#   and app to checks/share-result.txt so a share card that only breaks for the apps shows up.
import re, sys, time, struct, urllib.request, html
UAS = {'x': 'Twitterbot/1.0', 'tg': 'TelegramBot (like TwitterBot)', 'fb': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
       'dc': 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)', 'wa': 'WhatsApp/2.23.20.0'}
def get(url, ua):
    t = time.time()
    req = urllib.request.Request(url, headers={'User-Agent': ua, 'Accept': '*/*'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            b = r.read(); return r.status, r.headers.get('content-type', ''), b, round(time.time() - t, 2), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type', ''), e.read()[:300], round(time.time() - t, 2), url
    except Exception as e:
        return 0, str(e)[:80], b'', round(time.time() - t, 2), url
def dims(b):
    if b[:8] == b'\x89PNG\r\n\x1a\n': return '%dx%d' % struct.unpack('>II', b[16:24])
    if b[:2] == b'\xff\xd8':
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF: i += 1; continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2): h, w = struct.unpack('>HH', b[i + 5:i + 9]); return '%dx%d' % (w, h)
            i += 2 + struct.unpack('>H', b[i + 2:i + 4])[0]
    return '?'
out = []
for line in open('checks/share-urls.txt'):
    u = line.strip()
    if not u or u.startswith('#'): continue
    for k, ua in UAS.items():
        st, ct, b, s, final = get(u, ua)
        txt = b.decode('utf-8', 'replace') if 'html' in ct else ''
        m = re.search(r'<meta property="og:image" content="([^"]*)"', txt)
        tw = re.search(r'<meta name="twitter:image" content="([^"]*)"', txt)
        img = html.unescape(m.group(1)) if m else ''
        row = '%s %s page %s %.2fs %s' % (k, u, st, s, ('final ' + final) if final != u else '')
        if not img: row += ' NO-OG-IMAGE'
        else:
            ist, ict, ib, isec, _ = get(img, ua)
            row += ' | img %s %s %dkb %s %.2fs %s' % (ist, ict.split(';')[0], len(ib) // 1024, dims(ib) if ist == 200 else '', isec, img[-70:])
            if tw and html.unescape(tw.group(1)) != img: row += ' TW-IMAGE-DIFFERS'
        out.append(row)
open('checks/share-result.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
