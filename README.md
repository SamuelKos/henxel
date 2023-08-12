# Henxel
GUI-editor for Python development. Tested to work with Debian 12 and Windows 11.


# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Line numbering
* Tabbed editing
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

# Lacking
* Auto-completion
* Hinting

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
Python installation should already include tkinter. There currently is no
mkvenv script for Windows in this project, but here is short info about how to
create a working Python virtual environment in Windows. First open console, like
PowerShell (in which: ctrl-r to search command history, most useful) and:

```console
mkdir myproject
cd myproject
myproject> python.exe -m venv env
myproject> .\env\Scripts\activate
what you can get with pressing: (e <tab> s <tab> a <tab> <return>)

First the essential for the env:
(env) myproject> pip install --upgrade pip
(env) myproject> pip install wheel

Then to enable tab-completion in Python-console, most useful:
(env) myproject> pip install pyreadline3

And it is ready to use:
(env) myproject> pip list
(env) myproject> deactivate
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


# More on virtual environments:
This is now bit more complex, because we are not anymore expecting that we have many older versions of the project
left (as packages). But with this lenghty method we can compare to any commit, not just released packages.
So this is for you who are packaging Python-project and might want things like side-by-side live-comparison of two
different versions, most propably version you are currently developing and some earlier version. I Assume you are the
owner of the project so you have the git-history, or else you have done git clone. I use henxel as the project example.

First make build-env if you do not have it. It likely can be the same for many of your projects:

```console
~/$ mkvenv env
~/$ . env/bin/activate
(env) ~/$ pip install --upgrade build
(env) ~/$ deactivate
```

Then create development-venv for the project, if you haven't already and install current version to it:

```console
~/myproject/henxel$ mkvenv env
~/myproject/henxel$ . env/bin/activate
(env) ~/myproject/henxel$ pip install -e .
```

Then select the git-commit for the reference version. I have interesting commits with message like: version 0.2.0
so to list all such commits:

```console
~/myproject/henxel$ git log --grep=version
```

For example to make new branch from version 0.2.0, copy the first letters from the commit-id and:

```console
~/myproject/henxel$ git branch version020 e4f1f4ab3f
~/myproject/henxel$ git switch version020
```

Then 1: activate your build-env, 2: build that ref-version of your project.

There are some extra lines to help ensure you are in the correct env (that is build-env) and branch
(branch you made from older commit).
For example, if your build-env is in the root of your home-directory:

```console
~/$ . env/bin/activate
(env) ~/$ cd myproject/henxel
(env) ~/myproject/henxel$ pip list
(env) ~/myproject/henxel$ git branch
(env) ~/myproject/henxel$ git log
(env) ~/myproject/henxel$ python -m build
```

And it will create the ref-package: dist/henxel-0.2.0.tar.gz

3: install it with pip

Create ref-env to some place that is not version-controlled like the parent-folder and install your ref-package to it. First deactivate build-env if it still active:

```console
(env) ~/myproject/henxel$ deactivate
~/myproject/henxel$ cd ..
~/myproject$ mkvenv v020
~/myproject$ . v020/bin/activate
(v020) ~/myproject$ cd henxel
(v020) ~/myproject/henxel$ pip list
(v020) ~/myproject/henxel$ pip install dist/henxel-0.2.0.tar.gz
(v020) ~/myproject/henxel$ deactivate
```

Now you are ready to launch both versions of your project and do side-by-side comparison if that is what you want:

```console
~/myproject/henxel$ . env/bin/activate
(env) ~/myproject/henxel$ pip list
```

From other shell-window:

```console
~/myproject$ . v020/bin/activate
(v020) ~/myproject$ pip list
```


# More resources
[Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
