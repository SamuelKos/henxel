# to run: python3 name_of_this_file.py

# Only scrolling down is 'implemented', as it has momemtum
# and it stops at any key or button.

# Issue
# Try scrolling down with touchpad and wait it stop and repeat.
# Notice that after couple of scrolls, it wont scroll anymore 
# without tapping the pad first.

# Also im getting to like the default scroll behaviour


import tkinter


root = tkinter.Tk()
textwid = tkinter.Text(root)


lastlevel = 0
normal_scrolling = False

scroll_loop = None
check_loop = None

key_id = None
button_id = None


def stop_scroll(event=None):
	global lastlevel, scroll_loop, key_id, button_id, textwid

	lastlevel = 0
	scroll_loop = None
	
	textwid.unbind('<Any-KeyPress>', key_id)
	textwid.unbind('<Any-ButtonPress>', button_id)
	
	key_id = None
	button_id = None
	
	return 'break'
	

def start_scrolling(event=None):
	global normal_scrolling, lastlevel, scroll_loop
	
	normal_scrolling = True
	
	if lastlevel == 0:
		scroll_loop = None
	
	if lastlevel < 10:
		lastlevel += 2
	else:
		lastlevel += 1
	
	# if not, scrolling stops
	return 'break'



textwid.bind("<ButtonPress-5>", start_scrolling)
textwid.pack()


def scroll_it():
	global scroll_loop, lastlevel, normal_scrolling, root, textwid
	
	if lastlevel > 0:
			
		if lastlevel > 40:
			#print(40)
			root.after(30, textwid.yview_scroll(320 , 'pixels'))
			
		elif lastlevel > 30:
			#print(30)
			root.after(30, textwid.yview_scroll(180 , 'pixels'))
			
		elif lastlevel > 20:
			#print(20)
			root.after(30, textwid.yview_scroll(120 , 'pixels'))
			
		elif lastlevel > 15:
			#print(15)
			root.after(30, textwid.yview_scroll(80 , 'pixels'))
			
		elif lastlevel > 10:
			#print(10)
			root.after(30, textwid.yview_scroll(40 , 'pixels'))
			
		else:
			#print(0)
			textwid.yview_scroll(1, 'units')
		
		
		lastlevel -= 2
		textwid.update_idletasks()
	
		scroll_loop = root.after(50, scroll_it)
	else:
		normal_scrolling = False
		
		

def check_it(event=None):
	global check_loop, scroll_loop, normal_scrolling, key_id, button_id, textwid, root
	
	if normal_scrolling and not scroll_loop:
	
	
		if not key_id:
			key_id = textwid.bind('<Any-KeyPress>', stop_scroll)
			button_id = textwid.bind('<Any-ButtonPress>', stop_scroll)
			textwid.update_idletasks()
			
			
		root.after(50, scroll_it)

	
	check_loop = root.after(100, check_it)




s = ''
for i in range(1, 500):
	a = 10*f'{i}'
	s += f'{i} {a} \n'
	
textwid.insert('1.0', s)



root.after(100, check_it)
root.mainloop()




################################################################




