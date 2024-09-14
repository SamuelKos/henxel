#!/usr/bin/env osascript


tell application "System Events"

	key down {control}
	keystroke "d"
	key up {control}
	
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








