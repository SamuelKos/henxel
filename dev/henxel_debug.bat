@echo off
:start
start /w python.exe -i -c "import henxel;e=henxel.Editor(debug=True)"
if %errorlevel% neq 0 goto :start

