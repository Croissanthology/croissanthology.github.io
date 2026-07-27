@echo off
REM Build Roussette and drop it into your Minecraft mods folder.
REM   install.bat                 default %APPDATA%\.minecraft
REM   install.bat "C:\path\to\mc" a specific instance
REM Needs Java 21+ and, the first time, an internet connection.

setlocal enabledelayedexpansion
cd /d "%~dp0"

where java >nul 2>&1
if errorlevel 1 (
  echo error: Java not found. Install Java 21 or newer.
  exit /b 1
)

if exist gradlew.bat (
  set GRADLE=gradlew.bat
) else (
  where gradle >nul 2>&1
  if errorlevel 1 (
    echo error: Neither gradlew.bat nor gradle found.
    echo Install Gradle 8.x, or copy gradlew.bat and the gradle\ folder
    echo from any NeoForge MDK into this directory.
    exit /b 1
  )
  echo No wrapper here; generating one with your local Gradle.
  call gradle wrapper --gradle-version 8.14.3 >nul
  set GRADLE=gradlew.bat
)

echo Building. The first run downloads NeoForge and takes a few minutes.
call %GRADLE% build
if errorlevel 1 (
  echo error: build failed. Scroll up for the compile errors.
  exit /b 1
)

set "JAR="
for %%F in (build\libs\*.jar) do (
  echo %%~nxF | find "-sources" >nul || set "JAR=%%F"
)
if "%JAR%"=="" (
  echo error: build produced no jar.
  exit /b 1
)

if "%~1"=="" (set "MC=%APPDATA%\.minecraft") else (set "MC=%~1")
if not exist "%MC%" (
  echo error: no Minecraft folder at %MC%
  echo Pass the path explicitly:  install.bat "C:\path\to\.minecraft"
  exit /b 1
)

if not exist "%MC%\mods" mkdir "%MC%\mods"
copy /Y "%JAR%" "%MC%\mods\" >nul
echo Installed to %MC%\mods\
echo.
echo Next:
echo   1. Launch the NeoForge 26.2 profile, not vanilla.
echo   2. Everyone on the LAN world needs this same jar.
echo   3. In the world, once ever:  /roussette-temples
echo   4. /new-target ^<name^> to aim her, /roussette-spare ^<name^> to protect.
endlocal
