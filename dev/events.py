# Run: python3 name_of_this_file.py

# Get info on key-events and mouse-button -events

import tkinter

root = tkinter.Tk()
textwid = tkinter.Text(root)

eventnum = 0

def mycallback(event=None):
	global eventnum
	eventnum += 1

	print(f'Begin Event {eventnum}:\n')

	l = [ item for item in dir(event) if '_' not in item ]

	for key in l:
		print(key, getattr(event, key))


	print(f'\nEnd Event {eventnum}:')
	print(10*'= ')
	print(event)


textwid.bind('<Any-KeyPress>', mycallback)

# Notice binding to release of button for some reasons.
textwid.bind('<Any-ButtonRelease>', mycallback)

textwid.pack()

pat = '''
Press keys in text-area and look for keysym in terminal. If certain
key gets hijacked by OS before getting keysym, one can mask it, by for example
if such a key would be windows-key, press AND hold some state-changing key
like shift, alt, etc and then try again pressing that windows-key or whatever.

It seems that one should not bind: Shift-somekey but instead
bind: Somekey if that is what it reads in keysym when pressing shift-somekey.
but other state-changing keys are more easy:
like if pressing: ctrl-alt-somekey then bind: ctrl-alt-somekey

Combining keys with mouse events might also work.
'''

label = tkinter.Label(root, text=pat)
label.pack(side=tkinter.TOP)

root.mainloop()
