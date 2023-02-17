# Henxel
GUI-editor for Python development. Tested to work with Debian Bullseye


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
* Persistent configuration
* Near persistent contents

# Lacking
* Auto-completion
* Hinting

# Prerequisites
Python modules required that are sometimes not installed with OS: tkinter. Check:

```console
foo@bar:~$ python3 -c "import tkinter"
```

If no error, it is installed. If it throws an error you have to install it from OS-repository. In debian it is: python3-tk

```console
foo@bar:~$ sudo apt install python3-tk
```

# About virtual environment, optional but highly recommended
Consider creating virtual environment for your python-projects and installing python packages like this editor to it. Editor will not save your configuration if it was not launched from virtual environment. In debian you have to first install this package: python3-venv:

```console
foo@bar:~$ sudo apt install python3-venv
```

There is a script named 'mkvenv' in /util. Copy it to some place nice like bin-directory in your home-directory and make it executable if it is not already:
```console
foo@bar:~/bin$ chmod u+x mkvenv
```

Then make folder for your new project and install venv there and activate it, and show currently installed python-packages in your new virtual environment, and lastly deactivate (quit) environment:
```console
foo@bar:~$ mkdir myproject
foo@bar:~$ cd myproject
foo@bar:~/myproject$ mkvenv env
-------------------------------
foo@bar:~/myproject$ source env/bin/activate
(env) foo@bar:~/myproject$ pip list
-----------------------------------
(env) foo@bar:~/myproject$ deactivate
foo@bar:~/myproject$
```

To remove venv just remove the env-directory and you can start from clean desk making new one with mkvenv later. Optional about virtual environment ends here.

# Installing
```console
(env) foo@bar:~/myproject$ pip install henxel
```

or to install system-wide, not recommended. You need first to install pip from OS-repository:

```console
foo@bar:~/myproject$ pip install henxel
```


# Running from Python-console:

```console
foo@bar:~/myproject$ source env/bin/activate
(env) foo@bar:~/myproject$ python
--------------------------------------
>>> import henxel
>>> e=henxel.Editor()
```

# Developing

```console
foo@bar:~/myproject$ mkvenv env
foo@bar:~/myproject$ . env/bin/activate
(env) foo@bar:~/myproject$ git clone https://github.com/SamuelKos/henxel
(env) foo@bar:~/myproject$ cd henxel
(env) foo@bar:~/myproject/henxel$ pip install -e .
```

If you currently have no internet but have previously installed virtual environment which has pip and setuptools and you have downloaded henxel-repository:

```console
(env) foo@bar:~/myproject/henxel$ pip install --no-build-isolation -e .
```

Files are in src/henxel/


# More on virtual environments:
For you who are packaging Python-project and you need side-by-side live-comparison of two different versions,
most propably version you are currently developing and some earlier version. Or for anyone who is interested doing so, not many I think.

When creating development-venv for the project, make another one with same deps for comparison:

```console
foo@bar:~/myproject/$ mkvenv env
foo@bar:~/myproject/$ mkvenv ref_env
```

Then install your package in env, in editable mode of course, activate it and make some change to your project.
Then in other shell-window, activate ref_env and install your earlier version of the project to it from your
archive; when you build your package, they are put to /dist. So assuming your earlier version of myproject
was 0.0.3 and that you have not deleted it from your dist-folder:

```console
(ref_env) foo@bar:~/myproject/$ pip install dist/myproject-0.0.3.tar.gz
```


Or if you have saved your earlier version in the repository:

```console
(ref_env) foo@bar:~/myproject/$ pip install 'myproject==0.0.3'
```


Now you are ready to launch both versions of your project and do side-by-side comparison. If you
are doing something with GUI this is what you want.


# More resources
[Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG.md)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
