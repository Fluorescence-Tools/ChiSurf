; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "ChiSurf"
#define MyAppVersion "18.12.3dev"
#define MyAppPublisher "Thomas Peulen"
#define MyAppURL "https://www.github.com/Fluorescence-Tools/Chisurf"
#define MyAppExeName "chisurf.exe"
#define DevDir "C:\Users\thoma\PycharmProjects\ChiSurf\chisurf\"
#define RunTimeDir "C:\Users\thoma\PycharmProjects\ChiSurf\VC++ runtimes\"

[Setup]
AppId={{F25DCFFA-1234-4643-BC4F-2C3A20495937}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
UsePreviousAppDir=no
DefaultGroupName={#MyAppName}
LicenseFile={#DevDir}\..\LICENSE
OutputDir={#DevDir}\..\build
OutputBaseFilename=setup_{#MyAppVersion}
SetupIconFile={#DevDir}\mfm\ui\icons\cs_logo.ico
Compression=lzma
SolidCompression=yes
CompressionThreads=4
UninstallLogMode=overwrite
DirExistsWarning=yes
UninstallDisplayIcon={app}\chisurf.exe
DisableProgramGroupPage=yes


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#RunTimeDir}*"; DestDir: {tmp}; Flags: deleteafterinstall
Source: "{#DevDir}gui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DevDir}\..\build_tools\chisurf.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DevDir}mfm\*"; DestDir: "{app}\mfm"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DevDir}macro\*"; DestDir: "{app}\macro"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DevDir}tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Miniconda2\envs\chisurf\*"; DestDir: "{app}\Anaconda"; Flags: ignoreversion recursesubdirs createallsubdirs

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: {tmp}\VS_2005_vcredist_x64.exe; Parameters: /q
Filename: {tmp}\VS_2008_vcredist_x64.exe; Parameters: /q
Filename: {tmp}\VS_2010_vcredist_x64.exe; Parameters: /q
Filename: {tmp}\VS_2012_vcredist_x64.exe; Parameters: /q
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

