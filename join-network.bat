@echo off
REM Pull the shared GitHub hub with Git Bash, then run PTN on localhost.

setlocal
set "ROOT=%~dp0"
set "BASH="
if exist "C:\Program Files\Git\bin\bash.exe" set "BASH=C:\Program Files\Git\bin\bash.exe"
if exist "C:\Program Files (x86)\Git\bin\bash.exe" set "BASH=C:\Program Files (x86)\Git\bin\bash.exe"

if not defined BASH (
  echo Git Bash not found. Install Git for Windows:
  echo https://git-scm.com/download/win
  pause
  exit /b 1
)

echo Pulling PTN from GitHub via Git Bash...
"%BASH%" "%ROOT%scripts\join-network.sh"
if errorlevel 1 (
  echo Git pull failed.
  pause
  exit /b 1
)

set PTN_NETWORK_ENABLED=true
call "%ROOT%start-local.bat"
endlocal
