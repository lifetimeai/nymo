# nymo

nymo schwärzt Namen und persönliche Angaben in Akten, bevor Claude sie liest. Es läuft nur auf dem eigenen Rechner, nichts geht ins Internet.

**Download für Windows 10 und 11:** [nymo-setup.exe](https://github.com/lifetimeai/nymo/releases/latest/download/nymo-setup.exe) (Installer, rund 0,7 GB)

Der Installer bringt alles mit: Python, Poppler, die Texterkennung für Scans (RapidOCR) und die KI-Erkennung mit dem Sprachmodell. Keine Administrator-Rechte nötig, nichts weiter zu installieren.

1. `nymo-setup.exe` herunterladen und doppelklicken. Windows warnt eventuell beim ersten Start („Windows hat den Start einer unbekannten App verhindert“): „Weitere Informationen“ → „Trotzdem ausführen“.
2. Dem Setup folgen. nymo landet in `AppData\Local\Programs\nymo` des angemeldeten Benutzers, mit Verknüpfung „nymo“ im Startmenü und auf dem Schreibtisch.
3. nymo starten. Beim ersten Start lädt es die KI-Erkennung, das dauert einmalig bis zu zwei Minuten.

**Ohne Installation:** [nymo-windows.zip](https://github.com/lifetimeai/nymo/releases/latest/download/nymo-windows.zip) in einen kurzen Ordner entpacken (etwa `C:\Users\<name>\nymo`, nicht in OneDrive) und im Ordner `nymo` doppelt auf „nymo starten“ klicken.

**Prüfsummen (SHA-256):** [SHA256SUMS.txt](https://github.com/lifetimeai/nymo/releases/latest/download/SHA256SUMS.txt) zu jedem Release. Prüfen in PowerShell: `Get-FileHash nymo-setup.exe`.

**Updates:** nymo fragt einmal die Woche hier nach einer neueren Version (nur die Versionsnummer, keine Akten) und zeigt sie unten links im Fenster. Die neue Version einfach über die alte installieren, Akten und Einstellungen bleiben. Abschalten: `"updates": false` in `nymo.json` neben `nymo.py`.

Anleitung und Hintergrund: die `README.md` im Ordner `nymo`. Mehr unter [aibene.de](https://aibene.de).

Dieses Repository enthält nur die Releases und den Bau des Installers (`installer/`, GitHub Actions).
