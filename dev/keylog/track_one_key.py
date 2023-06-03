import tkinter as tk

class KeyTracker:
	def __init__(self, on_key_press, on_key_release):
		self.on_key_press = on_key_press
		self.on_key_release = on_key_release
		self._key_pressed = False

	def report_key_press(self, event):
		if not self._key_pressed:
			self.on_key_press()
		self._key_pressed = True

	def report_key_release(self, event):
		if self._key_pressed:
			self.on_key_release()
		self._key_pressed = False


def start_recording(event=None):
	print('Recording right now!')


def stop_recording(event=None):
	print('Stop recording right now!')


if __name__ == '__main__':
	master = tk.Tk()

	key_tracker = KeyTracker(start_recording, stop_recording)
	master.bind("<KeyPress-Return>", key_tracker.report_key_press)
	master.bind("<KeyRelease-Return>", key_tracker.report_key_release)
	master.mainloop()
