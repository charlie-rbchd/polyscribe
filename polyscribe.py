# The MIT License (MIT)

# Copyright (c) 2015 Joel Robichaud

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

if __name__ == "__main__":
    import sys
    import convert

    converter = convert.AudioToSheetMusicConverter()

    if len(sys.argv) < 2:
        import wx
        import gui

        # Launch the graphic user interface if no command-line arguments are supplied
        app = wx.App(False)
        frame = gui.MainFrame(converter)
        app.MainLoop()
    else:
        import os
        import argparse

        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="convert polyphonic multi-track audio to sheet music")
        parser.add_argument("input", metavar="INPUT", type=str, nargs="+", help="input file(s) path(s)")
        parser.add_argument("--output", type=str, nargs=1, help="output file path (without extension)")

        args = parser.parse_args(sys.argv[1:])

        # Expand path arguments into absolute paths
        input = [os.path.abspath(filename) for filename in args.input if os.path.exists(filename)]
        output = args.output[0] if args.output else "output"
        output = os.path.abspath(output)

        # Convert input files and output the result
        for progress in converter.convert(input, output): continue
        os.remove(output)
