@echo off
REM Helper CMD build script for V10
REM Usage: build.cmd
setlocal enabledelayedexpansion

if not exist icon.ico (
  echo icon.ico not found in project root. Place icon.ico next to this script.
  exit /b 1
)

REM Resolve full path to icon
for %%I in (icon.ico) do set ICON=%%~fI

if not exist build mkdir build
if not exist build\temp mkdir build\temp
if not exist release mkdir release

REM Copy icon into build folder
copy /Y "%ICON%" build\icon.ico >nul

echo Running PyInstaller...
pyinstaller --onefile --noconsole --uac-admin --icon="%ICON%" --name=SystemCheck --distpath=.\release --specpath=.\build --workpath=.\build\temp V10.py

if exist .env (
  copy /Y .env .\release\.env >nul
  echo .env copied to .\release
) else (
  echo Warning: .env not found in project root. Remember to copy .env into release after build.
)

echo Build script finished.
endlocal