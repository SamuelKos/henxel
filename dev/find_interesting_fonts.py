
import tkinter
import tkinter.font
import time
root = tkinter.Tk()
def_size = 16
textfont = tkinter.font.Font(family='Andale Mono', size=def_size, name='textfont')
otherfont = tkinter.font.Font(family='Optima', size=15, name='otherfont')

fontname_textfont = textfont.actual()['family']
fontname_otherfont = otherfont.actual()['family']

fontfamilies = [f for f in tkinter.font.families() if f not in [fontname_textfont, fontname_otherfont] ]

textwid = tkinter.Text(root, font=textfont)
textwid.tag_config('texttag', font=textfont)
textwid.tag_config('othertag', font=otherfont, offset=1)
textwid.insert('1.0', 'BBB\nBBB\nBBB\n')

textwid.mark_set('insert', '1.0')
textwid.tag_add('texttag', '1.0', '1.3')
textwid.tag_add('othertag', '2.0', '2.3')

textwid.pack()

textwid.update_idletasks()
textheight = textwid.dlineinfo('insert')[3]
otherheight = textwid.dlineinfo('insert +1lines')[3]
#print(f'{textfont.metrics()["linespace"]} {otherfont.metrics()["linespace"]} {textheight=} {otherheight=}')




def get_metrics(font):
	m = font.metrics()
	descent = m['descent']
	linespace = m['linespace']

	return descent, linespace


def print_metrics(values):
	descent, linespace = values
	print(f'{descent=}, {linespace=}')



print(f'1/{len(fontfamilies)} {fontname_textfont}')
m = get_metrics(textfont)
##print_metrics(m)
descent_textfont = m[0]
linespace_textfont = m[1]
print(f'2/{len(fontfamilies)} {fontname_otherfont}')
m = get_metrics(otherfont)
##print_metrics(m)

i = 2
total = 0
for fontname in fontfamilies:
	i += 1
	# First equalize linespace
	size = def_size
	otherfont.config(family=fontname, size=def_size)
	m = get_metrics(otherfont)
	linespace_otherfont = m[1]
	while linespace_otherfont > linespace_textfont:
		#print(linespace_otherfont, linespace_textfont, size)
		size -= 1
		otherfont.config(size=size)
		m = get_metrics(otherfont)
		linespace_otherfont = m[1]


##	if linespace_otherfont == linespace_textfont:
##		if m[0] - descent_textfont != 0:
##			print()
##			print(f'{i}/{len(fontfamilies)} {fontname}, {size=}, diff_desc:{m[0] - descent_textfont}')
##			total +=1



	# Then check if near descent_textfont
	# +1 descent is fixable
##	if m[0] - descent_textfont == 1:
##
##		for i in (1,2,3):
##			size -= 1
##			otherfont.config(size=size)
##			m = get_metrics(otherfont)
##			if m[0] - descent_textfont == 0:
##				print()
##				print(f'{i}/{len(fontfamilies)} {fontname}, {size=}, diff_desc:{m[0] - descent_textfont}')
##				total +=1
##				break

	if m[0] - descent_textfont > 1:
		print()
		print(f'{i}/{len(fontfamilies)} {fontname}, {size=}, diff_desc:{m[0] - descent_textfont}')
		total +=1



print(f'{total=}')



#root.mainloop()
























