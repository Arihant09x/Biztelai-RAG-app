@echo off
setlocal
cd /d "%~dp0"
if exist "..\BiztelAI-Backend\.tools\nodejs\node.exe" (
    set "PATH=%~dp0..\BiztelAI-Backend\.tools\nodejs;%PATH%"
)
echo Starting PlantAssist AI (BiztelAI Frontend)...
npm run dev
pause

