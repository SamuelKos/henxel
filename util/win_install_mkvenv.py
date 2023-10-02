import sys
import pathlib
tmp1 = 'launch_ed.bat'
tmp2 = 'create_scripts.bat'
tmp3 = 'mkvenv.bat'


temp1 = '''@echo off
start /B "" "py" "-m" "idlelib" "-c" "import henxel;e=henxel.Editor()" "-t" %cd%'''

temp2 = '''@echo off
echo @echo off > %1\\act.bat
echo cd %cd% >> %1\\act.bat
echo git status >> %1\\act.bat
echo %1\Scripts\\activate.bat >> %1\\act.bat

echo @echo off > %1\launch_ed.bat
echo %cd%\%1\\act.bat ^& start /B "" "py" "-m" "idlelib" "-c" "import henxel;e=henxel.Editor()" "-t" %cd% >> %1\launch_ed.bat
'''

temp3 = '''@echo off

set folder="venv"

IF %1.==. GOTO No1
set folder=%1
GOTO No1

:No1
  IF EXIST %folder% echo %folder% exists already, aborting venv creation. & GOTO End1
  
  IF EXIST "requirements.txt" (
    py -m venv %folder% & %folder%\Scripts\\activate.bat & pip install wheel & pip install -r requirements.txt & %folder%\Scripts\deactivate.bat & create_scripts.bat %folder%
	
  ) ELSE (
    py -m venv %folder% & %folder%\Scripts\\activate.bat & pip install wheel & %folder%\Scripts\deactivate.bat & create_scripts.bat %folder%
	
  )

:End1'''


fpath = pathlib.Path(sys.prefix) / tmp1

if fpath.exists():
    print(f'\nCan not overwrite file: {fpath}')
else:
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(temp1)
		
    except EnvironmentError as e:
        print(e.__str__())
        print('\n Could not save file: {fpath}')



fpath = pathlib.Path(sys.prefix) / tmp2

if fpath.exists():
    print(f'\nCan not overwrite file: {fpath}')
else:
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(temp2)
		
    except EnvironmentError as e:
        print(e.__str__())
        print('\n Could not save file: {fpath}')


fpath = pathlib.Path(sys.prefix) / tmp3

if fpath.exists():
    print(f'\nCan not overwrite file: {fpath}')
else:
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(temp3)
		
    except EnvironmentError as e:
        print(e.__str__())
        print('\n Could not save file: {fpath}')
