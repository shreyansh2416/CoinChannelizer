running run.bat from terminal will install all dependencies with system python and run main.py

files:
	main.py:
		main python program that reads input from 'inputfile', prints output to terminal and saves plots in '..\Plots\' in its directory which it is supposed to create on execution

	parameters.py:
		various parameters that 'main.py' uses which are described in the file

		defaults based on short-testing:
			mark_false_breakouts = False/True
			touch_tolerance = 0.15
			breakout_tolerance = 0.12
			touch_requirement_factor = 0.1
			crossings = 8

	inputfile:
		file from which 'main.py' reads input

	requirements.txt:
		contains dependencies useful for pip installing and creating virtual environment

	readme.txt:
		instruction file


how to set up project in virtual environment (windows):
	create a virtual environment for python:
		open terminal in the '..\Shreyansh\' directory and use the command:
		'python -m venv venv'

	activate the virtual environment:
		open terminal in the '..\Shreyansh\' directory and use the command:
		'venv\Scripts\activate.bat'

	install dependencies (using pip):
		open terminal in the '..\Shreyansh\' directory and use the command:
		'pip install -r requirements.txt'


how to run project (windows):
	provide input:
		enter the input in 'inputfile' (open with any text editor)

	run 'main.py':
		open terminal in the '..\shreyansh\' directory and use the command:
		'python main.py'

find output(s) on terminal and '..\Plots\'