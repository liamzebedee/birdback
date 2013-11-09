# While writing this I was listening to Flight of the Conchord's song 'Hiphopopotamus vs. Rhymenoceros'
# When naming, I thought I'd take a cue from the Rhymenocerous, of whose back the birds lie.

import controller
import signal

def main():
	app = None
	try:
		app = controller.Controller()
		print("Controller instantiated")
		app.run()
	except Exception as e:
		print("Exiting due to critical error:")
		print(e)
		app.quit(1)

if __name__ == '__main__':
	main()
