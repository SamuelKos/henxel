# Changelog
* To version: 	0.0.5
* From version:	0.0.3

# 0.0.5
* Small fix in getLineNumbers()
* Added borders etc.
* You can now walk back with: alt-q
* File open -dialog width is increased
* Close open dialogs when quitting, tk_chooseColor is problematic though
	(it might have own temporary root)
* Dumped 'proxy-undo',  reason being lag-increase, files are in /dev if interested
* If get motivation to continue with undo, I will go with ungrid, also in /dev


# 0.0.4
* Made decision not to try to do tab-specific undo, for reasons you can read in dev/todo.py
* Undo should no longer clear contents.
* Pasting from editor to console works again.
* Changed title of file selection dialog --> select file
* Changed title of editor: 3/5 --> 00@00
* Added dev-dir to repo and some may be useful -files there
* Updated mkvenv in readme
