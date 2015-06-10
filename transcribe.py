# Copyright (c) 2011 Michael Scott Cuthbert and the music21 Project
# Copyright (c) 2015 Joel Robichaud

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of [project] nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import copy
import math
import wave
import numpy
import scipy.signal
from music21 import stream, note, pitch, scale

def interpolation(correlation, peak):
    """Interpolation for estimating the true position of an inter-sample
    maximum when nearby samples are known."""

    curr = correlation[peak]
    prev = correlation[peak - 1] if peak - 1 >= 0 else curr
    next = correlation[peak + 1] if peak + 1 < len(correlation) else curr

    vertex = (prev - next) / (prev - 2.0 * curr + next)
    vertex = vertex * 0.5 + peak
    return vertex

def getFrequenciesFromAudioFile(filename, blocksize=512):
    """Retrieve a list of frequencies from an audio file."""

    wv = wave.open(filename, 'r')
    srate = wv.getframerate()
    blocks = []
    for i in range(int(wv.getnframes() / blocksize)):
        data = wv.readframes(blocksize)
        blocks.append(data)
    wv.close()

    freqs = []
    for data in blocks:
        samples = numpy.fromstring(data, dtype=numpy.int16)
        freqs.append(autocorrelationFunction(samples, srate))

    return freqs

def autocorrelationFunction(signal, srate):
    """Convert a signal from the time domain into the frequency domain."""

    signal = numpy.array(signal)
    correlation = scipy.signal.fftconvolve(signal, signal[::-1], mode='full')
    lengthCorrelation = len(correlation) / 2
    correlation = correlation[lengthCorrelation:]
    difference = numpy.diff(correlation) # Calculate the difference between slots
    positiveDifferences, = numpy.nonzero(numpy.ravel(difference > 0))
    if len(positiveDifferences) == 0:
        finalResult = 10 # Rest
    else:
        beginning = positiveDifferences[0]
        peak = numpy.argmax(correlation[beginning:]) + beginning
        vertex = interpolation(correlation, peak)
        finalResult = srate / vertex
    return finalResult

def detectPitchFrequencies(freqFromAQList, useScale=None):
    """Detect the pitches of the notes from a list of frequencies."""

    if useScale is None:
        useScale = scale.MajorScale('C4')
    (thresholds, pitches) = prepareThresholds(useScale)

    detectedPitchesFreq = []

    for i in range(len(freqFromAQList)): # Find thresholds and frequencies
        inputPitchFrequency = freqFromAQList[i]
        unused_freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)
        detectedPitchesFreq.append(pitch_name.frequency)
    return detectedPitchesFreq

def normalizeInputFrequency(inputPitchFrequency, thresholds=None, pitches=None):
    """Return a tuple of the normalized frequency and the pitch detected."""

    if ((thresholds is None and pitches is not None)
         or (thresholds is not None and pitches is None)):
        raise AudioSearchException("Cannot normalize input frequency if both thresholds and pitches are not given.")
    elif thresholds == None:
        (thresholds, pitches) = prepareThresholds()

    inputPitchLog2 = math.log(inputPitchFrequency, 2)
    (remainder, octave) = math.modf(inputPitchLog2)
    octave = int(octave)

    for i in range(len(thresholds)):
        threshold = thresholds[i]
        if remainder < threshold:
            returnPitch = copy.deepcopy(pitches[i])
            returnPitch.octave = octave - 4
            name_note = pitch.Pitch(str(pitches[i]))
            return name_note.frequency, returnPitch

    returnPitch = copy.deepcopy(pitches[-1])
    returnPitch.octave = octave - 3
    returnPitch.inputFrequency = inputPitchFrequency
    name_note = pitch.Pitch(str(pitches[-1]))
    return name_note.frequency, returnPitch

