#!/bin/bash
#MC 2026-10-15 Lighthouse on a simulated phone for each link in checks/speed-urls.txt, three runs each, the middle kept.
#   Errors go into the result too, so a failed run says why.
set +e
OUT=checks/speed-result.txt
echo "# $(date -u +%FT%TZ) $(tail -1 checks/speed-urls.txt)" > $OUT
CP=$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser)
echo "# chrome: $CP" >> $OUT
for u in $(grep -v '^#' checks/speed-urls.txt); do
  for i in 1 2 3; do
    rm -f /tmp/r$i.json
    CHROME_PATH="$CP" lighthouse "$u" --only-categories=performance --chrome-flags="--headless=new --no-sandbox" --output=json --output-path=/tmp/r$i.json --quiet 2>/tmp/err$i.txt || echo "# run $i failed: $(tail -c 300 /tmp/err$i.txt | tr '\n' ' ')" >> $OUT
  done
  python3 checks/speed_report.py "$u" >> $OUT
done
cat $OUT
exit 0
