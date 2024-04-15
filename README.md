# Henxel
GUI-editor for Python development. Tested to work with Debian 12, Windows 10 and 11 and macOS 12.

![editor_mac](pics/editor_macOS.png)
![editor_linux](pics/editor_linux.png)

# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Line numbering
* Tabbed editing
* Tab-completion
* Inspect object
* Show git-branch
* Run current file
* Search - Replace
* Indent - Unindent
* Comment - Uncomment
* Syntax highlighting
* Click to open errors
* Parenthesis checking
* Persistent configuration


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
Consider creating virtual environment for your python-projects and installing python packages like this editor to it. Editor will not save your configuration if it was not launched from virtual environment. In debian you have to first install this package: python3-venv:

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
Python installation should already include tkinter. There is
mkvenv-install script for Windows in /util. Here is short info about how to
create a working Python virtual environment in Windows. First open console, like
PowerShell (in which: ctrl-r to search command history, most useful) or CMD-Terminal and:

```console
mkdir myproject
cd myproject
myproject> py win_install_mkvenv.py
myproject> mkvenv env

myproject> env\act.bat

If that did not activate venv:
myproject> env\Scripts\activate

After venv is active upgrade pip and install Henxel:
(env) myproject> pip install --upgrade pip
(env) myproject> pip install henxel

Venv is now ready:
(env) myproject> pip list
(env) myproject> deactivate

Launch Henxel:
myproject> env\launch_ed.bat
```


# Prerequisites in macOS and venv-creation
Python installation (you may need to install newer version of python from python.org)
should already include tkinter. There currently is no mkvenv script for macOS,
but making venv is quite same as in Linux. It seems to be enough to make venv
and then install henxel to it without anything else.

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

or to install system-wide, not recommended. You need first to install pip from OS-repository:

```console
~/myproject$ pip install henxel
```


# Running from Python-console:

```console
~/myproject$ source env/bin/activate
(env) ~/myproject$ python
--------------------------------------
>>> import henxel
>>> e=henxel.Editor()
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
[Tcl/Tk](https://tcl.tk/man/tcl9.0/TkCmd/index.html)
[Python/Tkinter](https://docs.python.org/3/library/tkinter.html)
[Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
