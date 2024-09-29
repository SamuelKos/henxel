#!/usr/bin/env osascript

# Exit from python-console to Terminal after debug-session
tell application "System Events"
	key down {control}
	keystroke "d"
	key up {control}
end tell


# Do launch-test
set one to "1"
set res to do shell script "./launch_test.sh"


# Did not launch
if (res = one) then

	# Get err msg
	set errmesg to do shell script "./launch_test_err_msg.sh"
	
	# print error message to console
	log errmesg
	log "--------------------------------------------"
	log "Editor did not launch after last updates."
	log "Error message is above. Going to stash-start editor now."
	log " --> files are up-to date, editor is from last commit"
	log "--------------------------------------------"
	
	tell application "System Events"
	
		keystroke "python"
		key down {return}
		key up {return}

		keystroke "import subprocess"
		key down {return}
		key up {return}
		
		# Assuming last commit did launch:
		# 1: stash, (save away for a while), changes after last commit 
		keystroke "subprocess.run('git stash -q'.split())"
		key down {return}
		key up {return}
		
		# Using 'old' version from last commit
		keystroke "import henxel"
		key down {return}
		key up {return}
	
		# 2: Bring back what was stashed, that is,
		# everything is like before stashing. 
		keystroke "subprocess.run('git stash pop -q'.split())"
		key down {return}
		key up {return}

		# Launch
		keystroke "e=henxel.Editor"
		key down {return}
		key up {return}

else
	#log res
	
	# Editor is launchable
	tell application "System Events"
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
	
end if





