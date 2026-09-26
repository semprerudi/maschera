; MASCHERA — Inno-Setup-Rezept fuer den Windows-Installer.
;
; Nicht von Hand aufrufen: `tools/paket/windows_bauen.py` setzt die zwei
; Werte und ruft ISCC. `Fassung` kommt aus `app/serve.py` — die einzige
; Quelle —, `Quelle` ist das Verzeichnis, das PyInstaller gebaut hat.
;
; Installiert OHNE Administratorrechte in den Benutzerordner. Ein
; Werkzeug, das nichts ausser den eigenen Einstellungen schreibt, braucht
; keine Rechte am ganzen Rechner.

#ifndef Fassung
  #error "Fassung fehlt — ueber windows_bauen.py bauen"
#endif
#ifndef Quelle
  #error "Quelle fehlt — ueber windows_bauen.py bauen"
#endif

[Setup]
; Die Kennung bleibt ueber alle Fassungen gleich — daran erkennt Windows
; ein Update statt einer zweiten Installation.
AppId={{525570EC-5046-4E6B-B22F-10BCDF2732AE}
AppName=MASCHERA
AppVersion={#Fassung}
AppVerName=MASCHERA {#Fassung}
AppPublisher=MASCHERA
AppPublisherURL=https://www.maschera.ch
AppSupportURL=https://github.com/semprerudi/maschera/issues
DefaultDirName={autopf}\MASCHERA
DefaultGroupName=MASCHERA
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=MASCHERA-{#Fassung}-x64-setup
SetupIconFile=..\..\app\static\favicon.ico
UninstallDisplayIcon={app}\MASCHERA.exe
; Das Modell (1,2 GB) laesst sich kaum komprimieren — Gewichte sind fast
; Zufallszahlen. Es liegt deshalb unkomprimiert im Installer; alles andere
; komprimiert, aber nicht als ein einziger Block, sonst muss beim
; Installieren alles am Stueck entpackt werden.
Compression=lzma2
SolidCompression=no
WizardStyle=modern
; Die Sprache nach der Region, nicht nach der Oberflaechensprache: eine
; englische Oberflaeche mit Region Schweiz waehlte sonst Italienisch.
; Gemessen an einem Probe-Installer: mit `locale` kommt Deutsch.
LanguageDetectionMethod=locale

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Quelle}\*"; DestDir: "{app}"; Excludes: "\_internal\maschera\runs\*"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Quelle}\_internal\maschera\runs\*"; DestDir: "{app}\_internal\maschera\runs"; Flags: ignoreversion recursesubdirs createallsubdirs nocompression
; Die Lizenztexte — das gebaute Paket steht unter AGPL-3.0.
Source: "..\..\LICENSE"; DestDir: "{app}\lizenzen"; Flags: ignoreversion
Source: "..\..\LICENSE-AGPL-3.0.txt"; DestDir: "{app}\lizenzen"; Flags: ignoreversion
Source: "..\..\LIZENZ.md"; DestDir: "{app}\lizenzen"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MASCHERA"; Filename: "{app}\MASCHERA.exe"
Name: "{autodesktop}\MASCHERA"; Filename: "{app}\MASCHERA.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MASCHERA.exe"; Description: "{cm:LaunchProgram,MASCHERA}"; Flags: nowait postinstall skipifsilent

[Code]
// ⚠️ Bei hoher Skalierung (gemessen bei 250 %) schneidet Inno Setup das
// Kaestchen in beiden Listen links ab — Aufgaben und Schlussseite, im
// modernen wie im klassischen Stil. Rechts vom Text laesst es sich nicht
// setzen; eingerueckt ist es ganz sichtbar. Am Probe-Installer geprueft.
procedure InitializeWizard;
begin
  WizardForm.TasksList.Offset := WizardForm.TasksList.Offset + ScaleX(6);
  WizardForm.RunList.Offset := WizardForm.RunList.Offset + ScaleX(6);
end;
