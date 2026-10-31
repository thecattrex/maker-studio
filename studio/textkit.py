"""ASS subtitle / overlay engine — all the on-screen text for the shorts."""
import os

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "fonts")

ACCENT = "&H2E2EF7&"      # red
WHITE = "&HFFFFFF&"
BLACK = "&H000000&"

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {px}
PlayResY: {py}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{events}
"""

BASE_STYLES = """
Style: Title,Anton,{t1},&H00FFFFFF,&H000000FF,{out},&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,60,60,120,1
Style: TitleHi,Anton,{t1},{accent},&H000000FF,{out},&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,60,60,120,1
Style: Sub,Bebas Neue,{t2},&H00FFFFFF,&H000000FF,{out},&H00000000,-1,0,0,0,100,100,0,0,1,6,0,5,60,60,60,1
Style: Cap,Anton,{t3},&H00FFFFFF,&H0030C8FF,{outc},&H80101010,-1,0,0,0,100,100,2,0,1,6,2,2,60,60,80,1
Style: CapHi,Anton,{t3},{accent},&H0030C8FF,{outc},&H80101010,-1,0,0,0,100,100,2,0,1,6,2,2,60,60,80,1
Style: Rank,Archivo Black,{t4},&H00FFFFFF,&H000000FF,4,&H00000000,-1,0,0,0,100,100,2,0,1,5,1,2,0,0,0,1
Style: RankDim,Archivo Black,{t4},&H00787878,&H000000FF,4,&H00000000,-1,0,0,0,100,100,2,0,1,5,1,2,0,0,0,1
Style: Small,Inter,{t5},&H00FFFFFF,&H000000FF,3,&HB0000000,-1,0,0,0,100,100,2,0,1,3,0,2,20,20,20,1
Style: Chip,Inter,{t5},&H00FFFFFF,&H000000FF,3,&H90000000,-1,0,0,0,100,100,2,0,4,3,0,2,10,10,10,1
Style: Watermark,Inter,{t6},&H60FFFFFF,&H000000FF,0,&H60000000,-1,0,0,0,100,100,7,0,1,0,0,2,10,10,10,1
Style: Header,Poppins ExtraBold,{h1},&H00FFFFFF,&H000000FF,10,&HA0000000,-1,0,0,0,100,100,5,0,1,7,0,4,40,40,60,1
Style: HeaderHi,Poppins ExtraBold,{h1},{accent},&H000000FF,10,&HA0000000,-1,0,0,0,100,100,5,0,1,7,0,4,40,40,60,1
Style: ActionCap,Poppins ExtraBold,{a1},&H14FFFFFF,&H000000FF,9,&H99000000,-1,0,0,0,100,100,5,0,1,7,0,3,40,40,40,1
Style: Impact,Barlow Condensed ExtraBold,{i1},&H00FFFFFF,&H000000FF,12,&HC0000000,-1,0,0,0,100,100,5,0,1,7,0,4,40,40,40,1
Style: RankNum,Poppins ExtraBold,{r1},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,5,0,1,7,0,3,30,30,30,1
Style: RankLbl,Poppins ExtraBold,{r2},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,5,0,1,7,0,3,30,30,30,1
Style: CapYellow,Poppins Bold,{cy},&H0000D7FF,&H000000FF,6,&H90000000,-1,0,0,0,100,100,5,0,1,7,0,3,26,26,26,1
Style: Dialogue,Poppins ExtraBold,{d1},&H00FFFFFF,&H000000FF,7,&HB0000000,-1,0,0,0,100,100,5,0,1,7,0,3,30,30,30,1
Style: DialogueHi,Poppins ExtraBold,{d1},&H00FFFFFF,&H000000FF,7,&HB0000000,-1,0,0,0,100,100,5,0,1,7,0,3,30,30,30,1
"""



def rounded_rect(w, h, r):
    """ASS vector path for a rounded rectangle (origin top-left)."""
    k = 0.5523 * r
    return (f"m {r} 0 l {w - r} 0 "
            f"b {w - r + k} 0 {w} {r - k} {w} {r} "
            f"l {w} {h - r} "
            f"b {w} {h - r + k} {w - r + k} {h} {w - r} {h} "
            f"l {r} {h} "
            f"b {r - k} {h} 0 {h - r + k} 0 {h - r} "
            f"l 0 {r} "
            f"b 0 {r - k} {r - k} 0 {r} 0")


def _ts(t):
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s):
    return (s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            .replace("\n", "\\N"))


class Overlay:
    """Builds an .ass file. Coordinates are in 1080x1920 space."""

    def __init__(self, accent=ACCENT, playres=(1080, 1920)):
        self.events = []
        self.accent = accent
        self.playres = (int(playres[0]), int(playres[1]))
        self.warnings = []          # build ke waqt jo bhi gilat mile, yahan aata hai

    def add(self, start, end, style, text, layer=0):
        if end - start < 0.02:
            end = start + 0.02
        self.events.append((layer, max(0.0, start), end, style, text))



    # ------------------------------------------------- reference-matched text
    def header(self, start, end, top, bottom, size=54, y=170, gap=66,
               accent_word=None, emoji=None, italic=True, pop=True):
        """Two-line header like 'MALE EGO WHEN IT COMES TO / LOVE 💔🔥'.

        `bottom` is painted in the accent colour; an emoji can be appended.
        """
        it = "\\i1" if italic else ""
        sp = "\\fsp2"
        sh = "\\bord6\\bordcolor&HA0000000&\\shad5\\4c&H00000000&"
        st1 = f"{{\\an5\\pos(540,{y})\\fs{size}{it}{sp}{sh}"
        if pop:
            st1 += "\\fscx90\\fscy90\\alpha&HFF&\\t(0,120,\\fscx100\\fscy100\\alpha&H00&)"
        self.add(start, end, "Header", st1 + "}" + esc(top.upper()))

        y2 = y + gap
        acc = accent_word or bottom
        txt = bottom.upper()
        st2 = f"{{\\an5\\pos(540,{y2})\\fs{int(size * 1.08)}{it}{sp}{sh}\\c{self.accent}"
        if pop:
            st2 += "\\fscx90\\fscy90\\alpha&HFF&\\t(0,120,\\fscx100\\fscy100\\alpha&H00&)"
        self.add(start + 0.06, end, "Header", st2 + "}" + esc(acc.upper()))
        if emoji:
            self.add(start + 0.12, end, "Header",
                     f"{{\\an5\\pos(540,{y2 + int(size * 0.92)})\\fs{int(size * 0.8)}{it}}}"
                     + emoji)

    def band_header(self, start, end, line, band_h=132, bg="&H00FFFFFF&",
                    color="&H000000&", size=58, y=None, accent_word=None,
                    accent_color="&H002222D6&", rule=True, top=0):
        """Type-1 reference header: solid band upar, uske neeche ek patli line,
        text band ke beech me. Ek word accent colour me (reference: 'HE ALMOST D!ED')."""
        ty = top if y is None else y
        self.add(start, end, "Title",
                 f"{{\\an7\\pos(0,{top})\\p1\\c{bg}\\alpha&H00&\\bord0\\shad0}}"
                 + f"m 0 0 l {self.playres[0]} 0 {self.playres[0]} {band_h} 0 {band_h}"
                 + "{\\p0}", layer=4)
        if rule:
            self.add(start, end, "Title",
                     f"{{\\an7\\pos(0,{top + band_h})\\p1\\c&H000000&\\bord0\\shad0}}"
                     + f"m 0 0 l {self.playres[0]} 0 {self.playres[0]} 5 0 5"
                     + "{\\p0}", layer=4)
        parts = []
        txt = line.upper()
        if accent_word and accent_word.upper() in txt:
            bef, _, aft = txt.partition(accent_word.upper())
            if bef:
                parts.append("{\\c" + color + "}" + esc(bef))
            parts.append("{\\c" + accent_color + "}" + esc(accent_word.upper()))
            if aft:
                parts.append("{\\c" + color + "}" + esc(aft))
        else:
            parts.append("{\\c" + color + "}" + esc(txt))
        self.add(start, end, "Title",
                 f"{{\\an5\\pos({self.playres[0] // 2},{ty + band_h // 2})\\fs{size}\\fsp2"
                 f"\\bord0\\shad0}}" + " ".join(parts), layer=5)
        return 1

    def action_caption(self, start, end, text, y=1000, size=40, paren=True):
        """'(PUTS THE KNIFE BACK INSIDE)' style action caption in the middle."""
        t = f"({text.upper()})" if paren else text.upper()
        tags = (f"\\an5\\pos(540,{y})\\fs{size}\\fsp3\\c&HE8E8E8&"
                "\\bord9\\bordcolor&H000000&\\3c&H000000&\\3a&H9A&"
                "\\blur3\\fscx94\\fscy94\\alpha&HFF&"
                "\\t(0,110,\\fscx100\\fscy100\\alpha&H00&)")
        self.add(start, end, "ActionCap", "{" + tags + "}" + esc(t))

    def impact(self, start, dur, text, y=980, size=96, color=None,
               glow=True, scale_pop=True, glow_color=None):
        """Big punch word: 'IT'S OVER!' / 'CONGRATULATIONS'."""
        col = color or "&H00FFFFFF&"          # white fill pops on any frame
        gc = glow_color or self.accent
        # glow ON = soft halo; glow OFF = hard black outline (readable)
        tags = (f"\\an5\\pos(540,{y})\\fs{size}\\b1\\c{col}\\fsp2"
                + ("\\bord9\\bordcolor&H000000&\\shad2" if not glow
                   else "\\bord9\\bordcolor&H000000&\\shad0"))
        if glow:
            tags += f"\\blur7\\3c{gc}\\3a&H20&"
        if scale_pop:
            tags += ("\\fscx55\\fscy55\\alpha&HFF&"
                     "\\t(0,130,\\fscx112\\fscy112\\alpha&H00&)"
                     "\\t(130,220,\\fscx100\\fscy100)")
        self.add(start, start + dur, "Impact", "{" + tags + "}" + esc(text.upper()))


    # ------------------------------------------------- dialogue (karaoke) caps
    def dialogue_caps(self, words, to_global, y=1150, size=54, max_words=3,
                      max_dur=2.2, max_chars=26, hi_style="DialogueHi",
                      base_style="Dialogue", gap_split=0.55, upper=True):
        """Word-level dialogue captions: 2-3 words per card, spoken word in red.

        `words`: [{"w","s","e"}] in SOURCE time. `to_global(t)` maps source
        time -> timeline time (None => drop the word, e.g. inside a cut).
        """
        chunks, cur = [], []
        def flush():
            nonlocal cur
            if cur:
                chunks.append(cur)
                cur = []
        for w in words:
            txt = w["w"].strip()
            if not txt:
                continue
            start = w["s"]
            if cur:
                prev = cur[-1]
                if (len(cur) >= max_words or
                        start - prev["e"] > gap_split or
                        start - cur[0]["s"] > max_dur or
                        sum(len(c["w"]) + 1 for c in cur) + len(txt) > max_chars):
                    flush()
            cur.append({"w": txt, "s": w["s"], "e": w["e"]})

        def fmt(w):  # bracket-aware sentence case helper
            t = w["w"]
            return t.upper() if upper else t

        for ch in chunks:
            g0 = to_global(ch[0]["s"])
            if g0 is None:
                continue
            ends = [x for x in (to_global(ch[-1]["e"]) for x in [0]) if x is not None]
            g1 = to_global(ch[-1]["e"])
            if g1 is None:
                g1 = g0 + 0.9
            g1 = max(g0 + 0.35, g1 + 0.18)
            full = " ".join(fmt(w) for w in ch)
            # per-word highlight: redraw the whole line with one word accented
            for i, w in enumerate(ch):
                ws = to_global(w["s"])
                if ws is None:
                    continue
                we = to_global(w["e"]) or (ws + 0.3)
                nxt = to_global(ch[i + 1]["s"]) if i + 1 < len(ch) else g1
                seg_end = min(g1, max(we, nxt or we) if i + 1 < len(ch) else g1)
                parts = []
                for j, ww in enumerate(ch):
                    if j == i:
                        parts.append("{\\c" + self.accent + "&\\b1}" + esc(fmt(ww)) + "{\\c&HFFFFFF&}")
                    else:
                        parts.append(esc(fmt(ww)))
                self.add(ws, seg_end, hi_style,
                         "{\\an5\\pos(540," + str(y) + ")\\fs" + str(size) + "}" + " ".join(parts))


    # ------------------------------------------------ ranking list (ref style)
    def rank_side_list(self, start, end, items, x=92, y0=470, gap=168, size=62,
                       num_w=54, active=None, done=None, labels_on=None):
        """Persistent numbered list down the left edge, ref-A style.

        items: [{"n":1,"label":"No fear","color":"&H00FFFFFF&"}, ...]
        active: index that is currently playing (bright), others dim.
        done:   set of indices already played (dim + strikethrough dot).
        """
        for k, it in enumerate(items):
            y = y0 + k * gap
            i = int(it["n"]) - 1
            is_on = (active is None) or (i == active)
            is_done = done and i in done
            a = "&H00&" if is_on else ("&H18&" if is_done else "&H30&")
            col = it.get("color", "&H00FFFFFF&")
            self.add(start, end, "RankNum",
                     f"{{\\an4\\pos({x},{y})\\fnArchivo Black\\fsp0\\fs{size}\\c{col}\\alpha{a}"
                     f"\\bord9\\3c&H000000&\\3a&H00&}}"
                     + f"{it['n']}")
            if labels_on is not None and i not in labels_on:
                continue
            self.add(start, end, "RankLbl",
                     f"{{\\an4\\pos({x + num_w},{y + 14})\\fnAnton\\fs{int(size * 0.70)}"
                     f"\\c&H00FFFFFF&\\alpha{a}"
                     f"\\bord8\\3c&H000000&\\3a&H00&\\shad0}}"
                     + esc(str(it.get("label", "")).upper()))


    def yellow_caps(self, lines, y=985, size=38, max_words=5, cx=540):
        """Yellow small-caps captions, one short line per card (SPR ref style).

        lines: [{"t0":..,"t1":..,"text":".."}]
        """
        for ln in lines:
            t0, t1 = float(ln["t0"]), float(ln["t1"])
            if t1 - t0 < 0.25:
                t1 = t0 + 0.5
            txt = ln["text"]
            words = txt.split()
            chunks = []
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i:i + max_words]))
            step = (t1 - t0) / max(1, len(chunks))
            for i, ch in enumerate(chunks):
                a = t0 + i * step
                b = a + step * (1.0 if i < len(chunks) - 1 else 1.05)
                avail = int(cx * 1.80)          # 10% margin dono side
                fit = int(avail / max(1, len(ch)) / 0.60)
                fsz = max(24, min(size, fit))
                tags = (f"\\an5\\pos({cx},{y})\\fs{fsz}"
                        "\\bord10\\bordcolor&H000000&"
                        "\\shad3\\4c&H000000&\\4a&H80&"
                        "\\fscx97\\fscy97\\alpha&HFF&"
                        "\\t(0,90,\\fscx100\\fscy100\\alpha&H00&)")
                self.add(a, min(b, t1 + 0.15), "CapYellow",
                         "{" + tags + "}" + esc(ch.upper()))

    # ------------------------------------------- reference word-pop captions (T3)
    def word_caps_kara(self, groups, y=1260, size=60, font="Inter Black",
                       fsp=-1.5, bord=4, shad=3, max_line_chars=26,
                       lead=0.25, tail=0.45, blur=24, kf=8,
                       white=None, yellow=None, scale=122, an=2, style="Cap",
                       max_lines=2):
        """KARAOKE captions — pura sentence rehta hai, bola ja raha word highlight.

        Jo word abhi bola ja raha hai wo YELLOW + thora bada (\\fscy). Baaki
        WHITE. `\\fscy` use hota hai `\\fs` nahi — kyunki `\\fs` line ko
        reflow karta hai aur text hilti dikhti hai.

        groups: [[(word, start, end), ...], ...]   (global seconds)
        """
        white = white or WHITE
        yellow = yellow or "&H0000D7FF&"
        cx = self.playres[0] // 2
        groups = [[[w, float(s_), float(e_)] for w, s_, e_ in g] for g in groups if g]
        order = [min(x[1] for x in g) for g in groups]
        if order != sorted(order):
            self.warnings.append("caption groups out of order - sorted")
            groups.sort(key=lambda g: min(x[1] for x in g))

        # 1) relative word times monotonic karo
        for g in groups:
            for i in range(len(g) - 1):
                if g[i][2] > g[i + 1][1]:
                    g[i][2] = g[i + 1][1]

        # 2) sentence overlap hatao — agla pichle ke baad hi
        cur = 0.0
        for g in groups:
            if g[0][1] < cur:
                d = cur - g[0][1]
                for w in g:
                    w[1] += d
                    w[2] += d
            cur = g[-1][2] + 0.06

        # 3) display window — koi overlap nahi, last word pura dikhe
        wins = []
        for k, g in enumerate(groups):
            st = g[0][1] - lead
            if k:
                st = max(st, groups[k - 1][-1][2] + 0.02)
            en = g[-1][2] + tail
            if k + 1 < len(groups):
                en = min(en, groups[k + 1][0][1] - lead - 0.02)
            en = max(en, g[-1][2])
            wins.append((st, en))

        n = 0
        for g, (t_start, t_end) in zip(groups, wins):
            _ws = [w for w, _, _ in g]
            lines = (self._kara_wrap(_ws, max_line_chars) if max_lines <= 2
                     else self._kara_wrap_n(_ws, max_line_chars, max_lines))
            for i in range(len(g)):
                a = t_start if i == 0 else max(g[i][1], t_start)
                b = min(g[i + 1][1], t_end) if i + 1 < len(g) else t_end
                if b - a < 0.03:
                    b = a + 0.03
                out, k = [], 0
                for ln in lines:
                    buf = []
                    for _ in range(ln):
                        ww = esc(g[k][0])
                        if k == i:
                            buf.append("{\\c%s\\fscy%d}%s{\\c%s\\fscy100}"
                                       % (yellow, scale, ww, white))
                        else:
                            buf.append(ww)
                        k += 1
                    out.append(" ".join(buf))
                head = ("{\\an%d\\pos(%d,%d)\\fn %s\\fs%d\\bord%d\\shad%d"
                        "\\3c&H000000&\\4c&H000000&\\fsp%s}"
                        % (an, cx, y, font, size, bord, shad, fsp))
                if i == 0:
                    head = head[:-1] + ("\\blur%d\\alpha&HFF&\\t(0,%d,\\blur0"
                                        "\\alpha&H00&)}" % (blur, int(kf / 30.0 * 1000)))
                self.add(a, b, style, head + "\\N".join(out))
                n += 1

        # 4) kooch bhi overlap na ho
        caps = [e for e in self.events if e[3] == style]
        caps.sort(key=lambda e: e[1])
        for i in range(len(caps) - 1):
            if caps[i][2] > caps[i + 1][1]:
                caps[i] = (caps[i][0], caps[i][1], caps[i + 1][1],
                           caps[i][3], caps[i][4])
        # clamp ke baad jo event ulta/zero ho gaya use hata do
        caps = [e for e in caps if e[2] - e[1] >= 0.03]
        self.events = [e for e in self.events if e[3] != style] + caps
        n = len(caps)
        return n

    @staticmethod
    def _kara_wrap(words, maxc):
        """2 line me balanced break — dono line lagbhag barabar."""
        if not words:
            return [0]
        if len(words) <= 1 or len(" ".join(words)) <= maxc:
            return [len(words)]
        best, best_score = None, 1e9
        for k in range(1, len(words)):
            a = " ".join(words[:k]); b = " ".join(words[k:])
            sc = max(len(a), len(b))
            if sc > maxc:
                sc += (sc - maxc) * 4
            if sc < best_score:
                best, best_score = k, sc
        return [best, len(words) - best]

    @staticmethod
    def _kara_wrap_n(words, maxc, max_lines=3):
        """N lines me balanced break (DP). Lambi sentence ke liye — 2 line me
        fit nahi hoti to frame se bahar chali jaati thi."""
        if not words:
            return [0]
        n = len(words)
        if len(" ".join(words)) <= maxc:
            return [n]
        # greedy reference — DP feasible na ho to yahi use hoga
        g, cur = [], []
        for w in words:
            if cur and len(" ".join(cur + [w])) > maxc:
                g.append(len(cur)); cur = [w]
            else:
                cur.append(w)
        if cur:
            g.append(len(cur))
        INF = float("inf")
        best = [[INF] * (max_lines + 1) for _ in range(n + 1)]
        back = [[0] * (max_lines + 1) for _ in range(n + 1)]
        best[0][0] = 0.0
        for i in range(1, n + 1):
            for ln in range(1, max_lines + 1):
                for j in range(i, 0, -1):
                    L = len(" ".join(words[j - 1:i]))
                    if L > maxc and i - j >= 1:
                        cost = 1e6 + (L - maxc) ** 2 * 50
                    else:
                        cost = (maxc - L) ** 2
                    c = best[j - 1][ln - 1] + cost
                    if c < best[i][ln]:
                        best[i][ln] = c
                        back[i][ln] = j
                    if L > maxc:
                        break          # aur lamba sirf bura hoga
        bl, bc = 1, INF
        for ln in range(1, max_lines + 1):
            if best[n][ln] + ln * 3.0 < bc:
                bc, bl = best[n][ln] + ln * 3.0, ln
        if bc >= INF:            # koi valid partition nahi
            return g
        out, i, ln = [], n, bl
        while i > 0 and ln > 0:
            j = back[i][ln]
            if j <= 0:
                return g
            out.append(i - j + 1)
            i, ln = j - 1, ln - 1
        out = out[::-1]
        return out if sum(out) == n else g

    def word_caps_blur(self, groups, y=1260, size=66, font="Inter ExtraBold",
                       max_line_chars=22, max_words=4, blur=30, kf=7,
                       white=None, yellow=None, bord=5, shad=3, hold=0.45,
                       an=2):
        """Word-by-word BLUR-IN captions (reference HekAHosJBOE).

        Har word \\blur30 se aata hai, 7 frames me sharp. Sentence ka colour
        alternate (white/yellow). Naya word DOOSRE colour me aata hai, jab
        agla aata hai to wo base colour pe set ho jata hai.

        groups: [[(word, start, end), ...], ...]   (global seconds)
        """
        white = white or WHITE
        yellow = yellow or "&H0000D7FF&"
        tin = int(round(kf / 30.0 * 1000))
        cx = self.playres[0] // 2
        groups = [[(w, float(s_), float(e_)) for w, s_, e_ in g] for g in groups if g]
        order = [min(x[1] for x in g) for g in groups]
        if order != sorted(order):
            self.warnings.append("caption groups out of order - sorted")
            groups.sort(key=lambda g: min(x[1] for x in g))

        n = 0
        for gi, g in enumerate(groups):
            base = white if gi % 2 == 0 else yellow
            alt = yellow if gi % 2 == 0 else white
            nxt = groups[gi + 1][0][1] if gi + 1 < len(groups) else 1e9

            # line break
            lines, cur, ln = [], [], 0
            for it in g:
                w = it[0]
                if cur and (ln + len(w) + 1 > max_line_chars or len(cur) >= max_words):
                    lines.append(cur); cur, ln = [], 0
                cur.append(it); ln += len(w) + 1
            if cur:
                lines.append(cur)
            flat = [it for L in lines for it in L]

            for idx, (w, ws, we) in enumerate(flat):
                if idx + 1 < len(flat):
                    t_end = min(flat[idx + 1][1], nxt - 0.03)
                else:
                    t_end = min(we + hold, nxt - 0.03)
                if t_end - ws < 0.04:
                    continue
                # kitni line tak dikhana hai
                li = 0
                acc = 0
                for j, L in enumerate(lines):
                    if idx < acc + len(L):
                        li = j
                        break
                    acc += len(L)
                out = []
                for lj in range(li + 1):
                    parts = []
                    for k, item in enumerate(lines[lj]):
                        gidx = sum(len(lines[x]) for x in range(lj)) + k
                        ww = item[0]
                        if gidx < idx:
                            parts.append("{\\c" + base + "}" + esc(ww))
                        elif gidx == idx:
                            parts.append("{\\c" + alt + "\\blur" + str(blur) +
                                         "\\alpha&HFF&\\t(0," + str(tin) +
                                         ",\\blur0\\alpha&H00&)}" + esc(ww))
                        else:
                            break
                    if parts:
                        out.append(" ".join(parts))
                if not out:
                    continue
                txt = "\\N".join(out)
                tags = ("\\an" + str(an) + "\\pos(" + str(cx) + "," + str(y) + ")"
                        "\\fn" + font + "\\fs" + str(size) + "\\b1"
                        "\\bord" + str(bord) + "\\bordcolor&H000000&"
                        "\\shad" + str(shad) + "\\4c&H000000&")
                self.add(ws, t_end, "CapYellow", "{" + tags + "}" + txt)
                n += 1
        return n

    def word_caps(self, chunks, y=1260, size=58, max_line_chars=24, max_words=4,
                  hold=0.40, white=None, yellow=None, outline=10, shadow=4,
                  style="CapYellow"):
        """Reference-shorts captions: **purani line WHITE, current line YELLOW**,
        word-by-word build hoti hui. Koi scale-pop nahi, koi overlap nahi.

        chunks: [[(word, start, end), ...], ...]   har entry = ek narration chunk.
                Times GLOBAL hain (timeline ke seconds).
        """
        white = white or WHITE
        yellow = yellow or "&H0000D7FF&"

        def _line(parts, colour):
            return " ".join("{\\c" + colour + "}" + esc(w) for w, _, _ in parts)

        cx = self.playres[0] // 2
        ev = []
        chunks = [[(w, float(s), float(e)) for w, s, e in ch] for ch in chunks if ch]
        # chunks ka order galat aa sakta hai (narration JSON unsorted) -> warna
        # `nxt` galat nikalta hai aur caption chupchaap gir jaate hain.
        order = [min(w[1] for w in ch) for ch in chunks]
        if order != sorted(order):
            self.warnings.append("narration chunks out of order — sorted by start time")
            chunks.sort(key=lambda ch: min(w[1] for w in ch))
        for ci, ch in enumerate(chunks):
            nxt = chunks[ci + 1][0][1] if ci + 1 < len(chunks) else 1e9
            lines, cur, ln = [], [], 0
            for w, s, e in ch:
                if cur and (ln + len(w) + 1 > max_line_chars or len(cur) >= max_words):
                    lines.append(cur); cur, ln = [], 0
                cur.append((w, s, e)); ln += len(w) + 1
            if cur:
                lines.append(cur)
            for li, line in enumerate(lines):
                prev = lines[li - 1] if li else None
                for wi, (w, s, e) in enumerate(line):
                    t0 = s
                    if wi + 1 < len(line):
                        t1 = line[wi + 1][1]
                    elif li + 1 < len(lines):
                        t1 = lines[li + 1][0][1]
                    else:
                        t1 = min(e + hold, nxt - 0.05)
                    txt = ("{\\c" + white + "}" + _line(prev, white) + "\\N") if prev else ""
                    txt += _line(line[:wi + 1], yellow)
                    ev.append([t0, t1, txt])
        # clamp — koi bhi do caption ek saath na dikhein
        ev.sort(key=lambda x: x[0])
        for i in range(len(ev) - 1):
            if ev[i][1] > ev[i + 1][0] - 0.001:
                ev[i][1] = ev[i + 1][0] - 0.001
        n = 0
        for t0, t1, txt in ev:
            if t1 - t0 < 0.02:
                continue
            tags = (f"\\an5\\pos({cx},{y})\\fs{size}"
                    f"\\bord{outline}\\bordcolor&H000000&"
                    f"\\shad{shadow}\\4c&H000000&\\4a&H70&")
            self.add(t0, t1, style, "{" + tags + "}" + txt)
            n += 1
        return n

    # ------------------------------------------------------- designed blocks
    def center_block(self, start, end, lines, size=88, gap=104, mid_y=880,
                     pop=True, spacing=6):
        """Stacked, centred title lines. A '*' prefix paints that line in accent."""
        n = max(1, len(lines))
        y0 = int(mid_y - (n - 1) * gap / 2)
        for i, line in enumerate(lines):
            y = y0 + i * gap
            acc = line.startswith("*")
            txt = line.lstrip("*")
            tags = f"\\an5\\pos(540,{y})\\fs{size}\\fsp{spacing}"
            if acc:
                tags += f"\\c{self.accent}"
            if pop:
                tags += ("\\fscx92\\fscy92\\alpha&HFF&"
                         "\\t(0,150,\\fscx100\\fscy100\\alpha&H00&)")
            self.add(start + i * 0.07, end, "Title", "{" + tags + "}" + esc(txt))

    def tagline(self, start, end, text, y=372, size=34):
        tags = (f"\\an5\\pos(540,{y})\\fs{size}\\fsp3\\c&HE6E6E6&"
                "\\bord3\\bordcolor&H000000&\\3c&H000000&\\3a&H50&")
        self.add(start, end, "Small", "{" + tags + "}" + esc(text))

    def badge(self, start, end, num, total, x=742, y=1180, size=92, w=170, h=170):
        """Single big rank number in a soft rounded card (used instead of a list)."""
        self.add(start, end, "Title",
                 f"{{\\an7\\pos({x - w // 2},{y - h // 2})\\p1\\c&H0A0A0A&"
                 f"\\alpha&H45&\\bord0\\shad0}}" + rounded_rect(w, h, 34) + "{\\p0}",
                 layer=2)
        self.add(start, end, "Title",
                 f"{{\\an5\\pos({x},{y - 12})\\fs{size}\\b1\\c&HFFFFFF&"
                 f"\\bord0\\shad0}}" + str(num), layer=3)
        self.add(start, end, "Small",
                 f"{{\\an5\\pos({x},{y + h // 2 - 34})\\fs28\\c&HD2D2D2&"
                 f"\\bord0}}" + f"of {total}", layer=3)

    def label_bar(self, start, end, text, x=742, y=1330, size=38, width=320):
        """Small caption bar under the rank badge."""
        h = int(size * 2.1)
        pad = 26
        txt_w = max(90, min(width, int(len(text) * size * 0.52) + pad * 2))
        self.add(start, end, "Title",
                 f"{{\\an7\\pos({x - txt_w // 2},{y - h // 2})\\p1\\c&H0A0A0A&"
                 f"\\alpha&H50&\\bord0\\shad0}}" + rounded_rect(txt_w, h, h // 2)
                 + "{\\p0}", layer=2)
        self.add(start, end, "Small",
                 f"{{\\an5\\pos({x},{y + 2})\\fs{size}\\b1\\c&HFFFFFF&"
                 f"\\bord0}}" + esc(text), layer=3)

    def pill(self, start, end, text, x=110, y=1700, size=32):
        """Small rounded pill, bottom-left. Used when the source shows its own numbers."""
        txt_w = max(80, int(len(text) * size * 0.55) + 44)
        h = int(size * 1.9)
        self.add(start, end, "Title",
                 f"{{\\an7\\pos({x - txt_w // 2},{y - h // 2})\\p1\\c&H000000&"
                 f"\\alpha&H55&\\bord0\\shad0}}" + rounded_rect(txt_w, h, h // 2)
                 + "{\\p0}", layer=2)
        self.add(start, end, "Small",
                 f"{{\\an5\\pos({x},{y + 1})\\fs{size}\\b1\\c&HFFFFFF&\\bord0}}"
                 + esc(text), layer=3)

    def lower_title(self, start, end, text, y=1560, size=54):
        tags = (f"\\an5\\pos(540,{y})\\fs{size}\\b1\\fsp2"
                "\\bord4\\bordcolor&H000000&\\shad0")
        self.add(start, end, "Small", "{" + tags + "}" + esc(text))

    # ------------------------------------------------------------ primitives
    def title(self, start, end, lines, size=112, y=150, style="Title",
              pop=True, spacing=4):
        """Big stacked title, each line popping in 80ms apart."""
        for i, line in enumerate(lines):
            y2 = y + i * int(size * 1.06)
            st = start + i * 0.09
            tags = f"\\an5\\pos(540,{y2})\\fsp{spacing}"
            if pop:
                tags += ("\\fscx70\\fscy70\\alpha&HFF&"
                         f"\\t(0,120,\\fscx106\\fscy106\\alpha&H00&)"
                         f"\\t(120,220,\\fscx100\\fscy100)")
            color = self.accent if line.startswith("*") else None
            txt = line.lstrip("*")
            if color:
                tags += f"\\c{color}"
            self.add(st, end, style, "{" + tags + "}" + esc(txt))

    def sub(self, start, end, text, y=330, size=None, style="Sub"):
        tags = f"\\an5\\pos(540,{y})"
        if size:
            tags += f"\\fs{size}"
        self.add(start, end, style, "{" + tags + "}" + esc(text))

    def captions(self, words, start_off=0.0, style="Cap", hi_style="CapHi",
                 y=1560, max_words=3, max_chars=22, uppercase=True,
                 accent=None):
        """Word-synced pop captions (CapCut style) driven by whisper word times."""
        if not words:
            return
        groups, cur, chars = [], [], 0
        for w in words:
            t = w["w"]
            add = len(t) + 1
            if cur and (len(cur) >= max_words or chars + add > max_chars):
                groups.append(cur)
                cur, chars = [], 0
            cur.append(w)
            chars += add
        if cur:
            groups.append(cur)

        for g in groups:
            gs, ge = g[0]["start"] + start_off, g[-1]["end"] + start_off
            gs, ge = max(gs, 0.05), max(ge, gs + 0.35)
            parts = []
            for i, w in enumerate(g):
                txt = w["w"].upper() if uppercase else w["w"]
                dur_cs = max(4, int(round((w["end"] - w["start"]) * 100)))
                if i == 0:
                    parts.append(f"{{\\kf{dur_cs}}}{esc(txt)}")
                else:
                    parts.append(f" {{\\kf{dur_cs}}}{esc(txt)}")
            body = "".join(parts)
            col = accent or self.accent
            tags = (f"\\an2\\pos(540,{y})\\c&HFFFFFF&\\2c{col}"
                    f"\\fscx88\\fscy88\\t(0,90,\\fscx104\\fscy104)"
                    f"\\t(90,170,\\fscx100\\fscy100)")
            self.add(gs, ge + 0.06, style, "{" + tags + "}" + body)

    def rank_list(self, start, end, items, x=70, y0=760, gap=78, size=44,
                  active=None, done=None, title=None):
        """Left-hand column like '1. 2. 3. 4. 5.' with dim/active states."""
        if title:
            self.add(start, end, "Small",
                     f"{{\\an7\\pos({x},{y0 - 74})\\fs34\\b1\\c&HFFFFFF&}}" + esc(title))
        for i, label in enumerate(items, start=1):
            y = y0 + (i - 1) * gap
            st = "Rank" if (active is None or i <= len(items)) else "RankDim"
            col = "&HFFFFFF&" if (active is None or i <= active) else "&H7A7A7A&"
            if done and i in done:
                col = "&H59B0E0&"   # dim gold-ish
            mark = ""
            size_i = size
            if active == i:
                col = self.accent.replace("&H", "&H")
                size_i = int(size * 1.22)
                mark = "\\b1"
            self.add(start, end, st,
                     f"{{\\an7\\pos({x},{y})\\fs{size_i}{mark}\\c{col}}}"
                     f"{i}. {esc(label)}")

    def chip(self, start, end, text, x=70, y=140, size=34, pad=18,
             color="&H90000000&"):
        self.add(start, end, "Chip",
                 f"{{\\an7\\pos({x},{y})\\fs{size}\\bord{pad}\\4c{color}"
                 f"\\4a&H30&}}" + esc(text))

    def panel(self, start, end, x, y, w, h, alpha="&H55&", color="&H000000&",
              layer=1, radius=0):
        draw = f"m 0 0 l {w} 0 l {w} {h} l 0 {h}"
        self.add(start, end, "Title",
                 f"{{\\an7\\pos({x},{y})\\p1\\c{color}\\alpha{alpha}"
                 f"\\bord0\\shad0}}" + draw + "{\\p0}", layer=layer)

    def watermark(self, text, x=1040, y=1860, size=34):
        self.add(0.2, 999, "Watermark",
                 f"{{\\an9\\pos({x},{y})\\fs{size}\\bord3"
                 f"\\bordcolor&H000000&\\1c&HFFFFFF&\\1a&H40&}}" + esc(text), layer=7)

    def boom_word(self, start, dur, text="BOOM!", y=900, size=150, x=540):
        tags = (f"\\an5\\pos({x},{y})\\fs{size}\\c{self.accent}\\bord10"
                f"\\fscx40\\fscy40\\alpha&HFF&"
                f"\\t(0,110,\\fscx118\\fscy118\\alpha&H00&)"
                f"\\t(140,240,\\fscx100\\fscy100)"
                f"\\t({int(dur * 900)},{int(dur * 1000)},\\alpha&HFF&)")
        self.add(start, start + dur, "Title", "{" + tags + "}" + esc(text), layer=3)

    def progress_ticks(self, start, end, n, x=70, y=1700, gap=44, size=30):
        for i in range(n):
            self.add(start, end, "Small",
                     f"{{\\an7\\pos({x + i * gap},{y})\\fs{size}\\c&HFFFFFF&}}•",
                     layer=1)

    # ------------------------------------------------------------ output
    def write(self, path, styles=None, t1=112, t2=54, t3=76, t4=44, t5=34, t6=30,
              h1=54, a1=40, i1=96, d1=54, r1=64, r2=40, cy=38):
        st = BASE_STYLES.format(out=8, outc=7, accent=self.accent,
                                t1=t1, t2=t2, t3=t3, t4=t4, t5=t5, t6=t6,
                                h1=h1, a1=a1, i1=i1, d1=d1, r1=r1, r2=r2, cy=cy)
        ev = []
        for layer, a, b, style, text in sorted(self.events, key=lambda e: (e[0], e[1])):
            ev.append(f"Dialogue: {layer},{_ts(a)},{_ts(b)},{style},,0,0,0,,{text}")
        px, py = self.playres
        open(path, "w").write(HEADER.format(px=px, py=py, styles=st,
                                            events="\n".join(ev)))
        return path


def ass_filter(path):
    return (f"ass={path}:fontsdir={FONT_DIR}:shaping=complex")
