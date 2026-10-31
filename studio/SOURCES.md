# CLIP SOURCES — jo aaj test hue (2026-10-24)

Sab kuch sandbox se **actually download karke** check kiya — sirf "200 OK" nahi, file khuli, ffprobe chalaya.
Ek command har source ke liye: `python3 studio/srcget.py <source> <arg>`

```bash
python3 srcget.py tiktok  https://www.tiktok.com/@espn/video/7488031370086780190
python3 srcget.py pexels  5039768
python3 srcget.py coverr  "skateboard fall" 4
python3 srcget.py mixkit  fail 3
python3 srcget.py imgur   funny 3
python3 srcget.py wiki    "crash test" 3
python3 srcget.py peertube "bicycle" 2
python3 srcget.py ia      "fail" 2
python3 srcget.py nbc     https://www.today.com/video/...
python3 srcget.py vimeo   76979871
```

Sab `~/dl/src/<source>/` me girta hai. Output line: `OK  <path>  <WxH>  <sec>`

---

## Chalte hain (file aayi)

| # | Source | Kya milta hai | Quality (aaj mila) | Kaise | Type 1/2/3 |
|---|---|---|---|---|---|
| 1 | **TikTok** | asli viral clips, **vertical** | 1080×1920 / 720×1280 | full page ka `__UNIVERSAL_DATA_FOR_REHYDRATION__` → `bitrateInfo` → sabse badi gear ka `PlayAddr.UrlList` | 2 (ranking), 3 (verticals) |
| 2 | **Pexels** | stock + AI b-roll, 4K | 4096×2160, 3840×2160 | `pexels.com/download/video/<id>/` → 302 → `videos.pexels.com` | 1 (b-roll), 2 |
| 3 | **Coverr** | stock, **API search** | 1080p (kabhi 1080×1080) | `coverr.co/api/videos?query=<q>` → `base_filename` → `cdn.coverr.co/videos/<bf>/1080p.mp4` | 1, 2 |
| 4 | **Mixkit** | stock | 1280×720 | `mixkit.co/free-stock-video/<slug>/` → `assets.mixkit.co/videos/<id>/<id>-720.mp4` | 1 (b-roll) |
| 5 | **Imgur** | asli UGC clips, meme/fail | 482×854 – 854×854 | `api.imgur.com/3/gallery/t/<tag>/1` (Client-ID `546c25a59c58ad7`) → `i.imgur.com/<id>.mp4` | 2, 3 |
| 6 | **Internet Archive** | poori fail compilations, archival | 360–720p | `archive.org/advancedsearch.php` → `/metadata/<id>` → `/download/...` | 2 (clip nikalna), 1 (archival) |
| 7 | **Wikimedia Commons** | CC videos, crash tests, archival | 1280×720 – 1920×1080 | `commons.wikimedia.org/w/api.php?generator=search&gsrnamespace=6` → `upload.wikimedia.org` | 1 (b-roll), 3 |
| 8 | **PeerTube** (public instances) | long-form CC videos | up to 1080p | `<instance>/api/v1/search/videos?search=` → `/api/v1/videos/<uuid>` → `files[].fileUrl` | 1, 3 |
| 9 | **NBC / Today** | news + viral footage | **1920×1080** | page HTML me direct `.mp4` (`akamaized`, `nbcuni`) | 1, 2 |

**Proof (aaj ke actual downloads):**

```
OK  dl/src/tiktok/tt_7488031370086780190.mp4    1080x2028   8.60s
OK  dl/src/pexels/px_5039768.mp4                4096x2160   9.00s   (cleanup me hata diya)
OK  dl/src/coverr/cv_..._1080p.mp4              1080x1080   5.04s
OK  dl/src/mixkit/mk_23926_720.mp4              1280x720   13.64s
OK  dl/src/imgur/eNiS8fD.mp4                     854x854   47.14s
OK  dl/src/wiki/Crash_Testing_an_Ambulance.webm 1920x1080  443.80s  (cleanup me hata diya)
OK  dl/src/news/news_807385155683.mp4           1920x1080   39.61s
OK  dl/src/archive/Most_underride_guards...mp4    640x360  187.87s  (cleanup me hata diya)
```

---

## Aadhe-adhoore (kaam karte hain, par limit hai)

