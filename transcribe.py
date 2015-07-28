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

from aubio import pvoc, onset, source, pitch, freqtomidi
from numpy import array, hstack, zeros

from music21 import stream

def plotOnsets(filename):
    win_s = 512                 # fft size
    hop_s = win_s / 2           # hop size

    samplerate = 0

    s = source(filename, samplerate, hop_s)
    samplerate = s.samplerate
    o = onset("default", win_s, hop_s, samplerate)

    # list of onsets, in samples
    onsets = []

    # storage for plotted data
    desc = []
    tdesc = []
    allsamples_max = zeros(0,)
    downsample = 2  # to plot n samples / hop_s

    # total number of frames read
    total_frames = 0
    while True:
        samples, read = s()
        if o(samples):
            # print "%f" % (o.get_last_s())
            onsets.append(o.get_last())
        # keep some data to plot it later
        new_maxes = (abs(samples.reshape(hop_s/downsample, downsample))).max(axis=0)
        allsamples_max = hstack([allsamples_max, new_maxes])
        desc.append(o.get_descriptor())
        tdesc.append(o.get_thresholded_descriptor())
        total_frames += read
        if read < hop_s: break

    if 1:
        # do plotting
        from numpy import arange
        import matplotlib.pyplot as plt
        allsamples_max = (allsamples_max > 0) * allsamples_max
        allsamples_max_times = [ float(t) * hop_s / downsample / samplerate for t in range(len(allsamples_max)) ]
        plt1 = plt.axes([0.1, 0.75, 0.8, 0.19])
        plt2 = plt.axes([0.1, 0.1, 0.8, 0.65], sharex = plt1)
        plt.rc('lines',linewidth='.8')
        plt1.plot(allsamples_max_times,  allsamples_max, '-b')
        plt1.plot(allsamples_max_times, -allsamples_max, '-b')
        for stamp in onsets:
            stamp /= float(samplerate)
            plt1.plot([stamp, stamp], [-1., 1.], '-r')
        plt1.axis(xmin = 0., xmax = max(allsamples_max_times) )
        plt1.xaxis.set_visible(False)
        plt1.yaxis.set_visible(False)
        desc_times = [ float(t) * hop_s / samplerate for t in range(len(desc)) ]
        desc_plot = [d / max(desc) for d in desc]
        plt2.plot(desc_times, desc_plot, '-g')
        tdesc_plot = [d / max(desc) for d in tdesc]
        for stamp in onsets:
            stamp /= float(samplerate)
            plt2.plot([stamp, stamp], [min(tdesc_plot), max(desc_plot)], '-r')
        plt2.plot(desc_times, tdesc_plot, '-y')
        plt2.axis(ymin = min(tdesc_plot), ymax = max(desc_plot))
        plt.xlabel('time (s)')
        #plt.savefig('/tmp/t.png', dpi=200)
        plt.show()

