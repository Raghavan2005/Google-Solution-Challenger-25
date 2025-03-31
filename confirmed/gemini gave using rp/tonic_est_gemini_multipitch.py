import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, windows
from scipy.fft import fft
import threading
import concurrent.futures

# 1. Load Audio File
audioFilePath = r"C:\Users\drivi\gdsc prog files\Google-Solution-Challenger-25\matlab\kal.mp3"  # Replace with the actual path
y, sr = librosa.load(audioFilePath, sr=None)  # Load with original sampling rate
y = librosa.to_mono(y)  # Convert to mono if stereo

# 2. Parameters
frameLength = 2048  # Length of each analysis frame (samples)
hopLength = 512  # Hop size between frames (samples)
fmin = 50  # Minimum frequency to consider (Hz) - adjust as needed
fmax = 800  # Maximum frequency to consider (Hz) - adjust as needed
numHarmonics = 5  # Number of harmonics to consider for multi-pitch detection
num_threads = 4  # Adjust number of threads based on your CPU cores

# 3. Note Mapping Parameters (A4 = 440Hz)
A4 = 440.0
A4_INDEX = 57
notes = [
    "C0", "C#0", "D0", "D#0", "E0", "F0", "F#0", "G0", "G#0", "A0", "A#0", "B0",
    "C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1", "A1", "A#1", "B1",
    "C2", "C#2", "D2", "D#2", "E2", "F2", "F#2", "G2", "G#2", "A2", "A#2", "B2",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
    "C6", "C#6", "D6", "D#6", "E6", "F6", "F#6", "G6", "G#6", "A6", "A#6", "B6",
    "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7",
    "C8", "C#8", "D8", "D#8", "E8", "F8", "F#8", "G8", "G#8", "A8", "A#8", "B8",
    "C9", "C#9", "D9", "D#9", "E9", "F9", "F#9", "G9", "G#9", "A9", "A#9", "B9"
]

# ---- Helper Function: frequencyToNote -----
def frequencyToNote(inputFrequency, A4, A4_INDEX, notes):
    """Converts a frequency to the nearest note name (similar to the JavaScript code)."""
    MINUS = 0
    PLUS = 1

    frequency = A4
    r = 2**(1/12)  # Semitone ratio
    cent = 2**(1/1200)  # Cent ratio

    r_index = 0
    cent_index = 0
    side = 0

    if inputFrequency >= frequency:
        while inputFrequency >= r * frequency:
            frequency = r * frequency
            r_index += 1
        while inputFrequency > cent * frequency:
            frequency = cent * frequency
            cent_index += 1

        if (cent * frequency - inputFrequency) < (inputFrequency - frequency):
            cent_index += 1

        if cent_index > 50:
            r_index += 1
            cent_index = 100 - cent_index
            if cent_index != 0:
                side = MINUS
            else:
                side = PLUS
        else:
            side = PLUS
    else:
        while inputFrequency <= frequency / r:
            frequency = frequency / r
            r_index -= 1
        while inputFrequency < frequency / cent:
            frequency = frequency / cent
            cent_index += 1

        if (inputFrequency - frequency/cent) < (frequency - inputFrequency):
            cent_index += 1

        if cent_index >= 50:
            r_index -= 1
            cent_index = 100 - cent_index
            side = PLUS
        else:
            if cent_index != 0:
                side = MINUS
            else:
                side = PLUS

    # Get the note
    noteIndex = A4_INDEX + r_index

    # Check index bounds (IMPORTANT: Prevent errors)
    if noteIndex < 0:  # Python list indices start at 0
        noteIndex = 0
    elif noteIndex >= len(notes):
        noteIndex = len(notes) - 1

    result = notes[noteIndex] # Use square brackets for Python list indexing

    # Append cents value
    if side == PLUS:
        result = result + " + " + str(cent_index) + " cents"  # Convert int to str
    else:
        result = result + " - " + str(cent_index) + " cents"  # Convert int to str
    return result

