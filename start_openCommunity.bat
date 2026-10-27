@echo off
REM 在 Windows Terminal 中分两个窗格分别启动前后端开发服务器
REM 需要 Windows 11 自带的 wt.exe（Windows Terminal）
set "ROOT=%~dp0"

wt -d "%ROOT%backend" --title "Backend" cmd /k "venv\Scripts\activate && python manage.py runserver" ; split-pane -d "%ROOT%frontend" --title "Frontend" cmd /k "npm run dev"
