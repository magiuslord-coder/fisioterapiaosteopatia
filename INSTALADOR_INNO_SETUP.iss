; Fisio-Osteopatia installer
#define MyAppName "Fisio-Osteopatia"
#define MyAppVersion "4.1"
#define MyAppExeName "FisioOsteopatia.exe"

[Setup]
AppId={{C5E7D4C1-3B6D-4B8B-9A3D-8F2B1E8A4F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Fisio-Osteopatia
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=FisioOsteopatia_Instalador_Windows
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\FisioOsteopatia.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Fisio-Osteopatia"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Fisio-Osteopatia"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Fisio-Osteopatia"; Flags: nowait postinstall skipifsilent
