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

from music21 import *
import wave

def _interpolation(correlation, peak):
    """Interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known."""

    curr = correlation[peak]
    prev = correlation[peak - 1] if peak - 1 >= 0 else curr
    next = correlation[peak + 1] if peak + 1 < len(correlation) else curr

    vertex = (prev - next) / (prev - 2.0 * curr + next)
    vertex = vertex * 0.5 + peak
    return vertex

# Replace the music21 interpolation function with ours.
audioSearch.interpolation = _interpolation

def polyphonicStreamFromFiles(filenames):
    """Generate a multi-part score using each file as a part."""

    parts = [monophonicStreamFromFile(filename) for filename in filenames]
    score = stream.Score()
    for part in parts:
        score.append(part)
    return score

def monophonicStreamFromFile(filename):
    """Generate a score part from a wav file."""

    wv = wave.open(filename, 'r')
    audioSearch.recordSampleRate = wv.getframerate()
    wv.close()

    audioSearch.audioChunkLength = 1024

    return audioSearch.transcriber.monophonicStreamFromFile(filename)
