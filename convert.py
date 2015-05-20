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

import transcribe
from music21 import *

class AudioToSheetMusicConverter:
    """Convert audio files to sheet music."""

    def convert(self, filenames, destination):
        """Convert wav files into pdf using lilypond as renderer."""

        max_progress = len(filenames) + 2
        progress = 0

        parts = []
        for filename in filenames:
            parts.append(transcribe.monophonicStreamFromFile(filename))
            progress += 1
            yield int(float(progress) / float(max_progress) * 100)

        score = stream.Score()
        for part in parts:
            score.append(part)
        progress += 1
        yield int(float(progress) / float(max_progress) * 100)

        score.write("lily.pdf", destination)
        progress += 1
        yield int(float(progress) / float(max_progress) * 100)
