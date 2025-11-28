#!/usr/bin/env osascript

tell application "System Events"

	# Exit from python-console to Terminal after debug-session
	key down {control}
	keystroke "d"
	key up {control}
	
	# Then, relaunch editor
	keystroke "python"
	key down {return}
	key up {return}
	
	keystroke "import henxel"
	key down {return}
	key up {return}
	
	keystroke "e=henxel.Editor(debug=True)"
	key down {return}
	key up {return}

end tell


