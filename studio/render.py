"""Timeline -> final 9:16 short. One ffmpeg pass, no intermediate renders."""
import os
import shlex

from textkit import Overlay, ass_filter
from util import ensure_ffmpeg, ffmpeg_cmd, log, run

W, H = 1080, 1920
FPS = 30



LOOKS = {
    # measured against Kingsman ref 4rlFBAAYEZE: YAVG 84, SATAVG 23, V +4 (warm)
    "cinematic": (
        "eq=contrast=1.26:brightness=-0.055:saturation=0.58:gamma=0.90,"
        "colorbalance=rs=0.03:gs=-0.005:bs=-0.035:rm=0.02:bm=-0.02,"
        "curves=all='0/0 0.22/0.15 0.5/0.44 0.78/0.79 1/0.94',"
        "vignette=PI/4.5,"
        "noise=alls=7:allf=t+u"
    ),
    # warm filmic: keeps brightness, boosts saturation slightly, teal shadows /
    # warm highlights, grain + vignette — makes a movie clip look "regraded"
    "film": (
        "eq=contrast=1.24:saturation=1.16:gamma=0.97,"
        "colorbalance=rs=0.05:gs=0.005:bs=-0.06:rm=0.03:bm=-0.03:"
        "rh=0.07:gh=0.01:bh=-0.07,"
        "curves=all='0/0 0.20/0.17 0.50/0.52 0.80/0.85 1/1',"
        "vignette=PI/4.8,"
        "noise=alls=8:allf=t+u"
    ),
    # AI-upscaled look (ref: Tom Cruise upscale screenshot) — teal shadows,
    # warm highlights, black crush, heavy sharpen, synthetic grain.
    # NOTE: is look ka maqsad "asli film" nahi, AI-enhanced "4K" vibe hai.
    "ai": (
        "eq=contrast=1.55:brightness=0.09:gamma=1.02:saturation=1.18,"
        "unsharp=5:5:1.8:5:5:0.4,"
        "noise=alls=9:allf=t"
    ),
    # very desaturated teal — SPR explainer look
    "teal": (
        "eq=contrast=1.18:brightness=-0.04:saturation=0.34:gamma=0.94,"
        "colorbalance=bs=0.06:gs=0.015:rs=-0.045:bm=0.03:gm=0.01:rm=-0.02,"
        "curves=all='0/0 0.24/0.19 0.5/0.47 0.76/0.77 1/0.93',"
        "vignette=PI/4.5,"
        "noise=alls=6:allf=t+u"
    ),
}


class Segment:
    """One cut in the timeline."""

    def __init__(self, src, ss, dur, fit="blur", focus=(0.5, 0.45), zoom=1.0,
                 zoom_to=None, speed=1.0, mute=False, grade=True,
                 freeze=False, freeze_to=0.0, pop=None, label=None,
                 crop_top=0.0, crop_bottom=0.0, bright=0.0,
                 crop_left=0.0, crop_right=0.0):
        self.src, self.ss, self.dur = src, float(ss), float(dur)
        self.fit = fit
        self.focus = focus            # (x, y) 0..1 where to centre the crop
        self.zoom = zoom
        self.zoom_to = zoom_to        # animated zoom target
        self.speed = speed
        self.mute = mute
        self.grade = grade
        self.freeze = freeze
        self.freeze_to = freeze_to
        self.pop = pop                # optional dict for punch-in
        self.label = label
        self.crop_top = crop_top      # trim baked-in headers, 0..0.4
        self.crop_bottom = crop_bottom
        self.crop_left = crop_left    # trim baked-in side bars, 0..0.4
        self.crop_right = crop_right
        self.bright = bright          # extra brightness for dark B-roll

    def out_dur(self):
        return self.dur / self.speed


