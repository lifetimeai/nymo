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


def ok(was: str, gut: bool, mehr: str = "", pflicht: bool = True):
    """pflicht=False: nur Hinweis (WARN), haelt den Installer nicht auf"""
    print(f"[{'OK  ' if gut else 'FEHL' if pflicht else 'WARN'}] {was}{(' -- ' + mehr) if mehr else ''}", flush=True)
    if not gut and pflicht:
        fehler.append(was)


def lauf(cmd, timeout=300, **kw):
    r = subprocess.run(cmd, capture_output=True, timeout=timeout, **kw)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


print(f"Paket: {N}  (Python {sys.version.split()[0]}, {sys.executable})")
ok("mitgeliefertes Python", PY.is_file() and (N / "python" / "pythonw.exe").is_file())
ok("Startdateien", all((N / f).is_file() for f in ("nymo.py", "nymo.pyw", "nymo starten.bat", "oberflaeche.html")))

# Windows-App (app-win/baue.sh): Fenster und Schild gebaut; das Schild startet, meldet sich ("bereit", alle 100 ms
# "lebt") und endet, sobald seine Leitung (stdin) zugeht -- so wie nymo.exe es startet und bewacht (wache.cs).
# Der Lauf des Schilds ist vorerst nur Hinweis (WARN): ob der Runner eine Oberflaeche hat, ist nicht sicher.
FENSTER = N / "app-win" / "fenster"
ok("Windows-App gebaut (nymo.exe, nymo-schild.exe)", (FENSTER / "nymo.exe").is_file() and (FENSTER / "nymo-schild.exe").is_file())
if (FENSTER / "nymo-schild.exe").is_file():
    import threading
    zeilen = []
    try:
        schild = subprocess.Popen([str(FENSTER / "nymo-schild.exe"), "--nymo", "0"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, cwd=str(FENSTER))
        threading.Thread(target=lambda: [zeilen.append(z.decode("utf-8", "replace")) for z in schild.stdout], daemon=True).start()
        bis = time.time() + 30
        while time.time() < bis and sum('"lebt"' in z for z in zeilen) < 5:
            time.sleep(0.2)
        ok("Schild startet und meldet sich", any('"bereit"' in z for z in zeilen) and sum('"lebt"' in z for z in zeilen) >= 5,
           f"{len(zeilen)} Zeilen", pflicht=False)
        schild.stdin.close()
        try:
            schild.wait(10)
            ok("Schild endet mit seiner Leitung", True, pflicht=False)
        except subprocess.TimeoutExpired:
            schild.kill()
            ok("Schild endet mit seiner Leitung", False, "lief nach 10 s noch", pflicht=False)
    except OSError as ex:
        ok("Schild startet und meldet sich", False, str(ex), pflicht=False)

# OCR-Pakete im mitgelieferten Python
code, out = lauf([str(PY), "-I", "-c", "import rapidocr, onnxruntime, pypdfium2, docx; print('ok')"])
ok("OCR-Pakete (rapidocr, onnxruntime, pypdfium2, python-docx)", code == 0 and "ok" in out, out.strip()[-300:] if code else "")

# Poppler
code, out = lauf([str(N / "poppler" / "Library" / "bin" / "pdftotext.exe"), "-v"], 60)
ok("Poppler pdftotext", code == 0 and "pdftotext" in out, out.strip()[:120])

# Tesseract (mitgeliefert seit 10.11.2026, am Mac nur zusammenkopiert -- hier startet es zum ersten Mal)
TESS = N / "tesseract"
tess_env = dict(os.environ, TESSDATA_PREFIX=str(TESS / "tessdata"))
try:
    code, out = lauf([str(TESS / "tesseract.exe"), "--version"], 60, env=tess_env)
except OSError as ex:
    code, out = 1, str(ex)
ok("Tesseract startet", code == 0 and "tesseract" in out.lower(), out.strip()[:120])
try:
    code, out = lauf([str(TESS / "tesseract.exe"), "--list-langs"], 60, env=tess_env)
except OSError as ex:
    code, out = 1, str(ex)
ok("Tesseract mit Deutsch", code == 0 and "deu" in out.split(), " ".join(out.split())[:120])

# nymo-Module und KI-Erkennung (laeuft in diesem Python, wie nymo selbst)
sys.path.insert(0, str(N))
os.chdir(N)
try:
    import werkzeuge, ki_erkennung, nymo  # noqa: E402
    ok("nymo-Module importierbar", True, f"nymo {nymo.VERSION}")
    ok("werkzeuge.eingebettet()", werkzeuge.eingebettet())
    werkzeuge.pfade_ergaenzen()
    ok("Poppler im Suchpfad", bool(shutil.which("pdftoppm") and shutil.which("pdftotext")), shutil.which("pdftoppm") or "")
    ok("Tesseract im Suchpfad (das mitgelieferte)", Path(shutil.which("tesseract") or "").parent == TESS, shutil.which("tesseract") or "")
    # Mischweg an einer Probezeile: Tesseract liest, RapidOCR liest die Zeile nach. Vorerst nur Hinweis (WARN): der
    # Lauf ist neu, ein Fehler hier soll den Installer nicht aufhalten -- nymo faellt dann auf RapidOCR allein zurueck.
    try:
        import tempfile
        from PIL import Image, ImageDraw, ImageFont
        ocr = nymo.ocr_prep()
        probe = Image.new("L", (1800, 260), 255)
        schrift = next((ImageFont.truetype(f, 54) for f in ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/arial.ttf")
                        if Path(f).exists()), None) or ImageFont.load_default(54)
        ImageDraw.Draw(probe).text((60, 90), "Frau Anna Lindqvist, Marienstraße 4, 21335 Lüneburg", font=schrift, fill=0)
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "probe.png"
            probe.save(png)
            t0 = time.time()
            text, konf, zeilen = ocr.tesseract_seite(png, "deu", zeilen=True)
            d1 = time.time() - t0
        # "Lindqvist" liest Tesseract am Mac als "Lindgvist" (Sicherheit 93) -- genau das soll das Nachlesen richten
        ok("Tesseract liest die Probezeile", "Marienstraße" in text and "Lüneburg" in text, f"{d1:.1f} s, Sicherheit {konf:.0f}: {text.strip()[:80]}",
           pflicht=False)
        t0 = time.time()
        neu, stand = ocr.zeilen_nachlesen(probe, text, zeilen, lambda z: True)
        ok("RapidOCR liest die Zeile nach (Mischweg)", stand["nachgelesen"] >= 1 and "Lindqvist" in neu,
           f"{time.time() - t0:.1f} s, {stand}: {neu.strip()[:80]}", pflicht=False)
    except Exception as ex:  # noqa: BLE001
        ok("Mischweg an der Probezeile", False, f"{type(ex).__name__}: {ex}", pflicht=False)
    # Pflicht ist nur, dass RapidOCRs Lesemodell fuer einzelne Zeilen ueberhaupt antwortet (ocr.rapid_zeilen nutzt
    # Innereien von RapidOCR): sonst liest nymo jede Seite doppelt (Tesseract, dann RapidOCR ganz) -- langsamer als vorher.
    try:
        import numpy
        gelesen = nymo.ocr_prep().rapid_zeilen([numpy.full((48, 320, 3), 255, dtype=numpy.uint8)])
        ok("RapidOCR-Lesemodell fuer Zeilen", len(gelesen) == 1, str(gelesen)[:80])
    except Exception as ex:  # noqa: BLE001
        ok("RapidOCR-Lesemodell fuer Zeilen", False, f"{type(ex).__name__}: {ex}")
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
