# Changelog
* To version: 	0.0.9
* From version:	0.0.3

# 0.0.9
* Fix for: being able modify contents at the beginning of search.
* Cursor pos is again set after editor launch
* Clarified some varnames: like tag 'found' to 'focus'
* Dumped tkinter.filedialog.FileDialog. Instead use now fdialog.FDialog
* Tested setting cursor blink off when idle but it added too much overhead, so left as is.
	(Had to bind to: Button, KeyRelease, FocusIn and it seemed to be too much.)


# 0.0.8
* Reorder grid-related stuff in init to make instantiation of editor feel more instant.
* You can now toggle linenumbers with Alt-l (as lemon). This adds a new option to conf meaning this version is not compatible with earlier ones.
* Adjusted colors and borders for filedialog.Filedialog used in load().
* Made small fix to no_copy_ln(). If encounter problem with copying from editor to shell or console, try
first to copy something from shell or console to editor and retry. I have not had this issue for some time now.
* Added inspect-option to popup-menu, and updated help-file for how to use it.


# 0.0.7
* Fix for: goodfonts were left commented and removed badfonts as unused.
* Removed tkinter.scrolledtext -module as unused.
* Added info how to inspect objects in help. Was thinking implementing, but I changed my mind.
* Added a section about venvs for more advanced programmers in README.


# 0.0.6
* Trailing whitespace of non-empty lines is now stripped away in tabify() when saving files to disk.
* Control-f is now binded to Text-widget instead of Toplevel. Reason is again to avoid default binding.
	It seems to center to cursor by default.
* After doing long paste, more lines than in screen, cursor was out of screen. Now view is refreshed after
	paste.
* When doing search or replace, clipboard contents is now autofilled to entry in most situations. Yes, I got
	idea from Gnome editor, which by the way has some issue showing the last lines sometimes, this is bad,
	I have always showed the lines, keeping them untouched is another story.
* Finally got rid of module random. Fonts are now initiated with family='TkDefaulFont'.
* Some renaming etc. in linenumbers.
* Linenumber update is now handled by built-in event: <<'WidgetViewSync'>>  which is great news:
	got rid of quite complex self-handled event-loop. It was working alright but this approach is simpler
	and more responsive. Im keeping copy of version 0.0.5 in dev/oldversions so it can be used as a reference. Install it with pip install oldversion.tar.gz.
	About event <<'WidgetViewSync'>> :
	It is generated when doing: insert, delete or screen geometry change. Also on almost all font-changes but
	not when scrolling, so this is the reason why update_linenums is called also from sbset_override.
	This really made a difference. It is now child-play to do things like toggle-linenums etc.
* Started replacing usage of % in strings with f-strings. Now all calls to print() are %-free. Still ~150 replacements left.


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
