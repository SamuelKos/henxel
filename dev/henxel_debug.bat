@echo off

if "%1" == "mainloop" goto :main

:start
start /w python.exe -i -c "import henxel;e=henxel.Editor(debug=True)"
if %errorlevel% neq 0 goto :start
exit 0

:main
start /w python.exe -m henxel --debug
if %errorlevel% neq 0 goto :main

