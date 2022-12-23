# Changelog
* To version: 	0.0.6
* From version:	0.0.3

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
	and more responsive. Im keeping copy of version 0.0.5 so it can be used as a reference.
	About event <<'WidgetViewSync'>> :
	It is generated when doing: insert, delete or screen geometry change. Also on almost all font-changes but
	not when scrolling, so this is the reason why update_linenums is called also from sbset_override.
	This really made a difference. It is now child-play to do things like toggle-linenums etc.
* Started replacing usage of % in strings with f-strings. Now all calls to print() are %-free. Only ~150 replacements left.


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
