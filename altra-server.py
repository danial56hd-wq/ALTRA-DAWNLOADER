#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALTRA Helper  ·  المساعد المحلي لتطبيق ALTRA-DAWNLOADER

يشغّل yt-dlp على جهازك ويقدّم للتطبيق واجهة صغيرة (HTTP) لتحميل الفيديو والصوت
من أكثر من ألف موقع (يوتيوب، إنستغرام، تيك توك، فيسبوك، X، ريديت، ...).
كما يقدّم ملفات التطبيق نفسه، فيمكن فتح  http://localhost:8787  وتثبيته مباشرة.

التشغيل:
    python altra-server.py                 # المنفذ 8787، على هذا الجهاز فقط
    python altra-server.py --port 9000
    python altra-server.py --host 0.0.0.0  # للسماح لأجهزة الشبكة المحلية
    python altra-server.py --cookies cookies.txt

المتطلبات:  Python 3.8+  و  yt-dlp  (pip install -U "yt-dlp[default]")  و  ffmpeg (اختياري، للدمج والتحويل)
"""
import argparse
import glob
import json
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlparse

VERSION = "7.3"
HERE = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

# ── yt-dlp: مثبّت عبر pip، أو ملف yt-dlp (zipapp) بجوار هذا الملف ──────────────
yt_dlp = None
try:
    import yt_dlp  # type: ignore
except ImportError:
    for cand in (os.environ.get("YTDLP_PATH", ""), os.path.join(HERE, "yt-dlp")):
        if cand and os.path.isfile(cand):
            sys.path.insert(0, cand)
            try:
                import yt_dlp  # type: ignore
                break
            except ImportError:
                sys.path.remove(cand)

AUDIO_FORMATS = {"mp3", "ogg", "opus", "wav", "m4a", "flac", "aac"}
VIDEO_FORMATS = {"mp4", "webm", "best"}
STATIC_OK = {".html", ".js", ".webmanifest", ".png", ".json", ".css", ".svg", ".ico"}
DEFAULT_ORIGINS = {"https://danial56hd-wq.github.io"}

CFG = {
    "cache": os.path.join(tempfile.gettempdir(), "altra-cache"),
    "cookies": None,
    "browser": None,
    "keep": 60,
    "origins": set(DEFAULT_ORIGINS),
    "allow_all": False,
    "loopback": True,
    "has_ffmpeg": bool(shutil.which("ffmpeg")),
}
JOBS = {}
JOBS_LOCK = threading.Lock()
SLOTS = threading.BoundedSemaphore(4)


class Cancelled(Exception):
    pass


class Job:
    def __init__(self, url, params):
        self.id = uuid.uuid4().hex[:16]
        self.url = url
        self.params = params
        self.state = "queued"       # queued | running | done | error | cancelled
        self.phase = "queued"
        self.progress = 0.0
        self.speed = 0
        self.eta = None
        self.bytes = 0
        self.base_bytes = 0
        self.title = ""
        self.filename = ""
        self.filepath = ""
        self.size = 0
        self.error = ""
        self.hint = ""
        self.login = False
        self.site = site_of(url)
        self.created = time.time()
        self.finished = None
        self.cancel = threading.Event()
        self.dir = os.path.join(CFG["cache"], self.id)

    def public(self):
        return {
            "id": self.id, "state": self.state, "phase": self.phase,
            "progress": round(self.progress, 1), "speed": self.speed or 0,
            "eta": self.eta, "bytes": self.bytes, "title": self.title,
            "filename": self.filename, "size": self.size,
            "error": self.error, "hint": self.hint,
            "login": self.login, "site": self.site,
        }


# ── مساعدات ────────────────────────────────────────────────────────────────
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def clean_error(msg):
    msg = ANSI.sub("", str(msg)).strip()
    msg = re.sub(r"^(ERROR:\s*)+", "", msg)
    return msg[:400]


def site_of(url):
    try:
        h = (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    for key, name in (("instagram", "instagram"), ("facebook", "facebook"), ("fb.watch", "facebook"),
                      ("youtube", "youtube"), ("youtu.be", "youtube"), ("tiktok", "tiktok"),
                      ("twitter.com", "x"), ("x.com", "x"), ("reddit", "reddit")):
        if key in h:
            return name
    return h


LOGIN_KEYS = ("login required", "sign in", "log in", "logged in", "cookies", "rate-limit",
              "empty media response", "age-restricted", "confirm you", "authentication",
              "checkpoint", "you must be", "restricted video", "private video")


NOT_LOGIN_KEYS = ("unsupported url", "name or service not known", "timed out", "urlopen error",
                  "temporary failure", "network is unreachable", "connection refused",
                  "ffmpeg", "ffprobe", "no space left", "cancel")
LOGIN_SITES = ("instagram", "facebook", "x", "tiktok")


def login_needed(msg, url):
    m = msg.lower()
    if any(k in m for k in NOT_LOGIN_KEYS):
        return False
    if any(k in m for k in LOGIN_KEYS):
        return True
    # في إنستغرام وفيسبوك وX وتيك توك أغلب حالات الفشل سببها أن المقطع يتطلب حساباً
    return site_of(url) in LOGIN_SITES


def explain(msg):
    m = msg.lower()
    if any(k in m for k in LOGIN_KEYS):
        return "هذا المحتوى يتطلب تسجيل الدخول. اضغط الشارة الزرقاء في التطبيق لاستيراد جلسة الدخول."
    if "unsupported url" in m:
        return "الرابط غير مدعوم أو لا يحتوي على فيديو."
    if "private" in m:
        return "المحتوى خاص."
    if any(k in m for k in ("name or service not known", "timed out", "urlopen error",
                            "temporary failure", "network is unreachable", "connection")):
        return "تعذّر الوصول إلى الموقع من هذا الجهاز. تحقق من الإنترنت أو شغّل VPN."
    if "http error 403" in m or "http error 429" in m:
        return "الموقع رفض الطلب مؤقتاً. حدّث yt-dlp (pip install -U yt-dlp) أو استخدم cookies.txt."
    if "ffmpeg" in m or "ffprobe" in m:
        return "ffmpeg غير مثبّت. ثبّته لدمج الفيديو والصوت وتحويل الصيغ."
    return ""


def build_opts(job, hook):
    p = job.params
    q = str(p.get("quality") or "max")
    fmt = str(p.get("format") or "mp4").lower()
    mode = str(p.get("mode") or "auto")
    h = int(q) if q.isdigit() else None
    ff = CFG["has_ffmpeg"]
    audio = mode == "audio" or fmt in AUDIO_FORMATS

    hf = f"[height<={h}]" if h else ""
    opts = {
        "outtmpl": os.path.join(job.dir, "%(title).120B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [hook],
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "windowsfilenames": True,
        "overwrites": True,
    }
    stages = 1
    if audio:
        opts["format"] = "bestaudio/best"
        if ff:
            codec = fmt if fmt in AUDIO_FORMATS else "mp3"
            pp = {"key": "FFmpegExtractAudio", "preferredcodec": "vorbis" if codec == "ogg" else codec}
            if codec in ("mp3", "ogg", "opus"):
                pp["preferredquality"] = "320"
            opts["postprocessors"] = [pp]
    elif mode == "mute":
        opts["format"] = f"bv*{hf}[ext=mp4]/bv*{hf}/bv*/b"
    elif ff:
        if fmt == "webm":
            opts["format"] = (f"bv*{hf}[ext=webm]+ba[ext=webm]/bv*{hf}+ba/b{hf}/b")
            opts["merge_output_format"] = "webm"
        else:
            opts["format"] = (f"bv*{hf}[ext=mp4]+ba[ext=m4a]/bv*{hf}+ba/b{hf}[ext=mp4]/b{hf}/b")
            opts["merge_output_format"] = "mp4"
        stages = 2
    else:
        opts["format"] = f"b{hf}[ext=mp4]/b{hf}/b[ext=mp4]/b"

    cookies = cookies_path()
    if os.path.isfile(cookies):
        opts["cookiefile"] = cookies
    elif CFG["browser"]:
        opts["cookiesfrombrowser"] = (CFG["browser"],)

    runtimes = {}
    for rt in ("deno", "node", "bun"):
        if shutil.which(rt):
            runtimes[rt] = {}
    if runtimes:
        opts["js_runtimes"] = runtimes
    return opts, stages


def collect_files(info, jobdir):
    paths = []

    def add(i):
        if not i:
            return
        for rd in (i.get("requested_downloads") or []):
            fp = rd.get("filepath") or rd.get("_filename")
            if fp:
                paths.append(fp)
        for e in (i.get("entries") or []):
            add(e)

    add(info)
    paths = [p for p in dict.fromkeys(paths) if os.path.isfile(p)]
    if not paths:
        for f in sorted(os.listdir(jobdir)):
            fp = os.path.join(jobdir, f)
            if os.path.isfile(fp) and not f.endswith((".part", ".ytdl", ".temp", ".json")):
                paths.append(fp)
    return paths


def run_job(job):
    with SLOTS:
        if job.cancel.is_set():
            job.state, job.phase = "cancelled", "cancelled"
            return
        job.state, job.phase = "running", "starting"
        try:
            if yt_dlp is None:
                raise RuntimeError("yt-dlp غير مثبّت. نفّذ: pip install -U \"yt-dlp[default]\"")
            os.makedirs(job.dir, exist_ok=True)
            holder = {}

            def hook(d):
                if job.cancel.is_set():
                    raise Cancelled()
                st = holder.setdefault("st", {"done": 0})
                s = d.get("status")
                stages = holder.get("stages", 1)
                if s == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    got = d.get("downloaded_bytes") or 0
                    frac = min(got / total, 1) if total else 0
                    job.progress = max(job.progress, (st["done"] + frac) / stages * 92)
                    job.speed = d.get("speed") or 0
                    job.eta = d.get("eta")
                    job.bytes = job.base_bytes + got
                    job.phase = "downloading"
                elif s == "finished":
                    st["done"] += 1
                    job.base_bytes += d.get("total_bytes") or d.get("downloaded_bytes") or 0
                    job.progress = max(job.progress, min(st["done"] / stages * 92, 92))
                    job.phase = "processing"

            opts, holder["stages"] = build_opts(job, hook)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
            if job.cancel.is_set():
                raise Cancelled()
            if not info:
                raise RuntimeError("لم يُعثر على وسائط في هذا الرابط.")
            job.title = (info.get("title") or "")[:200]
            files = collect_files(info, job.dir)
            if not files:
                raise RuntimeError("اكتمل الاستخراج دون إنتاج ملف.")
            if len(files) > 1:
                base = re.sub(r'[\\/:*?"<>|]', "_", job.title or "altra")[:100] or "altra"
                zpath = os.path.join(job.dir, base + ".zip")
                with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
                    for f in files:
                        z.write(f, os.path.basename(f))
                final = zpath
            else:
                final = files[0]
            job.filepath = final
            job.filename = os.path.basename(final)
            job.size = os.path.getsize(final)
            job.bytes = job.size
            job.progress = 100.0
            job.state, job.phase = "done", "done"
        except Cancelled:
            job.state, job.phase = "cancelled", "cancelled"
            job.error = "أُلغي"
        except Exception as e:  # noqa: BLE001
            if job.cancel.is_set():
                job.state, job.phase = "cancelled", "cancelled"
                job.error = "أُلغي"
            else:
                job.error = clean_error(e) or "فشل غير معروف"
                job.login = login_needed(job.error, job.url)
                job.hint = explain(job.error) if not job.login else "هذا المحتوى يتطلب تسجيل الدخول. اضغط الشارة الزرقاء في التطبيق لاستيراد جلسة الدخول."
                if not job.hint:
                    job.hint = explain(job.error)
                job.state, job.phase = "error", "error"
        finally:
            job.finished = time.time()


def cookies_path():
    return CFG["cookies"] or os.path.join(HERE, "cookies.txt")


def parse_cookies(text):
    """يقبل Netscape (cookies.txt) أو JSON من إضافة Cookie-Editor ويرجع قائمة صفوف Netscape."""
    text = (text or "").strip().lstrip("\ufeff")
    rows = []
    far = int(time.time()) + 30 * 86400
    if text[:1] in "[{":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("cookies") or []
        for c in data:
            dom, name = str(c.get("domain") or ""), c.get("name")
            if not dom or name is None:
                continue
            exp = c.get("expirationDate") or c.get("expires") or 0
            exp = int(exp) if isinstance(exp, (int, float)) and exp > 0 else far
            rows.append([("#HttpOnly_" if c.get("httpOnly") else "") + dom,
                         "TRUE" if dom.startswith(".") else "FALSE", c.get("path") or "/",
                         "TRUE" if c.get("secure") else "FALSE", str(exp), str(name), str(c.get("value") or "")])
    else:
        for line in text.splitlines():
            line = line.rstrip("\r\n")
            if not line.strip() or (line.startswith("#") and not line.startswith("#HttpOnly_")):
                continue
            parts = line.split("\t") if line.count("\t") >= 6 else re.split(r"\s+", line.strip(), 6)
            if len(parts) < 7:
                continue
            rows.append(parts[:7])
    return rows


def save_cookies(rows, replace=False):
    path = cookies_path()
    keyed = {}
    if not replace and os.path.isfile(path):
        for r in parse_cookies(open(path, encoding="utf-8", errors="ignore").read()):
            keyed[(r[0].replace("#HttpOnly_", ""), r[2], r[5])] = r
    for r in rows:
        keyed[(r[0].replace("#HttpOnly_", ""), r[2], r[5])] = r
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for r in keyed.values():
            f.write("\t".join(r) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return sorted({k[0].lstrip(".") for k in keyed})


def cookie_domains():
    path = cookies_path()
    if not os.path.isfile(path):
        return []
    try:
        rows = parse_cookies(open(path, encoding="utf-8", errors="ignore").read())
    except Exception:
        return []
    return sorted({r[0].replace("#HttpOnly_", "").lstrip(".") for r in rows})


def cleaner():
    while True:
        time.sleep(300)
        limit = time.time() - CFG["keep"] * 60
        with JOBS_LOCK:
            old = [j for j in JOBS.values() if j.finished and j.finished < limit]
            for j in old:
                JOBS.pop(j.id, None)
        for j in old:
            shutil.rmtree(j.dir, ignore_errors=True)


# ── HTTP ───────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "AltraHelper/" + VERSION

    def log_message(self, fmt, *args):  # صامت
        pass

    # --- مساعدات
    def origin_ok(self):
        origin = self.headers.get("Origin")
        if not origin or CFG["allow_all"]:
            return True
        u = urlparse(origin)
        if u.hostname in ("localhost", "127.0.0.1", "::1"):
            return True
        if u.netloc == self.headers.get("Host"):
            return True
        return origin in CFG["origins"]

    def host_ok(self):
        if not CFG["loopback"]:
            return True
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in ("localhost", "127.0.0.1", "::1", "")

    def cors(self):
        origin = self.headers.get("Origin")
        if origin and self.origin_ok():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Expose-Headers", "Content-Disposition, Content-Length")

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def guard(self):
        if not self.host_ok():
            self.send_json({"error": "host not allowed"}, 403)
            return False
        if not self.origin_ok():
            self.send_json({"error": "origin not allowed. use --origin"}, 403)
            return False
        return True

    # --- طرق HTTP
    def do_OPTIONS(self):
        if not self.guard():
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Max-Age", "600")
        self.cors()
        self.end_headers()

    def do_GET(self):
        if not self.guard():
            return
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json({
                "ok": True, "altra": True, "version": VERSION,
                "ytdlp": getattr(getattr(yt_dlp, "version", None), "__version__", None) if yt_dlp else None,
                "ffmpeg": CFG["has_ffmpeg"],
                "cookies": bool(cookie_domains()),
                "cookie_domains": cookie_domains(),
            })
        m = re.match(r"^/api/status/([0-9a-f]{16})$", path)
        if m:
            j = JOBS.get(m.group(1))
            return self.send_json(j.public() if j else {"error": "not found"}, 200 if j else 404)
        m = re.match(r"^/file/([0-9a-f]{16})$", path)
        if m:
            j = JOBS.get(m.group(1))
            if not j or j.state != "done" or not os.path.isfile(j.filepath):
                return self.send_json({"error": "file not ready"}, 404)
            return self.send_file(j.filepath, j.filename)
        return self.serve_static(path)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if not self.guard():
            return
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            limit = 2 * 1024 * 1024 if path == "/api/cookies" else 65536
            if n > limit:
                return self.send_json({"error": "too large"}, 413)
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self.send_json({"error": "bad json"}, 400)

        if path == "/api/resolve":
            url = str(data.get("url") or "").strip()
            if not re.match(r"^https?://", url, re.I) or len(url) > 2048:
                return self.send_json({"error": "رابط غير صالح"}, 400)
            q = str(data.get("quality") or "max")
            fmt = str(data.get("format") or "mp4").lower()
            mode = str(data.get("mode") or "auto")
            if not (q == "max" or q.isdigit()):
                q = "max"
            if fmt not in AUDIO_FORMATS | VIDEO_FORMATS:
                fmt = "mp4"
            if mode not in ("auto", "audio", "mute"):
                mode = "auto"
            job = Job(url, {"quality": q, "format": fmt, "mode": mode})
            with JOBS_LOCK:
                JOBS[job.id] = job
            threading.Thread(target=run_job, args=(job,), daemon=True).start()
            return self.send_json({"id": job.id})

        if path == "/api/cookies":
            try:
                rows = parse_cookies(str(data.get("text") or ""))
            except Exception:
                return self.send_json({"error": "تعذّر قراءة الملف. استخدم cookies.txt أو JSON من Cookie-Editor."}, 400)
            if not rows:
                return self.send_json({"error": "لم أجد أي كوكيز صالحة في النص."}, 400)
            doms = save_cookies(rows, replace=bool(data.get("replace")))
            return self.send_json({"ok": True, "count": len(rows), "domains": doms})
        if path == "/api/cookies/clear":
            try:
                os.remove(cookies_path())
            except OSError:
                pass
            return self.send_json({"ok": True})

        m = re.match(r"^/api/cancel/([0-9a-f]{16})$", path)
        if m:
            j = JOBS.get(m.group(1))
            if j:
                j.cancel.set()
            return self.send_json({"ok": bool(j)})
        return self.send_json({"error": "not found"}, 404)

    # --- ملفات
    def send_file(self, path, fname):
        size = os.path.getsize(path)
        start, end, status = 0, size - 1, 200
        rng = self.headers.get("Range")
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
            if m:
                a, b = m.groups()
                if a == "" and b != "":
                    start = max(0, size - int(b))
                elif a != "":
                    start = int(a)
                    end = int(b) if b else size - 1
                end = min(end, size - 1)
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                status = 206
        ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        ascii_name = re.sub(r"[^A-Za-z0-9._-]", "_", fname) or "download"
        self.send_header("Content-Disposition",
                         f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(fname)}")
        self.send_header("Cache-Control", "no-store")
        self.cors()
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = length
                while left > 0:
                    chunk = f.read(min(262144, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_static(self, path):
        rel = unquote(path.lstrip("/")) or "index.html"
        full = os.path.realpath(os.path.join(HERE, rel))
        ext = os.path.splitext(full)[1].lower()
        if not full.startswith(HERE + os.sep) or not os.path.isfile(full) or ext not in STATIC_OK:
            return self.send_json({"error": "not found"}, 404)
        with open(full, "rb") as f:
            body = f.read()
        ctype = "application/manifest+json" if ext == ".webmanifest" else (mimetypes.guess_type(full)[0] or "application/octet-stream")
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser(description="ALTRA helper server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--cookies", help="ملف cookies.txt (صيغة Netscape)")
    ap.add_argument("--browser", help="قراءة الكوكيز من متصفح (chrome, firefox, edge...) على الكمبيوتر")
    ap.add_argument("--origin", action="append", default=[], help="سماح لموقع إضافي، أو * للجميع")
    ap.add_argument("--cache", help="مجلد الملفات المؤقتة")
    ap.add_argument("--keep", type=int, default=60, help="مدة حفظ الملفات المؤقتة بالدقائق")
    ap.add_argument("--jobs", type=int, default=4, help="عدد التحميلات المتزامنة في المساعد")
    a = ap.parse_args()

    CFG["cookies"] = a.cookies
    CFG["browser"] = a.browser
    CFG["keep"] = a.keep
    CFG["loopback"] = a.host in ("127.0.0.1", "localhost", "::1")
    for o in a.origin:
        if o == "*":
            CFG["allow_all"] = True
        else:
            CFG["origins"].add(o.rstrip("/"))
    if a.cache:
        CFG["cache"] = os.path.abspath(a.cache)
    global SLOTS
    SLOTS = threading.BoundedSemaphore(max(1, a.jobs))

    shutil.rmtree(CFG["cache"], ignore_errors=True)
    os.makedirs(CFG["cache"], exist_ok=True)
    threading.Thread(target=cleaner, daemon=True).start()

    try:
        srv = ThreadingHTTPServer((a.host, a.port), Handler)
    except OSError as e:
        print(f"تعذّر فتح المنفذ {a.port}: {e}\nجرّب منفذاً آخر:  python altra-server.py --port {a.port + 1}")
        sys.exit(1)
    srv.daemon_threads = True

    ver = getattr(getattr(yt_dlp, "version", None), "__version__", None) if yt_dlp else None
    print("═" * 56)
    print(f" ALTRA Helper v{VERSION}")
    print(f" yt-dlp : {ver or 'غير مثبّت  ←  pip install -U \"yt-dlp[default]\"'}")
    print(f" ffmpeg : {'متوفر' if CFG['has_ffmpeg'] else 'غير موجود (الدمج والتحويل معطّلان)'}")
    print(f" العنوان: http://{'localhost' if CFG['loopback'] else a.host}:{a.port}")
    print(" اترك هذه النافذة مفتوحة أثناء التحميل.  إيقاف: Ctrl+C")
    print("═" * 56)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nتم الإيقاف.")
    finally:
        shutil.rmtree(CFG["cache"], ignore_errors=True)


if __name__ == "__main__":
    main()
