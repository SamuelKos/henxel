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
* Parenthesis checking
* Persistent configuration

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
This is now bit more complex, because we are not anymore expecting that we have many older versions of the project
left (as packages). But with this lenghty method we can compare to any commit, not just released packages.
So this is for you who are packaging Python-project and might want things like side-by-side live-comparison of two
different versions, most propably version you are currently developing and some earlier version. I Assume you are the
owner of the project so you have the git-history, or else you have done git clone. I use henxel as the project example.

First make build-env if you do not have it. It likely can be the same for many of your projects:

```console
foo@bar:~/$ mkvenv env
foo@bar:~/$ . env/bin/activate
(env) foo@bar:~/$ pip install --upgrade build
(env) foo@bar:~/$ deactivate
```

Then create development-venv for the project, if you haven't already and install current version to it:

```console
foo@bar:~/myproject/henxel$ mkvenv env
foo@bar:~/myproject/henxel$ . env/bin/activate
(env) foo@bar:~/myproject/henxel$ pip install -e .
```

Then select the git-commit for the reference version. I have interesting commits with message like: version 0.2.0
so to list all such commits:

```console
foo@bar:~/myproject/henxel$ git log --grep=version
```

For example to make new branch from version 0.2.0, copy the first letters from the commit-id and:

```console
foo@bar:~/myproject/henxel$ git branch version020 e4f1f4ab3f
foo@bar:~/myproject/henxel$ git switch version020
```

Then 1: activate your build-env, 2: build that ref-version of your project.

There are some extra lines to help ensure you are in the correct env (that is build-env) and branch
(branch you made from older commit).
For example, if your build-env is in the root of your home-directory:

```console
foo@bar:~/$ . env/bin/activate
(env) foo@bar:~/$ cd myproject/henxel
(env) foo@bar:~/myproject/henxel$ pip list
(env) foo@bar:~/myproject/henxel$ git branch
(env) foo@bar:~/myproject/henxel$ git log
(env) foo@bar:~/myproject/henxel$ python -m build
```

And it will create the ref-package: dist/henxel-0.2.0.tar.gz

3: install it with pip

Create ref-env to some place that is not version-controlled like the parent-folder and install your ref-package to it. First deactivate build-env if it still active:

```console
(env) foo@bar:~/myproject/henxel$ deactivate
foo@bar:~/myproject/henxel$ cd ..
foo@bar:~/myproject$ mkvenv v020
foo@bar:~/myproject$ . v020/bin/activate
(v020) foo@bar:~/myproject$ cd henxel
(v020) foo@bar:~/myproject/henxel$ pip list
(v020) foo@bar:~/myproject/henxel$ pip install dist/henxel-0.2.0.tar.gz
(v020) foo@bar:~/myproject/henxel$ deactivate
```

Now you are ready to launch both versions of your project and do side-by-side comparison if that is what you want:

```console
foo@bar:~/myproject/henxel$ . env/bin/activate
(env) foo@bar:~/myproject/henxel$ pip list
```

From other shell-window:

```console
foo@bar:~/myproject$ . v020/bin/activate
(v020) foo@bar:~/myproject$ pip list
```


# More resources
[Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
