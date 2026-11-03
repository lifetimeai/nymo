r"""Windows-Paket pruefen, bevor der Installer gebaut wird (GitHub Actions, installer.yml) -- oder von Hand auf
einem Windows-Rechner im entpackten Zip:

    python\python.exe -I app-win\installer\pruefe.py .

Prueft mit dem mitgelieferten Python: OCR-Pakete, Poppler, nymo-Module, die mitgelieferte KI-Erkennung
(Hintergrundprozess, Probesatz) und den Start des nymo-Servers (/api/hallo). Jeder Fehler beendet mit
Rueckgabe 1 -- dann gibt es keinen Installer fuer dieses Paket.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

N = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()       # der Ordner nymo\ des Pakets
PY = N / "python" / "python.exe"
fehler = []


def ok(was: str, gut: bool, mehr: str = ""):
    print(f"[{'OK  ' if gut else 'FEHL'}] {was}{(' -- ' + mehr) if mehr else ''}", flush=True)
    if not gut:
        fehler.append(was)


def lauf(cmd, timeout=300, **kw):
    r = subprocess.run(cmd, capture_output=True, timeout=timeout, **kw)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


print(f"Paket: {N}  (Python {sys.version.split()[0]}, {sys.executable})")
ok("mitgeliefertes Python", PY.is_file() and (N / "python" / "pythonw.exe").is_file())
ok("Startdateien", all((N / f).is_file() for f in ("nymo.py", "nymo.pyw", "nymo starten.bat", "oberflaeche.html")))

# OCR-Pakete im mitgelieferten Python
code, out = lauf([str(PY), "-I", "-c", "import rapidocr, onnxruntime, pypdfium2, docx; print('ok')"])
ok("OCR-Pakete (rapidocr, onnxruntime, pypdfium2, python-docx)", code == 0 and "ok" in out, out.strip()[-300:] if code else "")

# Poppler
code, out = lauf([str(N / "poppler" / "Library" / "bin" / "pdftotext.exe"), "-v"], 60)
ok("Poppler pdftotext", code == 0 and "pdftotext" in out, out.strip()[:120])

# nymo-Module und KI-Erkennung (laeuft in diesem Python, wie nymo selbst)
sys.path.insert(0, str(N))
os.chdir(N)
try:
    import werkzeuge, ki_erkennung, nymo  # noqa: E402
    ok("nymo-Module importierbar", True, f"nymo {nymo.VERSION}")
    ok("werkzeuge.eingebettet()", werkzeuge.eingebettet())
    werkzeuge.pfade_ergaenzen()
    ok("Poppler im Suchpfad", bool(shutil.which("pdftoppm") and shutil.which("pdftotext")), shutil.which("pdftoppm") or "")
    ok("KI-Erkennung mitgeliefert", ki_erkennung.mitgeliefert())
    ok("KI-Erkennung eingerichtet()", ki_erkennung.eingerichtet(), json.dumps(ki_erkennung.bereit_info())[:200])
    t0 = time.time()
    ki = ki_erkennung.KiErkennung()
    try:
        spans = ki.finde("Frau Anna Lindqvist aus der Marienstraße 4 in 21335 Lüneburg hat angerufen.")
        person = [s["text"] for s in spans if s["label"] == "person"]
        adresse = [s["text"] for s in spans if s["label"] == "address"]
        ok("KI-Erkennung Probesatz", bool(person) and bool(adresse),
           f"{time.time() - t0:.0f} s, person={person}, address={adresse}, stand={ki.stand}")
    finally:
        ki.beenden()
except Exception as ex:  # noqa: BLE001
    ok("nymo-Module / KI-Erkennung", False, f"{type(ex).__name__}: {ex}")

# Server starten und /api/hallo fragen (ohne Browser, eigener Akten-Ordner)
akten, kiordner = N.parent / "Akten-Test", N.parent / "KI-Test"      # getrennt (Konfig.pruefe), nicht ineinander
akten.mkdir(exist_ok=True); kiordner.mkdir(exist_ok=True)
proc = subprocess.Popen([str(PY), "-I", str(N / "nymo.py"), "start", "--kein-browser", "--port", "8799",
                         "--akten", str(akten), "--ki", str(kiordner)], cwd=str(N),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
antwort, ausgabe = None, b""
try:
    for _ in range(60):
        time.sleep(1)
        if proc.poll() is not None:
            break
        try:
            with urllib.request.urlopen("http://127.0.0.1:8799/api/hallo", timeout=2) as r:
                antwort = json.loads(r.read().decode("utf-8"))
            break
        except Exception:  # noqa: BLE001
            continue
finally:
    if proc.poll() is None:
        proc.kill()
    try:
        ausgabe = proc.communicate(timeout=10)[0]
    except Exception:  # noqa: BLE001
        pass
ok("nymo-Server antwortet (/api/hallo)", bool(antwort) and antwort.get("nymo") == nymo.VERSION,
   json.dumps(antwort) if antwort else ausgabe.decode("utf-8", "replace")[-600:])

print()
print("Alles in Ordnung." if not fehler else "Fehler: " + ", ".join(fehler))
sys.exit(1 if fehler else 0)
