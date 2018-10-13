from scipy import signal
import numpy as np
import struct
import wave

DEFAULT_SAMPLE_RATE = 44100
MINIMAL_TIME = 60.0 / 400.0
MINIMAL_AMPLITUDE_RATE = 3.0
MINIMAL_AMPLITUDE_DIFF = 200000


class Note:
    def __init__(self, tone, start_time, end_time=None):
        self.tone = tone
        self.start_time = start_time
        self.end_time = end_time


def get_notes(frequencies, times, spectrogram, num_of_notes=3, minimal_time=MINIMAL_TIME):
    frequency_separator_indices = []  # TODO: think of how to calculate this
    sample_time = times[1] - times[0]
    samples_per_note = (minimal_time // sample_time) + 1
    min_frequency_index = 0
    notes = []

    for note_start_index in range(len(times) // samples_per_note):
        notes.append([0] * num_of_notes)
        for frequency_index, max_frequency_index in enumerate(frequency_separator_indices):
            for index in range(samples_per_note):
                notes[-1][frequency_index] = \
                    max(notes[-1][frequency_index],
                        *spectrogram[note_start_index + index][min_frequency_index:max_frequency_index])
            min_frequency_index = max_frequency_index

    final_notes = []
    current_notes = [None] * num_of_notes
    for index, note in enumerate(notes):
        for note_index in range(len(note)):
            if notes[index + 1][note_index] - note[note_index] > MINIMAL_AMPLITUDE_DIFF and \
                    notes[index + 1][note_index] / note[note_index] > MINIMAL_AMPLITUDE_RATE:
                current_time = times[index * samples_per_note]
                if current_notes[note_index]:
                    current_notes[note_index].end_time = current_time
                final_notes.append(Note(note_index, current_time))
                current_notes[note_index] = final_notes[-1]
            if note[note_index] - notes[index + 1][note_index] > MINIMAL_AMPLITUDE_DIFF and \
                    note[note_index] / notes[index + 1][note_index] > MINIMAL_AMPLITUDE_RATE:
                if current_notes[note_index]:
                    current_notes[note_index].end_time = current_time
                    current_notes[note_index] = None
    return final_notes


def get_spectrogram(data, sample_rate=DEFAULT_SAMPLE_RATE, nfft=None):
    data_array = np.array(data)
    frequencies, times, spectrogram = signal.spectrogram(data_array, fs=sample_rate, nfft=nfft or sample_rate)
    return frequencies, times, np.swapaxes(spectrogram, 0, 1)


def read_wav_file(file_path):
    with wave.open(file_path) as wav_file:
        nframes = wav_file.getnframes()
        data = wav_file.readframes(nframes)
        return struct.unpack(f'{nframes}h', data), wav_file.getframerate()
