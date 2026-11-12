@echo off
setlocal
cd /d "%~dp0BiztelAI-Frontend"
if exist "..\BiztelAI-Backend\.tools\nodejs\node.exe" (
    set "PATH=%~dp0BiztelAI-Backend\.tools\nodejs;%PATH%"
)
echo Starting PlantAssist AI (BiztelAI Frontend)...
npm run dev
pause