def plotPitches(filename):
    downsample = 1
    samplerate = 44100 / downsample

    win_s = 4096 / downsample # fft size
    hop_s = 512  / downsample # hop size

    s = source(filename, samplerate, hop_s)
    samplerate = s.samplerate

    tolerance = 0.8

    pitch_o = pitch("yin", win_s, hop_s, samplerate)
    pitch_o.set_unit("freq")
    pitch_o.set_tolerance(tolerance)

    pitches = []
    confidences = []

    # total number of frames read
    total_frames = 0
    while True:
        samples, read = s()
        p = pitch_o(samples)[0]
        #p = int(round(p))
        confidence = pitch_o.get_confidence()
        #if confidence < 0.8: p = 0.
        # print "%f %f %f" % (total_frames / float(samplerate), p, confidence)
        pitches += [p]
        confidences += [confidence]
        total_frames += read
        if read < hop_s: break

    #print pitches
    from numpy import array, ma
    import matplotlib.pyplot as plt

    skip = 1

    pitches = array(pitches[skip:])
    confidences = array(confidences[skip:])
    times = [t * hop_s for t in range(len(pitches))]

    fig = plt.figure()

    ax1 = fig.add_subplot(311)
    ax1 = get_waveform_plot(filename, samplerate = samplerate, block_size = hop_s, ax = ax1)
    plt.setp(ax1.get_xticklabels(), visible = False)
    ax1.set_xlabel('')

    def array_from_text_file(filename, dtype = 'float'):
        import os.path
        from numpy import array
        filename = os.path.join(os.path.dirname(__file__), filename)
        return array([line.split() for line in open(filename).readlines()],
            dtype = dtype)

    ax2 = fig.add_subplot(312, sharex = ax1)
    import sys, os.path
    ground_truth = os.path.splitext(filename)[0] + '.f0.Corrected'
    if os.path.isfile(ground_truth):
        ground_truth = array_from_text_file(ground_truth)
        true_freqs = ground_truth[:,2]
        true_freqs = ma.masked_where(true_freqs < 2, true_freqs)
        true_times = float(samplerate) * ground_truth[:,0]
        ax2.plot(true_times, true_freqs, 'r')
        ax2.axis( ymin = 0.9 * true_freqs.min(), ymax = 1.1 * true_freqs.max() )
    # plot raw pitches
    ax2.plot(times, pitches, '--g')
    # plot cleaned up pitches
    cleaned_pitches = pitches
    #cleaned_pitches = ma.masked_where(cleaned_pitches < 0, cleaned_pitches)
    #cleaned_pitches = ma.masked_where(cleaned_pitches > 120, cleaned_pitches)
    cleaned_pitches = ma.masked_where(confidences < tolerance, cleaned_pitches)
    ax2.plot(times, cleaned_pitches, '.-')
    #ax2.axis( ymin = 0.9 * cleaned_pitches.min(), ymax = 1.1 * cleaned_pitches.max() )
    #ax2.axis( ymin = 55, ymax = 70 )
    plt.setp(ax2.get_xticklabels(), visible = False)
    ax2.set_ylabel('f0 (Hz)')

    # plot confidence
    ax3 = fig.add_subplot(313, sharex = ax1)
    # plot the confidence
    ax3.plot(times, confidences)
    # draw a line at tolerance
    ax3.plot(times, [tolerance]*len(confidences))
    ax3.axis( xmin = times[0], xmax = times[-1])
    ax3.set_ylabel('condidence')
    set_xlabels_sample2time(ax3, times[-1], samplerate)
    plt.show()
    #plt.savefig(os.path.basename(filename) + '.svg')

def get_waveform_plot(filename, samplerate = 0, block_size = 4096, ax = None, downsample = 2**4):
    import matplotlib.pyplot as plt
    if not ax:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    hop_s = block_size

    allsamples_max = zeros(0,)
    downsample = downsample  # to plot n samples / hop_s

    a = source(filename, samplerate, hop_s)            # source file
    if samplerate == 0: samplerate = a.samplerate

    total_frames = 0
    while True:
        samples, read = a()
        # keep some data to plot it later
        new_maxes = (abs(samples.reshape(hop_s/downsample, downsample))).max(axis=0)
        allsamples_max = hstack([allsamples_max, new_maxes])
        total_frames += read
        if read < hop_s: break
    allsamples_max = (allsamples_max > 0) * allsamples_max
    allsamples_max_times = [ ( float (t) / downsample ) * hop_s for t in range(len(allsamples_max)) ]

    ax.plot(allsamples_max_times,  allsamples_max, '-b')
    ax.plot(allsamples_max_times, -allsamples_max, '-b')
    ax.axis(xmin = allsamples_max_times[0], xmax = allsamples_max_times[-1])

    set_xlabels_sample2time(ax, allsamples_max_times[-1], samplerate)
    return ax

def set_xlabels_sample2time(ax, latest_sample, samplerate):
    ax.axis(xmin = 0, xmax = latest_sample)
    if latest_sample / float(samplerate) > 60:
        ax.set_xlabel('time (mm:ss)')
        ax.set_xticklabels([ "%02d:%02d" % (t/float(samplerate)/60, (t/float(samplerate))%60) for t in ax.get_xticks()[:-1]], rotation = 50)
    else:
        ax.set_xlabel('time (ss.mm)')
        ax.set_xticklabels([ "%02d.%02d" % (t/float(samplerate), 100*((t/float(samplerate))%1) ) for t in ax.get_xticks()[:-1]], rotation = 50)


def polyphonicStreamFromFiles(filenames):
    """Generate a multi-part score using each file as a part."""

    parts = [monophonicStreamFromFile(filename) for filename in filenames]
    score = stream.Score()
    for part in parts:
        score.append(part)
    return score

def monophonicStreamFromFile(filename):
    """Generate a score part from a wav file."""

    # plotOnsets(filename)
    plotPitches(filename)

    part = stream.Part()

    return part
