"""Pack the tour into ONE html file: plan data and panoramas inlined, so it opens by double-click (no server).
Only Three.js and the font still come from their CDNs.

  python3 tools/build_standalone.py OUT.html
"""
import base64, os, re, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
html = open(os.path.join(root, "index.html"), encoding="utf-8").read()
home = open(os.path.join(root, "home.js"), encoding="utf-8").read()
panos = sorted(f for f in os.listdir(os.path.join(root, "panos")) if f.endswith(".jpg"))
data = ",\n".join('  %d: "data:image/jpeg;base64,%s"' % (int(re.search(r"(\d+)", f).group(1)),
                   base64.b64encode(open(os.path.join(root, "panos", f), "rb").read()).decode()) for f in panos)

html = html.replace('<script src="home.js"></script>', "<script>\n" + home + "window.PANOS = {\n" + data + "\n};\n</script>")
old = 'const panoSrc = (n) => `panos/pano${String(n).padStart(2, "0")}.jpg`;'
assert old in html
html = html.replace(old, 'const panoSrc = (n) => window.PANOS ? window.PANOS[n] : `panos/pano${String(n).padStart(2, "0")}.jpg`;')
guard = '  if (location.protocol === "file:") { $("load").textContent = "این صفحه را با یک سرور محلی باز کنید (python3 -m http.server)."; return; }\n'
assert guard in html
html = html.replace(guard, "")
open(sys.argv[1], "w", encoding="utf-8").write(html)
print(sys.argv[1], round(os.path.getsize(sys.argv[1]) / 1e6, 1), "MB")
