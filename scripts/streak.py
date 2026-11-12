import os, json, urllib.request, datetime as dt

TOKEN = os.environ["GITHUB_TOKEN"]
USER = os.environ.get("GH_USER", "bagasadh")

def gql(q, v):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": v}).encode(),
        headers={"Authorization": "bearer " + TOKEN},
    )
    return json.load(urllib.request.urlopen(req))["data"]

# Zona waktu WIB (UTC+7)
WIB = dt.timezone(dt.timedelta(hours=7))
now_utc = dt.datetime.now(dt.timezone.utc)
now_wib = now_utc.astimezone(WIB)
now = now_wib.replace(tzinfo=None)

created = gql("query($u:String!){user(login:$u){createdAt}}", {"u": USER})["user"]["createdAt"][:4]
Q = "query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"

days = {}
for y in range(int(created), now.year + 1):
    f = "%d-01-01T00:00:00Z" % y
    t = min(dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now_utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cal = gql(Q, {"u": USER, "f": f, "t": t})["user"]["contributionsCollection"]["contributionCalendar"]
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]

dates = sorted(dt.date.fromisoformat(k) for k in days)
today = now.date()

best = (0, None, None)
run = 0
start = None
prev = None
for d in dates:
    if days[d.isoformat()] > 0:
        if run == 0 or prev is None or (d - prev).days != 1:
            run, start = 0, d
        run += 1
        prev = d
        if run > best[0]:
            best = (run, start, d)
    else:
        run = 0
        prev = None

cur = (0, None, None)
d = today
if days.get(d.isoformat(), 0) == 0:
    d -= dt.timedelta(days=1)
end = d
n = 0
while days.get(d.isoformat(), 0) > 0:
    n += 1
    d -= dt.timedelta(days=1)
if n:
    cur = (n, d + dt.timedelta(days=1), end)

def rng(s, e):
    if not s:
        return "-"
    if s == e:
        return s.strftime("%b %d")
    return s.strftime("%b %d") + " - " + e.strftime("%b %d")

D = "stroke:#24292f;stroke-opacity:0.8;stroke-width:3.5;stroke-dasharray:11.5 4;stroke-dashoffset:1"
W = """stroke="#ffffff" stroke-width="1.5" stroke-dasharray="9.5 6\""""
def line(x1, y1, x2, y2):
    return """<line x1="%s" y1="%s" x2="%s" y2="%s" style="%s"/><line x1="%s" y1="%s" x2="%s" y2="%s" %s/>""" % (x1, y1, x2, y2, D, x1, y1, x2, y2, W)

H = 170
T = H + 36
s = """<svg xmlns="http://www.w3.org/2000/svg" width="566" height="%d" viewBox="-3 -3 566 %d"><g font-family="JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="15" fill="#ffffff">""" % (T, T)
s += """<rect x="1" y="1" width="558" height="%d" rx="6" fill="none" style="%s"/>""" % (H, D)
s += """<rect x="1" y="1" width="558" height="%d" rx="6" fill="#000000" fill-opacity="0.5" stroke="#ffffff" stroke-width="1.5" stroke-dasharray="9.5 6"/>""" % H
s += """<text x="280" y="30" text-anchor="middle">Streak</text>"""
s += line(1, 44, 559, 44)
s += """<text x="140.5" y="66" text-anchor="middle">Current streak</text><text x="419.5" y="66" text-anchor="middle">Longest streak</text>"""
s += line(1, 78, 559, 78)
s += line(280, 44, 280, H + 1)
for cx, data in ((140.5, cur), (419.5, best)):
    s += """<text x="%s" y="124" text-anchor="middle" font-size="34" font-weight="bold">%d</text>""" % (cx, data[0])
    s += """<text x="%s" y="146" text-anchor="middle">days</text>""" % cx
    s += """<text x="%s" y="164" text-anchor="middle" font-size="12" fill="#8b949e">%s</text>""" % (cx, rng(data[1], data[2]))
s += "</g></svg>"
os.makedirs("assets", exist_ok=True)
open("assets/streak-card.svg", "w", encoding="utf-8").write(s)
print("current", cur[0], "longest", best[0])

