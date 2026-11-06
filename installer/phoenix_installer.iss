; P.H.O.E.N.I.X. Windows Desktop Application Installer
; Built using Inno Setup (https://jrsoftware.org/isinfo.php)

#define MyAppName "P.H.O.E.N.I.X."
#define MyAppDirName "PHOENIX"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Antigravity AI"
#define MyAppURL "https://github.com/swayamprabhu2005/P.H.O.E.N.I.X."
#define MyAppExeName "run.bat"
#define MyAppIcoName "phoenix.ico"

[Setup]
AppId={{94F0C3D7-6F7D-4F77-A3BA-04987E92A111}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppDirName}
AllowRootDirectory=yes
AllowNoIcons=yes
AlwaysShowDirOnReadyPage=yes
AppendDefaultDirName=no
DirExistsWarning=no
EnableDirDoesntExistWarning=no
UsePreviousAppDir=no
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=dist_installer
OutputBaseFilename=PHOENIX_Setup
SetupIconFile=phoenix.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Launch P.H.O.E.N.I.X. automatically on Windows startup"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git*,.pytest_cache,tests,dist_installer"
Source: "phoenix.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIcoName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppIcoName}"
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startupicon; IconFilename: "{app}\{#MyAppIcoName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall nowait skipifsilent