| Source | Problem |
|---|---|
| **Dailymotion** | `dailymotion.com/player/metadata/video/<id>` → HLS chalta hai, par jo 139 videos scan hui unme **sabse achhi 512×288**. 720p+ nahi mila. Sirf last-resort. |
| **Vimeo** | `player.vimeo.com/video/<id>/config` chalta hai, par files `separate_av` + DRM — 76979871 par HLS fail. DRM-free video par progressive mp4 milta hai. ID chahiye. |

---

## Band / dead — dobara mat try karo

| Source | Kya hua |
|---|---|
| **YouTube** | SABR force — 11 client, PO token, cookies, sab fail. Home IP chahiye. |
| **Reddit** | `www.reddit.com/*.json` = **403**, safereddit = Anubis proof-of-work |
| **Twitter / X** | `syndication.twitter.com` = **429**, nitter/xcancel sab dead, fxtwitter ko tweet ID chahiye |
| **Instagram** | embed 200 deta hai par andar video URL nahi nikalta |
| **Snapchat** | spotlight page **404** |
| **Rumble** | site 403, embed 410 |
| **VK** | redirect loop |
| **Rutube** | API **401** |
| **Bilibili** | **412** (region block) |
| **Twitch clips** | API HTML return karta hai, JSON nahi |
| **Pixabay** | site **403**, CDN guess 404 |
| **Videvo / Mazwai** | **403** |
| **Videezy** | 200 par sirf apna masthead mp4; download login maangta hai |
| **Storyblocks / Pond5 / MotionArray** | watermark ya 403 |
| **Giphy / Tenor API** | public keys **403** |
| **Odysee / LBRY** | API HTML shell deta hai |

---

## Kaun kis type ke liye

**Type 1 (b-roll / scene building)**
Pexels → Coverr → Mixkit → Wikimedia → PeerTube → NBC

**Type 2 (ranking / fail moments)**
TikTok → Imgur → Internet Archive → Pexels → NBC

**Type 3 (vertical / person-led)**
TikTok (native 1080×1920, no crop needed) → Imgur (854 vertical) → Coverr (1080×1080 square)

**Rule jo aaj confirm hua:** vertical source > landscape. Landscape ko 1080×1428 me daalne par sirf 42% width bachti hai — subject frame se bahar chala jaata hai. Vertical/tiktok clips me poori width dikhti hai.

---

## Note

TikTok ka **web player** version download hota hai — usme `@user` watermark nahi hota. Creator ka apna burned-in caption aa sakta hai (source ka hissa hai, chhedna nahi).

---

## 2026-10-24 — SOURCING POLICY (user ka naya rule)

**Problem jo user ne pakda:** "pure internet se gin-chun ke sourcing kar rahe ho, wo bhi dikkat de raha hai."
Matlab: random repost = claim + reused-content ka risk. Ab **tiered** sourcing:

### Tier 1 — ZERO risk (default yahi)
| Source | Kaise | Fail footage? |
|---|---|---|
| **Pexels** | `srcget.py pexels <id>` | Thoda (skatepark, sport) |
| **Mixkit** | `assets.mixkit.co/videos/<id>/<id>-720.mp4` | Kam |
| **Coverr** | API `hits[].base_filename` | B-roll zyada, fail kam |
| **Pixabay** | site 403 — sirf CDN direct URL | — |

License: commercial ok, **credit nahi chahiye**, Content ID nahi. Yahan se claim nahi aata.

### Tier 2 — documented license
Wikimedia Commons · Archive.org (public domain items) · PeerTube instances · Openverse.
**Rule:** file ka license page check karo, CC0/CC BY/PD ho tabhi lo.

### Tier 3 — creator clips (sirf zaroorat pade to)
Chhote individual creators. **Bade compilation pages = BAND** — ESPN, FailArmy, House of Highlights, Woah Dude, SportsNation etc. Unke paas Content ID + Copyright Match Tool hai, automatic pakad lega.

### Naya pre-download check
Har clip download ke baad **6-frame strip** dekho aur ye reject karo:
- burned caption / "WAIT FOR IT" / meme text
- kisi platform ka handle ya logo (`@daztok`, `@espn`)
- duotone/subtitle bars

Rule: **text mila = clip reject, baad me hataane ka jhanjhat nahi.** (User: "aage se koi text ho to hata diya karna" = source hi na lo.)