class Timeline:
    def __init__(self, music=None, music_vol=0.42, name="short", size=(1080, 1920)):
        self.W, self.H = size
        self.segments = []
        self._size = size
        self.sfx = []                 # (time, path, gain)
        self.music = music
        self.music_vol = music_vol
        self.music_ss = 0.0            # start offset inside the music file
        self.master_gain_db = 0.0      # makeup gain before the limiter
        self.overlay = Overlay(playres=size)   # ASS canvas == video size (1:1 text)
        self.name = name
        self.keep_original = True
        self.original_vol = 1.0
        self.duck = None               # volume multiplier for the original while VO plays
        self.look = None               # named colour grade preset
        self.frame = None              # (x, y, w, h) — video lives here, rest is black
        self.rounded_frame = None      # dict from analyze.rounded_mask()

    def add(self, seg):
        self.segments.append(seg)
        return seg

    def add_gap(self, dur):
        """Black beat between clips (makes the end of each clip readable)."""
        from util import CACHE, ensure_ffmpeg, ffmpeg_cmd, run
        os.makedirs(CACHE, exist_ok=True)
        p = os.path.join(CACHE, f"black_{self.W}x{self.H}.mp4")
        if not os.path.exists(p):
            cmd = ffmpeg_cmd(["-f", "lavfi", "-i",
                              f"color=c=black:s={self.W}x{self.H}:r={FPS}:d=1",
                              "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                              "-t", "1", "-c:v", "libx264", "-preset", "ultrafast",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", p])
            run(cmd, timeout=120)
        self.add(Segment(src=p, ss=0.0, dur=float(dur), fit="crop", grade=False))
        return self.segments[-1]

    def add_sfx(self, t, name, gain=1.0, path=None):
        if path is None:
            import sfx
            path = sfx.get(name)
        self.sfx.append((round(float(t), 3), path, float(gain)))

    def duration(self):
        return sum(s.out_dur() for s in self.segments)

    # ------------------------------------------------------------------
    def _seg_chain(self, i, s):
        W, H = self.W, self.H
        """Return (video_chain, audio_chain) strings. Each is ';'-joined graph parts."""
        head = f"[{i}:v]fps={FPS},setsar=1,format=yuv420p"
        parts = []
        if s.fit == "crop":
            z = s.zoom
            # when the clip lives inside a sub-frame, cover that frame's aspect —
            # covering the full canvas first would crop twice and lose the subject
            cw, ch = (self.frame[2], self.frame[3]) if self.frame else (W, H)
            chain = head
            if s.crop_top or s.crop_bottom or s.crop_left or s.crop_right:
                ct, cb = s.crop_top, s.crop_bottom
                cl, cr = getattr(s, "crop_left", 0.0), getattr(s, "crop_right", 0.0)
                chain += (f",crop=w='trunc(iw*(1-{cl}-{cr})/2)*2'"
                          f":h='trunc(ih*(1-{ct}-{cb})/2)*2'"
                          f":x='trunc(iw*{cl})':y='trunc(ih*{ct})'")
            # cover the 9:16 frame, then cut the overflow around the focus point
            chain += f",scale={cw}:{ch}:force_original_aspect_ratio=increase"
            if z != 1.0:
                chain += f",scale=iw*{z}:ih*{z}"
            chain += (f",crop={cw}:{ch}:x='(iw-ow)*{s.focus[0]:.4f}'"
                      f":y='(ih-oh)*{s.focus[1]:.4f}'")
            chain += f"[p{i}]"
            parts.append(chain)
        else:
            parts.append(f"{head},split=2[bga][fga]")
            if s.fit == "pad":
                parts.append(f"[bga]scale={W}:{H},eq=brightness=-0.35:saturation=0.2,"
                             f"gblur=sigma=1[bg]")
            else:
                parts.append(f"[bga]scale={W}:{H}:force_original_aspect_ratio=increase,"
                             f"crop={W}:{H},gblur=sigma=28,eq=brightness=-0.22:"
                             f"saturation=1.2[bg]")
            pre = "[fga]"
            if s.crop_top or s.crop_bottom or s.crop_left or s.crop_right:
                ct, cb = s.crop_top, s.crop_bottom
                cl, cr = getattr(s, "crop_left", 0.0), getattr(s, "crop_right", 0.0)
                parts.append(f"[fga]crop=w='trunc(iw*(1-{cl}-{cr})/2)*2'"
                             f":h='trunc(ih*(1-{ct}-{cb})/2)*2'"
                             f":x='trunc(iw*{cl})':y='trunc(ih*{ct})'[fgc]")
                pre = "[fgc]"
            if s.fit == "fill":
                parts.append(f"{pre}crop=w='trunc(ih*0.72/2)*2':h=ih:"
                             f"x='(iw-ow)*{s.focus[0]:.4f}':y=0,"
                             f"scale={W}:-2:flags=lanczos[fg]")
            else:
                parts.append(f"{pre}scale={W}:-2:flags=lanczos[fg]")
            parts.append("[fg]null[fgz]")
            parts.append(f"[bg][fgz]overlay=(W-w)/2:(H-h)/2:shortest=1[p{i}]")

        tail = []
        if s.grade:
            tail.append(f"eq=contrast=1.07:saturation=1.16:gamma={1.0 - s.bright:.3f}"
                        if s.bright else "eq=contrast=1.07:saturation=1.16:gamma=0.99")
            tail.append("unsharp=5:5:0.55:5:5:0.0")
        if s.speed != 1.0:
            tail.append(f"setpts=PTS/{s.speed}")
        if s.freeze:
            tail.append(f"tpad=stop_mode=clone:stop_duration="
                        f"{max(0.2, (s.freeze_to or (s.dur + 0.22)) - s.dur):.3f}")
        if self.look and self.look in LOOKS:
            tail.append(LOOKS[self.look])
        if self.frame:
            fx, fy, fw, fh = self.frame
            tail += [f"scale={fw}:{fh}:force_original_aspect_ratio=increase",
                     f"crop={fw}:{fh}:x='(iw-ow)*{s.focus[0]:.4f}'",
                     f"pad={W}:{H}:{fx}:{fy}:color=black"]
        elif self.rounded_frame:
            pass                      # composited later in build()
        else:
            tail += [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
                     f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black"]
        if s.zoom_to and abs(s.zoom_to - s.zoom) > 1e-3:
            d = max(0.1, s.out_dur())
            tail.append(f"scale=w='trunc({W}*({s.zoom}+({s.zoom_to}-{s.zoom})"
                        f"*min(t/{d},1))/2)*2':h=-2:eval=frame")
            tail.append(f"crop={W}:{H}")
        tail.append("setsar=1")
        parts.append(f"[p{i}]" + (",".join(tail) if tail else "null") + f"[v{i}]")
        vid = ";".join(parts)

        aud = None
        if not s.mute:
            d = s.out_dur()
            chain = [f"[{i}:a]aresample=44100", "aformat=channel_layouts=stereo",
                     f"atrim=0:{max(0.05, d):.3f}"]
            if s.speed != 1.0:
                chain.append(f"atempo={min(2.0, max(0.5, s.speed)):.3f}")
            chain += ["asetpts=PTS-STARTPTS", "apad", f"atrim=0:{d:.3f}", f"[a{i}]"]
            aud = ",".join(x if not x.startswith("[") else x for x in chain[:1]) + \
                  "," + ",".join(chain[1:])
            aud = (f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                   f"atrim=0:{max(0.05, d):.3f},"
                   + (f"atempo={min(2.0, max(0.5, s.speed)):.3f}," if s.speed != 1.0 else "")
                   + f"asetpts=PTS-STARTPTS,apad,atrim=0:{d:.3f}[a{i}]")
        return vid, aud

    def _render_segment(self, i, s, path, crf=18, preset="veryfast"):
        """Render one cut to its own file (small memory footprint, reusable)."""
        vid, aud = self._seg_chain(0, s)
        fc = vid + (";" + aud if aud else "")
        src_input = ["-ss", f"{s.ss:.3f}", "-t", f"{max(0.06, s.dur):.3f}", "-i", s.src]
        if not aud:
            fc += (f";anullsrc=r=44100:cl=stereo,atrim=0:{s.out_dur():.3f},"
                   f"asetpts=PTS-STARTPTS[a0]")
        cmd = ffmpeg_cmd([*src_input, "-filter_complex_threads", "1",
                          "-filter_complex", fc,
                          "-map", "[v0]", "-map", "[a0]",
                          "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                          "-profile:v", "high", "-pix_fmt", "yuv420p",
                          "-r", str(FPS), "-g", "60", "-threads", "2",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                          "-video_track_timescale", "90000",
                          "-t", f"{s.out_dur():.3f}", path])
        r = run(cmd, timeout=1200)
        if r.returncode != 0:
            open("/tmp/last_fc.txt", "w").write(fc)
            raise RuntimeError("segment %d failed:\n%s" % (i, (r.stderr or "")[-2500:]))
        if self._is_black(path):
            # source ran out -> pull the seek back and try once more
            s2 = max(0.0, s.ss - s.dur * 0.5)
            if s2 != s.ss:
                s_backup = s.ss
                s.ss = s2
                log(f"  segment {i + 1}: black frames, retrying from {s2:.2f}s")
                out = self._render_segment(i, s, path, crf=crf, preset=preset)
                s.ss = s_backup
                return out
        return path

    @staticmethod
    def _is_black(path, samples=3, thresh=12.0):
        from util import FFMPEG, probe
        d = probe(path)["duration"]
        if d < 0.12:
            return True
        for k in range(samples):
            tmp = "/tmp/_segchk.jpg"
            run([FFMPEG, "-v", "error", "-ss", f"{d * (k + 1) / (samples + 1):.2f}",
                 "-i", path, "-frames:v", "1", "-vf", "scale=64:-2", "-q:v", "5",
                 tmp, "-y"])
            try:
                import cv2
                im = cv2.imread(tmp, cv2.IMREAD_GRAYSCALE)
                if im is not None and float(im.mean()) > thresh:
                    return False
            except Exception:
                return False
        return True

    def build(self, out_path, crf=19, preset="veryfast", max_dur=None,
              loudnorm=True, threads=2):
        """Render each cut separately, then concat + overlay + mix in one pass."""
        import hashlib
        import json
        ensure_ffmpeg()
        if not self.segments:
            raise RuntimeError("empty timeline")

        W, H = self.W, self.H
        total = self.duration()
        if max_dur:
            total = min(total, max_dur)

        # Include source-file fingerprints: replacing a clip in-place must not
        # silently reuse pre-rendered segments made from the old bytes.
        source_stamps = {}
        for seg in self.segments:
            p = os.path.abspath(seg.src)
            if p not in source_stamps:
                try:
                    st = os.stat(p)
                    source_stamps[p] = (st.st_size, st.st_mtime_ns)
                except OSError:
                    source_stamps[p] = None
        CODE_V = "v6-source-stamp-in-sig"
        sig = hashlib.md5(json.dumps([
            CODE_V,
            crf, preset,                       # quality bhi signature ka hissa
            tuple(self.frame) if self.frame else None,   # band layout bhi signature ka hissa
            self.look,
            sorted(source_stamps.items()),
            [(s.src, round(s.ss, 3), round(s.dur, 3), s.fit, s.focus, s.zoom,
              s.zoom_to, s.speed, s.mute, s.grade, s.freeze, s.freeze_to,
              s.crop_top, s.crop_bottom, getattr(s, 'crop_left', 0.0),
              getattr(s, 'crop_right', 0.0)) for s in self.segments]]
            , default=str).encode()).hexdigest()[:12]
        segdir = os.path.join(os.path.dirname(out_path), "..", "work", "segs", sig)
        segdir = os.path.abspath(segdir)
        os.makedirs(segdir, exist_ok=True)

        files = []
        for i, s in enumerate(self.segments):
            p = os.path.join(segdir, f"s{i:03d}.mp4")
            if not (os.path.exists(p) and os.path.getsize(p) > 2000):
                log(f"  segment {i + 1}/{len(self.segments)}")
                self._render_segment(i, s, p, crf=crf, preset=preset)
            files.append(p)

        lst = os.path.join(segdir, "list.txt")
        with open(lst, "w") as f:
            for p in files:
                f.write("file '%s'\n" % p.replace("'", "'\\''"))

        inputs = ["-f", "concat", "-safe", "0", "-i", lst]
        idx = 1
        music_idx = None
        if self.music:
            music_idx = idx
            if getattr(self, "music_ss", 0):
                inputs += ["-ss", f"{self.music_ss:.3f}", "-i", self.music]
            else:
                inputs += ["-i", self.music]
            idx += 1
        sfx_slots = []
        for t, p_, g in self.sfx:
            sfx_slots.append((t, idx, g))
            inputs += ["-i", p_]
            idx += 1

        if self.rounded_frame:
            m = self.rounded_frame
            mask_idx = idx                     # mask goes in as the LAST input
            inputs += ["-i", m["path"]]
            chains = [
                f"[0:v]fps={FPS},split=2[fg0][bg0]",
                (f"[bg0]scale={m['w']}:{m['h']}:force_original_aspect_ratio=increase,"
                 f"crop={m['w']}:{m['h']},gblur=sigma={m.get('blur', 26)},"
                 f"eq=brightness=-0.16:saturation=0.95[bg]"
                 if m.get("bg") == "blur" else
                 f"color=c=black:s={m['w']}x{m['h']}:r={FPS}:d={total:.3f}[bg]"),
                f"[fg0]scale={m['box_w']}:{m['box_h']}:force_original_aspect_ratio=increase,"
                f"crop={m['box_w']}:{m['box_h']},format=yuva420p[vr]",
                f"[{mask_idx}:v]crop={m['box_w']}:{m['box_h']}:"
                f"(iw-{m['box_w']})/2:{m['box_y']},format=gray[mk]",
                "[vr][mk]alphamerge[rv]",
                f"[bg][rv]overlay=(W-w)/2:{m['box_y']}:shortest=1,format=yuv420p[rc]",
                f"[rc]{ass_filter(self.overlay.path)}[vout]",
            ]
        else:
            chains = [f"[0:v]{ass_filter(self.overlay.path)}[vout]"]
        chains.append(f"[0:a]volume={self.original_vol},"
                      f"aformat=channel_layouts=stereo[abase]")
        mix = ["[abase]"]
        if music_idx is not None:
            chains.append(
                f"[{music_idx}:a]aresample=44100,aformat=channel_layouts=stereo,"
                f"atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={self.music_vol},"
                f"afade=t=in:st=0:d=0.25,"
                f"afade=t=out:st={max(0.1, total - 0.7):.2f}:d=0.7[mus]")
            mix.append("[mus]")
        for t, i, gain in sfx_slots:
            chains.append(
                f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                f"volume={gain},adelay={int(t * 1000)}|{int(t * 1000)},"
                f"apad,atrim=0:{total:.3f}[sx{i}]")
            mix.append(f"[sx{i}]")
        chains.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:"
                      f"duration=longest[mixed]")
        if loudnorm and os.environ.get("NORM", "1") == "1":
            chains.append("[mixed]loudnorm=I=-14:TP=-1.5:LRA=11:linear=true[aout]")
        else:
            g = getattr(self, "master_gain_db", 0.0)
            pre = f"volume={g:.1f}dB," if g else ""
            chains.append(f"[mixed]{pre}alimiter=limit=0.95[aout]")

        cmd = ffmpeg_cmd([*inputs, "-filter_complex_threads", "1",
                          "-filter_complex", ";".join(chains),
                          "-map", "[vout]", "-map", "[aout]",
                          "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                          "-profile:v", "high", "-pix_fmt", "yuv420p",
                          "-r", str(FPS), "-g", "60",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                          *( [] if os.environ.get("NORM","1")=="0" else ["-movflags","+faststart"] ),
                          "-t", f"{total:.3f}",
                          "-threads", str(threads), out_path])
        open("/tmp/last_cmd.txt", "w").write(" ".join(cmd))
        log("rendering ->", out_path)
        r = run(cmd, timeout=3600)
        if r.returncode != 0:
            open("/tmp/last_fc.txt", "w").write(";".join(chains))
            raise RuntimeError((r.stderr or "")[-3000:])
        return out_path