def prepareThresholds(useScale=None):
    """Return a tuple of two lists consisting of the threshold values and the
    pitches of a scale."""

    if useScale is None:
        useScale = scale.ChromaticScale('C4')

    scPitches = useScale.pitches
    scPitchesRemainder = []

    for p in scPitches:
        pLog2 = math.log(p.frequency, 2)
        scPitchesRemainder.append(math.modf(pLog2)[0])
    scPitchesRemainder[-1] += 1

    scPitchesThreshold = []
    for i in range(len(scPitchesRemainder) - 1):
        scPitchesThreshold.append((scPitchesRemainder[i] + scPitchesRemainder[i + 1]) / 2)

    return scPitchesThreshold, scPitches

def smoothFrequencies(detectedPitchesFreq, smoothLevels=7, inPlace=True):
    """Smooth the shape of the signal in order to avoid false detections of
    the fundamental frequency."""

    dpf = detectedPitchesFreq
    if inPlace == True:
        detectedPitchesFreq = dpf
    else:
        detectedPitchesFreq = copy.copy(dpf)

    beginning = 0.0
    ends = 0.0

    for i in range(smoothLevels):
        beginning = beginning + float(detectedPitchesFreq[i])
        ends = ends + detectedPitchesFreq[len(detectedPitchesFreq) - 1 - i]
    beginning = beginning / smoothLevels
    ends = ends / smoothLevels

    for i in range(len(detectedPitchesFreq)):
        if i < int(math.floor(smoothLevels / 2.0)):
            detectedPitchesFreq[i] = beginning
        elif i > len(detectedPitchesFreq) - int(math.ceil(smoothLevels / 2.0)) - 1:
            detectedPitchesFreq[i] = ends
        else:
            t = 0
            for j in range(smoothLevels):
                t = t + detectedPitchesFreq[i + j - int(math.floor(smoothLevels / 2.0))]
            detectedPitchesFreq[i] = t / smoothLevels

    return [int(round(fq)) for fq in detectedPitchesFreq]

def pitchFrequenciesToObjects(detectedPitchesFreq, useScale=None):
    """Return a list of the pitches that best match the input frequencies."""

    if useScale is None:
        useScale = scale.MajorScale('C4')

    detectedPitchObjects = []
    (thresholds, pitches) = prepareThresholds(useScale)

    for i in range(len(detectedPitchesFreq)):
        inputPitchFrequency = detectedPitchesFreq[i]
        unused_freq, pitch_name = normalizeInputFrequency(inputPitchFrequency, thresholds, pitches)
        detectedPitchObjects.append(pitch_name)

    i = 0
    while i < len(detectedPitchObjects) - 1:
        name = detectedPitchObjects[i].name
        hold = i
        tot_octave = 0
        while i < len(detectedPitchObjects) - 1 and detectedPitchObjects[i].name == name:
            tot_octave = tot_octave + detectedPitchObjects[i].octave
            i = i + 1
        tot_octave = round(tot_octave / (i - hold))
        for j in range(i - hold):
            detectedPitchObjects[hold + j - 1].octave = tot_octave
    return detectedPitchObjects

def joinConsecutiveIdenticalPitches(detectedPitchObjects):
    """Return a tuple of two lists consisting of a list of note and rest
    objects (each of quarterLength 1.0) and a list of how many pitches were
    joined together to make that object."""

    REST_FREQUENCY = 10
    detectedPitchObjects[0].frequency = REST_FREQUENCY

    j = 0
    good = 0
    bad = 0
    valid_note = False

    total_notes = 0
    total_rests = 0
    notesList = []
    durationList = []

    while j < len(detectedPitchObjects):
        fr = detectedPitchObjects[j].frequency

        # Detect consecutive instances of the same frequency
        while j < len(detectedPitchObjects) and fr == detectedPitchObjects[j].frequency:
            good = good + 1

            # If more than 6 consecutive identical samples, it might be a note
            if good >= 6:
                valid_note = True

                # If we've gone 15 or more samples without getting something constant, assume it's a rest
                if bad >= 15:
                    durationList.append(bad)
                    total_rests = total_rests + 1
                    notesList.append(note.Rest())
                bad = 0
            j = j + 1
        if valid_note == True:
            durationList.append(good)
            total_notes = total_notes + 1
            n = note.Note()
            n.pitch = detectedPitchObjects[j - 1]
            notesList.append(n)
        else:
            bad = bad + good
        good = 0
        valid_note = False
        j = j + 1
    return notesList, durationList

