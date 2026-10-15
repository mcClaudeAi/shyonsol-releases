#MC 2026-10-15 the middle of three Lighthouse runs, one line
import json, sys
rs = []
for i in (1, 2, 3):
    try: rs.append(json.load(open('/tmp/r%d.json' % i)))
    except Exception: pass
if not rs:
    print(sys.argv[1], 'no result'); sys.exit(0)
rs.sort(key=lambda r: r['categories']['performance']['score'] or 0)
r = rs[len(rs) // 2]; a = r['audits']
print(sys.argv[1], 'score', round((r['categories']['performance']['score'] or 0) * 100), '| FCP', a['first-contentful-paint']['displayValue'], '| LCP', a['largest-contentful-paint']['displayValue'],
      '| TBT', a['total-blocking-time']['displayValue'], '| CLS', a['cumulative-layout-shift']['displayValue'], '| SI', a['speed-index']['displayValue'], '| all', [round((x['categories']['performance']['score'] or 0) * 100) for x in rs])
