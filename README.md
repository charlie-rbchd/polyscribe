# polyscribe #
Polyscribe is an easy-to-use polyphonic multi-track audio to sheet music converter.

## Prerequisites ##
- Python >= 2.7
- [Lilypond](http://www.lilypond.org/)
- [wxPython](http://www.wxpython.org/)

## Installation ##
Dependencies (music21, numpy, scipy, matplotlib & ObjectListView) can be installed using pip:
```
pip install -r requirements.txt
```

## How to use ##
Polyscribe can be either used in command-line mode or in graphical mode (with a GUI). When the program is invoked without any command-line argument, that is ```python polyscribe.py```, the GUI is launched. Otherwise, the program is launched in command-line mode. A list of the arguments that can be specified is available using the help command: ```python polyscribe --help```.
