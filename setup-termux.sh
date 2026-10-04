#!/data/data/com.termux/files/usr/bin/bash
# ALTRA Helper: إعداد تلقائي على أندرويد (Termux)
set -e
BASE="https://danial56hd-wq.github.io/ALTRA-DAWNLOADER"

echo "▶ تثبيت الحزم (python, ffmpeg, nodejs)…"
pkg update -y
pkg install -y python ffmpeg nodejs curl

echo "▶ تثبيت yt-dlp…"
python -m pip install -U "yt-dlp[default]"

echo "▶ تنزيل ملفات ALTRA…"
mkdir -p "$HOME/altra"
cd "$HOME/altra"
for f in altra-server.py index.html sw.js manifest.webmanifest icon-192.png icon-512.png; do
  curl -fsSL -o "$f" "$BASE/$f"
  echo "   ✓ $f"
done

grep -q "alias altra=" "$HOME/.bashrc" 2>/dev/null || \
  echo "alias altra='cd \$HOME/altra && python altra-server.py'" >> "$HOME/.bashrc"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true

echo
echo "✅ جاهز. في المرات القادمة اكتب فقط:  altra"
echo "   ثم افتح ALTRA أو http://localhost:8787"
echo
exec python altra-server.py
