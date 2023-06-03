# Key press prototype
# Tracks keys as pressed, ignoring the keyboard repeater
# Current keys down are kept in a dictionary.
# That a key is pressed is flagged, and the last key pressed is tracked

import tkinter

winWid = 640
winHei = 480
keyDown = False
lastKey = "none"
keyChange = keyDown
keyList = {}
timerhandle = None

def onKeyDown(event):
	global keyDown, lastKey, keyList
	print('down', event.keysym)
	if event.keysym not in keyList:
		keyList[event.keysym] = "down"
		print(keyList)
	keyDown = True
	lastKey = event.keysym

def onKeyUp(event):
	print('up', event.keysym)
	global keyDown, keyList
	if event.keysym in keyList:
		keyList.pop(event.keysym)
	if len(keyList) == 0:
		keyDown = False
	print(keyList)
	
#onTimer is present to show keyboard action as it happens.
#It is not needed to track the key changes, and it can be
#removed.
def onTimer():
	global keyChange, timerhandle, KeyDown, lastKey
	if keyDown != keyChange:
		keyChange = keyDown
		if keyDown:
			print("Key down, last key pressed - " + lastKey)
		else:
			print("Key up, last key pressed - " + lastKey)
	timerhandle = window.after(20,onTimer)
	
def onShutdown():
	global timerhandle
	window.after_cancel(timerhandle)
	window.destroy()

window = tkinter.Tk()
frame = tkinter.Canvas(window, width=winWid, height=winHei, bg="black")
frame.pack()

frame.bind("<Any-KeyPress>", onKeyDown)
frame.bind("<Any-KeyRelease>", onKeyUp)
frame.focus_set()

timerhandle = window.after(20,onTimer)
window.protocol("WM_DELETE_WINDOW",onShutdown)
window.mainloop()
