; Inno Setup script — обновлённый: использует {commonpf} вместо устаревшего {pf}
; Скомпилируйте этот скрипт в Inno Setup Compiler (https://jrsoftware.org/isinfo.php)

[Setup]
AppName=ContractsApp
AppVersion=1.1
DefaultDirName={commonpf}\ContractsApp
DefaultGroupName=ContractsApp
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
OutputBaseFilename=ContractsApp_Installer
UninstallDisplayName=ContractsApp

[Files]
; Копируем exe и утилиты (dist\ContractsApp.exe должен быть подготовлен PyInstaller)
Source: "dist\ContractsApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "nssm.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_for_installer.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Создаём папку для данных в ProgramData (права админа требуются; будет создана при установке)
Name: "{commonappdata}\ContractsApp"; Permissions: users-modify

[Icons]
; Ярлык для запуска приложения
Name: "{group}\ContractsApp"; Filename: "{app}\ContractsApp.exe"
; Ярлык деинсталлятора в меню Пуск — использует встроенный uninstaller
Name: "{group}\Uninstall ContractsApp"; Filename: "{uninstallexe}"
; Иконка на рабочем столе (опционально)
Name: "{commondesktop}\ContractsApp"; Filename: "{app}\ContractsApp.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: unchecked

[Run]
; После установки: инициализация БД и создание админа (выполняется скрыто)
Filename: "{app}\ContractsApp.exe"; Parameters: "init-db"; Flags: runhidden waituntilterminated
Filename: "{app}\ContractsApp.exe"; Parameters: "create-admin admin root64"; Flags: runhidden waituntilterminated

; Опционально: установить NSSM‑службу (если nssm.exe присутствует в каталоге установки)
Filename: "{app}\nssm.exe"; Parameters: "install ContractsAppService ""{app}\ContractsApp.exe"" serve --host 127.0.0.1 --port 8000"; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set ContractsAppService AppDirectory ""{app}"""; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "set ContractsAppService Start SERVICE_AUTO_START"; Flags: runhidden waituntilterminated
Filename: "{app}\nssm.exe"; Parameters: "start ContractsAppService"; Flags: runhidden waituntilterminated

[UninstallDelete]
; По умолчанию не удаляем папку данных в ProgramData, чтобы не потерять БД пользователя.
; Можно добавить удаление/перемещение в резервную копию при деинсталляции при желании.

; Конец скрипта