# --- Multithreaded Frame Processing ---
def process_frame(i, y, sr, frameLength, hopLength, numHarmonics, A4, A4_INDEX, notes, estimatedFrequencies, confidenceScores, noteNames):
    """Processes a single frame of audio data for multi-pitch analysis."""
    startIndex = i * hopLength
    endIndex = startIndex + frameLength
    frame = y[startIndex:endIndex]

    # Windowing (e.g., Hanning window)
    window = windows.hann(frameLength)
    frame = frame * window

    # Compute the Spectrum (FFT)
    N = len(frame)
    fft_frame = fft(frame, N)
    P2 = np.abs(fft_frame / N)
    P1 = P2[:N // 2 + 1]
    P1[1:-1] = 2 * P1[1:-1]
    f = sr * np.arange(N // 2 + 1) / N  # frequency axis

    # Harmonic Product Spectrum (HPS) inspired
    hps_spectrum = P1.copy()
    for h in range(2, numHarmonics + 1):
        downsampled_indices = np.arange(0, len(P1), h, dtype=int)
        hps_spectrum = hps_spectrum[:len(downsampled_indices)] * P1[downsampled_indices]

    # Estimate the Fundamental Frequency (F0)
    peak_index = np.argmax(hps_spectrum)
    estimatedF0 = f[peak_index]

    # Store the estimated frequencies and their confidence scores
    for harmonic in range(1, numHarmonics + 1):
        harmonicFrequency = estimatedF0 * harmonic
        harmonicIndex = np.argmin(np.abs(f - harmonicFrequency))

        estimatedFrequency = f[harmonicIndex]
        estimatedFrequencies[i, harmonic - 1] = estimatedFrequency
        confidenceScores[i, harmonic - 1] = P1[harmonicIndex]

        # Map to Note
        noteName = frequencyToNote(estimatedFrequency, A4, A4_INDEX, notes)
        noteNames[i, harmonic - 1] = noteName

    return P1, f  # Return P1 and f

# 4. Multi-Pitch Analysis
numFrames = (len(y) - frameLength) // hopLength + 1

estimatedFrequencies = np.zeros((numFrames, numHarmonics))
confidenceScores = np.zeros((numFrames, numHarmonics))
noteNames = np.empty((numFrames, numHarmonics), dtype=object)  # Use object dtype for strings

with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = [executor.submit(process_frame, i, y, sr, frameLength, hopLength, numHarmonics, A4, A4_INDEX, notes, estimatedFrequencies, confidenceScores, noteNames) for i in range(numFrames)]

    # Wait for all tasks to complete
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Extract P1 and f from the last processed frame (they should be similar across frames)
P1, f = results[-1]

# 5. Tonic Estimation

# Weight each harmonic based on its relative spectral power
frequency_weights = np.mean(confidenceScores / np.sum(confidenceScores, axis=1, keepdims=True), axis=0)
weighted_frequencies = estimatedFrequencies * frequency_weights

# Histogram Analysis to find prominent peaks
hist, bin_edges = np.histogram(weighted_frequencies.flatten(), bins=50)  # Flatten array
peak_locations, _ = find_peaks(hist, distance=5)  # Adjust 'distance' as needed

# Convert peak locations to frequency values
peakFrequencies = bin_edges[peak_locations]

# If peak frequencies are empty, use the mean to estimate tonic
if len(peakFrequencies) == 0:
    tonicEstimate = np.mean(weighted_frequencies)
    print(f'No prominent peaks found. Using mean frequency: {tonicEstimate:.2f} Hz')
else:
    max_peak_index = np.argmax(hist[peak_locations])  # Use the histogram values to find the max peak
    tonicEstimate = peakFrequencies[max_peak_index]
    print(f'Prominent Peak found. Tonic Estimated from largest peak in distribution: {tonicEstimate:.2f} Hz')

# Find note name of tonic Estimate
tonicNoteName = frequencyToNote(tonicEstimate, A4, A4_INDEX, notes)
print(f"Estimated Tonic Note: {tonicNoteName}")

# 6. Visualization

# Time Axis
timeAxis = np.arange(numFrames) * hopLength / sr

# Create Figure
fig, axs = plt.subplots(3, 1, figsize=(10, 12))  # Adjust figure size for better spacing

# Subplot 1: Spectrogram
librosa.display.specshow(librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=frameLength, hop_length=hopLength)), ref=np.max),
                         sr=sr, hop_length=hopLength, x_axis='time', y_axis='log', ax=axs[0])  # Explicit ax=
axs[0].set_title('Spectrogram of the Audio')
axs[0].set_xlabel('Time (s)')  # Added x-axis label
axs[0].set_ylabel('Frequency (Hz)')  # Added y-axis label
fig.colorbar(axs[0].images[0], ax=axs[0], format='%+2.0f dB')

# Subplot 2: Multi-pitch over time
for harmonic in range(numHarmonics):
    axs[1].plot(timeAxis, estimatedFrequencies[:, harmonic], label=f'Harmonic {harmonic + 1}')  # Explicit ax=
axs[1].set_xlabel('Time (s)')
axs[1].set_ylabel('Frequency (Hz)')
axs[1].set_title('Estimated Frequencies over Time')
axs[1].legend()
axs[1].set_ylim([fmin, fmax * numHarmonics])

# Subplot 3: Histogram of Estimated Frequencies and Tonic
axs[2].hist(weighted_frequencies.flatten(), bins=bin_edges)  # Explicit ax= Use same bins
axs[2].axvline(tonicEstimate, color='r', linewidth=2, label=f'Tonic Estimate: {tonicEstimate:.2f} Hz ({tonicNoteName})')
axs[2].axvline(peakFrequencies, color='g', linewidth=1, label=f'Peaks from distribution: {peakFrequencies}', linestyle='--')
axs[2].set_xlabel('Frequency (Hz)')
axs[2].set_ylabel('Count')
axs[2].set_title('Histogram of Estimated Frequencies and Prominent Peaks')
axs[2].legend()

fig.suptitle('Multi-Pitch Analysis and Tonic Estimation')
fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent overlapping titles
plt.show()