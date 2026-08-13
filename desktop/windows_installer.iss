#define MyAppName "Cosmic Reconciliation Memory"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "Cory Shane Davis / NavisWORLD"
#define MyAppExeName "CosmicMemory.exe"

[Setup]
AppId={{A7DAD2B6-3DD0-4F27-91DE-C51F7D36E35A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Cosmic Reconciliation Memory
DefaultGroupName=Cosmic Reconciliation Memory
DisableProgramGroupPage=yes
OutputDir=..\dist-installer
OutputBaseFilename=CosmicMemory-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Cosmic Reconciliation Memory"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Cosmic Reconciliation Memory"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Cosmic Reconciliation Memory"; Flags: nowait postinstall skipifsilent
