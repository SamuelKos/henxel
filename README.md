# Henxel
GUI-editor for Python development.

![editor_mac](pics/editor_macOS.png)

![editor_windows](pics/editor_win.png)

# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Line numbering
* Tabbed editing
* Tab-completion
* Inspect module
* Show git-branch
* Run code/file/project
* Search - Replace
* Indent - Unindent
* Comment - Uncomment
* Syntax highlighting
* Click to open errors
* Parenthesis checking
* Persistent configuration
* etc


# Prerequisites in Linux
Python modules required that are sometimes not installed with OS: tkinter. Check in Python-console:

```console
>>> import tkinter
```

If no error, it is installed. If it throws an error you have to install it from OS-repository. In debian it is: python3-tk

```console
~$ sudo apt install python3-tk
```

# About virtual environment, optional but highly recommended
Consider creating virtual environment for your python-projects and installing python packages like this editor to it. In debian you may have to first install this package: python3-venv:

```console
~$ sudo apt install python3-venv
```

There is a linux-script named 'mkvenv' in /util. Copy it to some place nice like bin-directory in your home-directory and make it executable if it is not already:

```console
~/bin$ chmod u+x mkvenv
```

Then make folder for your new project and install venv there and activate it, and show currently installed python-packages in your new virtual environment, and lastly deactivate (quit) environment:

```console
~$ mkdir myproject
~$ cd myproject
~/myproject$ mkvenv env
-------------------------------
~/myproject$ source env/bin/activate
(env) ~/myproject$ pip list
-----------------------------------
(env) ~/myproject$ deactivate
~/myproject$
```

To remove venv just remove the env-directory and you can start from clean desk making new one with mkvenv later. Optional about virtual environment ends here.

# Prerequisites in Windows and venv-creation
Python installation should already include tkinter. First open console, like
PowerShell (in which: ctrl-r to search command history, most useful) and read
macOS -info below. Just use: env/Scripts/activate to activate venv.


# Prerequisites in macOS and venv-creation
You will need to install newer version of python. Can simply use pkg-installer
from Python-homepage. Making venv is quite same as in Linux. It seems to be
enough to make venv and then install henxel to it without anything else.

```console
~$ mkdir myproject
~$ cd myproject
~/myproject$ python -m venv env
-------------------------------
~/myproject$ source env/bin/activate
(env) ~/myproject$ pip list
-----------------------------------
(env) ~/myproject$ deactivate
~/myproject$
```



# Installing
```console
(env) ~/myproject$ pip install henxel
```

To install system-wide, (You may need first to install pip from OS-repository):

```console
~/myproject$ pip install henxel
```


# Running, from Python-console:

```console
~/myproject$ source env/bin/activate
(env) ~/myproject$ python
--------------------------------------
>>> import henxel
>>> e=henxel.Editor()
```

# Running, from terminal:
Can just type "henxel" and hit Enter or for example:

```console
~/myproject$ source env/bin/activate
(env) henxel file1.py file2.py ...
```

# Running, from terminal:

```console
~/myproject$ source env/bin/activate
(env) python -m henxel file1.py file2.py ...
```

# Developing

```console
~/myproject$ mkvenv env
~/myproject$ . env/bin/activate
(env) ~/myproject$ git clone https://github.com/SamuelKos/henxel
(env) ~/myproject$ cd henxel
(env) ~/myproject/henxel$ pip install -e .
```

If you currently have no internet but have previously installed virtual environment which has pip and setuptools and you have downloaded henxel-repository:

```console
(env) ~/myproject/henxel$ pip install --no-build-isolation -e .
```

Files are in src/henxel/


# More resources
* [Tcl/Tk](https://tcl.tk/man/tcl9.0/TkCmd/index.html)

* [Python/Tkinter](https://docs.python.org/3/library/tkinter.html)

* [Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG)

* [Shortcuts for Windows and Linux](https://github.com/SamuelKos/henxel/blob/main/src/henxel/shortcuts.txt)

* [Shortcuts for macOS](https://github.com/SamuelKos/henxel/blob/main/src/henxel/shortcuts_mac.txt)

* [Help](src/henxel/help.txt)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
































