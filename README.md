# Henxel
GUI-editor for Python development. Tested to work with Debian Bullseye


# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Line numbering
* Tabbed editing
* Show git-branch
* Run current file
* Search - Replace
* Indent - Unindent
* Comment - Uncomment
* Click to open errors
* Persistent configuration
* Near persistent contents

# Lacking
* Auto-completion
* Hinting
* Syntax highlighting

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
Consider creating virtual environment for your python-projects and installing python packages like this editor to it. In debian you have to first install this package: python3-venv:

```console
foo@bar:~$ sudo apt install python3-venv
```

Then save this script to file named 'mkvenv' to some place nice like bin-directory in your home-directory:
```console
#!/usr/bin/env bash
# Create a new virtual environment for python.
# Usage: mkvenv [name_of_myvenv]
# If no argument is given this  defaults to creating virtual environment
# named "venv"


if [[ "$#" -gt 1 ]]; then
 echo "mkvenv: Illegal number of parameters"
 exit 1
elif [[ "$#" -eq 0 ]]; then
 newdir="venv"
else
 var="$1"
 isdash=${var::1}
 if  [[ $isdash == "-" ]]; then
  echo "Usage: mkvenv [name_of_myvenv]"
  echo "If no argument is given this  defaults to creating virtual environment"
  echo 'named "venv"'
  exit 1
 else
  newdir=$1
 fi
fi

# First: update pip and setuptools and then install wheel
python3 -m venv ${newdir}		&& \

. ${newdir}/bin/activate		&& \

pip install -U pip			&& \
pip install -U setuptools		&& \
pip install wheel			&& \
echo ""					&& \
echo "venv installed succesfully"	&& \
echo ""					&& \

# Second: install normal requirements
if [[ -e requirements.txt ]]; then
 pip install -r requirements.txt	&& \
 echo ""				&& \
 echo "requirements installed succesfully"

fi
```

Then make it executable:
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

To remove venv just remove the env-directory and you can start from clean desk making new one with mkvenv later.
* Optional end

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


# More resources
[Changelog](https://github.com/SamuelKos/henxel/blob/main/CHANGELOG.md)

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
