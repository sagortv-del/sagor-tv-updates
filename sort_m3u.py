#!/usr/bin/env python3
"""
M3U সাজানোর স্ক্রিপ্ট: বাংলাদেশ -> ইন্ডিয়া -> খেলা -> বাকি সব।

ব্যবহার:
    python3 sort_m3u.py                      # সরাসরি লিংক থেকে নামিয়ে sorted.m3u বানাবে
    python3 sort_m3u.py input.m3u out.m3u    # লোকাল ফাইল থেকে
"""
import re
import sys
import urllib.request

URL = "https://raw.githubusercontent.com/iptvmaxmupro/Iptvmaxm3upro/refs/heads/main/filex.m3u"

# নিচের লিস্টগুলো নিজের মতো বদলাতে পারবেন (বড় হাতের অক্ষরে লিখুন)
BANGLADESH = [
    r"\bBD\b", r"BANGLADESH", r"BANGLA", r"BENGALI",
    "SOMOY", "JAMUNA", "CHANNEL I", "CHANNEL 24", "GAZI", "GTV", "BTV",
    "ATN", "NTV", "RTV", "EKATTOR", "DBC", "DEEPTO", "MAASRANGA",
    "NAGORIK", "BOISHAKHI", "EKUSHEY", "SANGSAD", "T SPORTS", "T-SPORTS",
    "INDEPENDENT TV", "NEWS24", "DESH TV", "MY TV", "MOHONA",
]
INDIA = [
    r"^IND\b", r"\bIND\s*\|", r"\bIN\s*\|", "INDIA", "HINDI", "BOLLYWOOD",
    "MALAYALAM", "TAMIL", "TELUGU", "KANNADA", "MARATHI",
    "STAR PLUS", "ZEE ", "SONY", "COLORS", "STAR SPORTS", "STAR GOLD",
]
CRICKET = ["CRICKET", r"\bIPL\b", "PSL", "BBL", "ASTRO CRICKET"]
SPORTS = [
    "SPORT", "SOCCER", "FOOTBALL", "FORMULA", r"\bF1\b", "UFC", "WWE", "NBA",
    "NFL", "TENNIS", "GOLF", "HORSE", "RACING", "BEIN", "PREMIER LEAGUE",
    "EFL", "LA LIGA", "SERIE A", "BUNDESLIGA", "CHAMPIONS LEAGUE", "ESPN",
    "FOX SOCCER", "TNT", "DAZN", "EUROSPORT", "PARAMOUNT",
]


def compile_list(items):
    return re.compile("|".join(items))


RE_BD = compile_list(BANGLADESH)
RE_IN = compile_list(INDIA)
RE_CRICKET = compile_list(CRICKET)
RE_SPORT = compile_list(SPORTS)


def parse(text):
    """#EXTINF থেকে URL লাইন পর্যন্ত প্রতিটি চ্যানেলকে একটি এন্ট্রি ধরে।"""
    entries, block = [], []
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.strip() or line.startswith("#EXTM3U"):
            continue
        block.append(line)
        if not line.startswith("#"):  # URL লাইন = এন্ট্রি শেষ
            entries.append(block)
            block = []
    return entries  # শেষে URL ছাড়া ভাঙা এন্ট্রি থাকলে বাদ যায়


def info(entry):
    head = next((l for l in entry if l.startswith("#EXTINF")), "")
    m = re.search(r'group-title="([^"]*)"', head)
    group = m.group(1) if m else ""
    name = head.rsplit(",", 1)[-1] if "," in head else ""
    return group.upper(), name.upper()


def tier(group, name):
    both = f"{group} | {name}"
    if RE_BD.search(both):
        return 0
    if RE_IN.search(group) or RE_IN.search(name):
        # ইন্ডিয়ার খেলার চ্যানেল খেলার ট্যাগেই থাকবে, তাই এখানে আগে চেক
        if not RE_SPORT.search(group):
            return 1
    if RE_CRICKET.search(both):
        return 2
    if RE_SPORT.search(both):
        return 3
    return 4


def main():
    if len(sys.argv) >= 2:
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            text = f.read()
        out_path = sys.argv[2] if len(sys.argv) > 2 else "sorted.m3u"
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        out_path = "sorted.m3u"

    entries = parse(text)

    # প্রতিটি গ্রুপ প্রথম কোথায় এসেছে তা মনে রাখি, যাতে গ্রুপগুলো একসাথে থাকে
    first_seen = {}
    for i, e in enumerate(entries):
        first_seen.setdefault(info(e)[0], i)

    def key(item):
        idx, e = item
        g, n = info(e)
        return (tier(g, n), first_seen[g], idx)

    ordered = [e for _, e in sorted(enumerate(entries), key=key)]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for e in ordered:
            f.write("\n".join(e) + "\n")

    counts = {}
    for e in entries:
        t = tier(*info(e))
        counts[t] = counts.get(t, 0) + 1
    labels = {0: "বাংলাদেশ", 1: "ইন্ডিয়া", 2: "ক্রিকেট", 3: "অন্যান্য খেলা", 4: "বাকি"}
    print(f"মোট চ্যানেল: {len(entries)} -> {out_path}")
    for t in sorted(counts):
        print(f"  {labels[t]}: {counts[t]}")


if __name__ == "__main__":
    main()
