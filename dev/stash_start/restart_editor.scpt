#!/usr/bin/env osascript

# Exit from python-console to Terminal after debug-session
tell application "System Events"
	key down {control}
	keystroke "d"
	key up {control}
end tell

set gitroot to do shell script "git rev-parse --show-toplevel"
set file1 to gitroot & "/dev/launch_test.sh"
set file2 to gitroot & "/dev/launch_test_err_msg.sh"
#set file3 to "python " & gitroot & "/dev/launch_test.py"

#display dialog res
#log file1
#log file2

# Do launch-test
set one to "1"
set zero to "0"
set res to do shell script file1

#log res
#log "jou"

# Did not launch
if (res = one) then
	#log "is one"
	#log res
	
	# Get err msg
	set errmesg to do shell script file2
	
	# print error message to console
	log errmesg
	
	log "------------------------------------------------------"
	log "Editor did not launch after last updates."
	log "Error message is above. Going to stash-start editor now."
	log " --> files are up-to date, editor is from last commit"
	log "------------------------------------------------------"
	
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
		keystroke "e=henxel.Editor(debug=True)"
		key down {return}
		key up {return}
	end tell
	

else if (res = zero) then
	#log "is zero"
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
	
	
else
	log "is something else"
	log res
	
end if





