; nymo-setup.exe -- Installer fuer das Windows-Paket (Inno Setup 6). Baut GitHub Actions (installer.yml) aus dem
; nymo-windows.zip des Releases; von Hand: ISCC /DVersion=1.1 /DQuelle=<entpacktes Zip> /DZiel=<Ausgabe> nymo.iss
; (Quelle und Ziel absolut angeben -- relative Pfade loest Inno Setup von diesem Skript aus auf)
;
; Installiert fuer den angemeldeten Benutzer nach %LOCALAPPDATA%\Programs\nymo (kurzer Pfad, nicht in OneDrive,
; keine Administrator-Rechte), legt die Verknuepfungen „nymo“ an (Startmenue, Schreibtisch) und schreibt
; installiert.ini -- daran erkennt nymo.pyw, dass es keine Verknuepfungen mehr anlegen muss. Ein Update laeuft
; einfach ueber die alte Version: python\, ki\ und poppler\ werden vorher geleert (keine Reste alter Pakete),
; nymo.json (Einstellungen) bleibt. Laeuft nymo gerade, bittet das Setup, es zu schliessen (Restart Manager).

#ifndef Version
  #define Version "0.0"
#endif
#ifndef Quelle
  #define Quelle "paket"
#endif
#ifndef Ziel
  #define Ziel "ausgabe"
#endif

[Setup]
AppId={{7E2B1C0A-5F3D-4B8E-9A61-6E0D2C4F9B10}
AppName=nymo
AppVersion={#Version}
AppVerName=nymo {#Version}
AppPublisher=aibene
AppPublisherURL=https://aibene.de
AppSupportURL=https://aibene.de
AppUpdatesURL=https://github.com/lifetimeai/nymo/releases/latest
VersionInfoVersion={#Version}.0.0
DefaultDirName={userpf}\nymo
DisableDirPage=yes
DefaultGroupName=nymo
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#Ziel}
OutputBaseFilename=nymo-setup
SetupIconFile={#Quelle}\nymo\app-win\nymo.ico
UninstallDisplayIcon={app}\app-win\nymo.ico
UninstallDisplayName=nymo
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
WizardStyle=modern
ShowLanguageDialog=no
CloseApplications=yes
RestartApplications=no
UsePreviousTasks=yes

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"

[Messages]
de.WelcomeLabel2=nymo schwärzt Namen und persönliche Angaben in Akten, bevor Claude sie liest. Es läuft nur auf diesem Rechner – nichts geht ins Internet.%n%nDas Setup richtet nymo mit allem ein, was es braucht (Python, Texterkennung, KI-Modell; rund 2 GB), nur für den angemeldeten Benutzer. Administrator-Rechte sind nicht nötig.
de.FinishedLabel=nymo ist eingerichtet. Du findest es im Startmenü und auf dem Schreibtisch.%n%nBeim ersten Start lädt nymo die KI-Erkennung – das dauert einmalig bis zu zwei Minuten.

[Tasks]
Name: "desktopicon"; Description: "Verknüpfung auf dem Schreibtisch anlegen"; GroupDescription: "Verknüpfungen:"

[InstallDelete]
; Keine Reste alter Versionen in den Paketordnern (Python-Pakete, Modell, Poppler, Fenster)
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\ki"
Type: filesandordirs; Name: "{app}\poppler"
Type: filesandordirs; Name: "{app}\app-win"
Type: filesandordirs; Name: "{app}\__pycache__"

[Files]
Source: "{#Quelle}\nymo\*"; DestDir: "{app}"; Excludes: "__pycache__,*.pyc,nymo.json,namen.txt,.DS_Store"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#Quelle}\ocr-prep.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#Quelle}\ocr-prep-README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[INI]
Filename: "{app}\installiert.ini"; Section: "nymo"; Key: "version"; String: "{#Version}"
Filename: "{app}\installiert.ini"; Section: "nymo"; Key: "installer"; String: "Inno Setup"

[Icons]
Name: "{userprograms}\nymo"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\nymo.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\app-win\nymo.ico"; Comment: "nymo – Akten schwärzen, bevor Claude sie sieht"
Name: "{userdesktop}\nymo"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\nymo.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\app-win\nymo.ico"; Comment: "nymo – Akten schwärzen, bevor Claude sie sieht"; Tasks: desktopicon

[Run]
; Bytecode vorab (BJ, 03.11.2026, Tempo Windows): Das Paket kommt ohne .pyc (paket.sh baut am Mac, andere
; Python-Version). Ohne diesen Schritt uebersetzt der erste Start Tausende Dateien von PyTorch, transformers und
; RapidOCR, und Defender prueft jede neu geschriebene Datei -- das kostete den ersten Start bis zu zwei Minuten.
; Hier zahlt das Setup das einmal, auf allen Kernen (-j 0). Einzelne Dateien, die Python 3.13 nicht uebersetzen kann
; (Vorlagen, Tests in Paketen), melden einen Fehler und werden uebersprungen; das Setup laeuft weiter.
Filename: "{app}\python\python.exe"; Parameters: "-I -m compileall -q -j 0 ""{app}"""; WorkingDir: "{app}"; StatusMsg: "Bereite nymo vor (einmalig, bis zu zwei Minuten) …"; Flags: runhidden waituntilterminated
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\nymo.pyw"""; WorkingDir: "{app}"; Description: "nymo jetzt starten"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; Was nymo selbst im Programmordner anlegt (Bytecode, Protokoll des KI-Dienstes); nymo.json bleibt absichtlich
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\ki"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\installiert.ini"
