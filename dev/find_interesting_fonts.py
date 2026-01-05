
import tkinter
import tkinter.font
import time

root = tkinter.Tk()
textfont = tkinter.font.Font(family='TkDefaulFont', size=12, name='textfont')
fontname = textfont.actual()['family']
fontfamilies = [f for f in tkinter.font.families() if f != fontname]
textwid = tkinter.Text(root, font=textfont)
textwid.pack()

def get_metrics(font):
	m = font.metrics()
	ascent = m['ascent']
	descent = m['descent']
	linespace = m['linespace']

	return ascent, descent, linespace

def print_metrics(values):
	ascent, descent, linespace = values
	print(f'ascent: {ascent}, descent: {descent}, linespace: {linespace}')



print(f'1/{len(fontfamilies)} {fontname}')
m = get_metrics(textfont)
print_metrics(m)

curascent = m[0]
curdescent = m[1]
i = 1

for fontname in fontfamilies:
	i += 1
	textfont.config(family=fontname)
	m = get_metrics(textfont)
	if m[0] != curascent or m[1] != curdescent:
		curascent = m[0]
		curdescent = m[1]

		print(f'{i}/{len(fontfamilies)} {fontname}')
		print_metrics(m)
		time.sleep(2)



#root.mainloop()
