def notesAndDurationsToStream(notesList, durationList, removeRestsAtBeginning=True):
    """Take a list of objects or rests and an equally long list of how long
    each ones lasts in terms of samples and return a Stream using the information
    from quarterLengthEstimation and quantizeDurations."""

    qle = quarterLengthEstimation(durationList)
    part = stream.Part()

    for i in range(len(durationList)):
        actualDuration = quantizeDuration(durationList[i] / qle)
        notesList[i].quarterLength = actualDuration
        if removeRestsAtBeginning and notesList[i].name == "rest":
            pass
        else:
            part.append(notesList[i])
            removeRestsAtBeginning = False

    return part

def quarterLengthEstimation(durationList, mostRepeatedQuarterLength=1.0):
    """Take a list of lengths of notes (measured in audio samples) and try to
    estimate what the length of a quarter note should be in this list."""

    dl = copy.copy(durationList)
    dl.append(0)

    pdf, bins = histogram(dl,8.0)
    i = len(pdf) - 1
    while pdf[i] != max(pdf):
        i = i - 1

    qle = (bins[i] + bins[i + 1]) / 2.0

    if mostRepeatedQuarterLength == 0:
        mostRepeatedQuarterLength = 1.0

    binPosition = 0 - math.log(mostRepeatedQuarterLength, 2)
    qle = qle * math.pow(2, binPosition) # Normalize the length to a quarter note

    return qle

def histogram(data, bins):
    """Partition a list into a number of bins and return the number of elements
    in each bins and a set of elements where the first element is the start of
    the first bin, the last element is the end of the last bin, and every remaining
    element is the dividing point between one bin and another."""

    maxValue = max(data)
    minValue = min(data)
    lengthEachBin = (maxValue-minValue) / bins

    container = []
    for i in range(int(bins)):
        container.append(0)
    for i in data:
        count = 1
        while i > minValue + count*lengthEachBin:
            count += 1
        container[count - 1] += 1

    binsLimits = []
    binsLimits.append(minValue)
    count = 1
    for i in range(int(bins)):
        binsLimits.append(minValue+count*lengthEachBin)
        count +=1
    return container, binsLimits

def quantizeDuration(length):
    """Round an approximated quarterLength duration to better one."""

    length = length * 100
    typicalLengths = [25.00, 50.00, 100.00, 150.00, 200.00, 400.00]
    thresholds = []
    for i in range(len(typicalLengths) - 1):
        thresholds.append((typicalLengths[i] + typicalLengths[i + 1]) / 2)

    finalLength = typicalLengths[0]
    for i in range(len(thresholds)):
        threshold = thresholds[i]
        if length > threshold:
            finalLength = typicalLengths[i + 1]
    return finalLength / 100

def polyphonicStreamFromFiles(filenames):
    """Generate a multi-part score using each file as a part."""

    parts = [monophonicStreamFromFile(filename) for filename in filenames]
    score = stream.Score()
    for part in parts:
        score.append(part)
    return score

def monophonicStreamFromFile(filename):
    """Generate a score part from a wav file."""

    useScale = scale.ChromaticScale()

    freqFromAQList = getFrequenciesFromAudioFile(filename, 256)

    detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale)
    detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)

    detectedPitchObjects = pitchFrequenciesToObjects(detectedPitchesFreq, useScale)
    (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
    part = notesAndDurationsToStream(notesList, durationList, removeRestsAtBeginning=True)
    return part
