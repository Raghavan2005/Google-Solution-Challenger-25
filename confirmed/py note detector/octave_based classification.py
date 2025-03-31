import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display
from scipy.signal import find_peaks
from collections import Counter

# Load the audio file
audio_file = r"C:\Users\drivi\Downloads\kal.mp3"  # Change to your file path
y, sr = librosa.load(audio_file, sr=44100)

# Step 1: Compute Constant-Q Transform (CQT) Spectrogram
cqt = np.abs(librosa.cqt(y, sr=sr, hop_length=512, bins_per_octave=24, n_bins=192))
frequencies = librosa.cqt_frequencies(n_bins=192, fmin=21.8, bins_per_octave=24)

# Step 2: Detect the Most Stable Frequency (Sa)
stable_freqs = []
time_frames = []

for i in range(cqt.shape[1]):  # Iterate over time frames
    spectrum = cqt[:, i]  # Get frequency content at time step
    peak_indices, _ = find_peaks(spectrum, height=np.mean(spectrum) * 1.5)  # Detect strong frequencies
    detected_freqs = frequencies[peak_indices]
    
    if len(detected_freqs) > 0:
        stable_freqs.extend(detected_freqs)  # Store detected frequencies over time
        time_frames.extend([i] * len(detected_freqs))  # Store corresponding time frames

# Find the most frequent frequency (Sa) using mode
sa_freq = Counter(stable_freqs).most_common(1)[0][0]  # Most stable frequency

# Step 3: Generate Swara Frequencies Based on Detected Sa
swaras_ratios = [1, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8, 2]  # S, R, G, m, P, D, N, S'
swaras_labels = ["S", "R", "G", "m", "P", "D", "N", "S'"]
swaras_freqs = [sa_freq * ratio for ratio in swaras_ratios]

# Step 4: Map Each Detected Frequency to the Closest Swara
detected_notes = []
detected_times = []

for freq, time in zip(stable_freqs, time_frames):
    closest_swara = min(zip(swaras_freqs, swaras_labels), key=lambda x: abs(x[0] - freq))[1]  # Find closest note
    detected_notes.append(closest_swara)
    detected_times.append(librosa.frames_to_time(time, sr=sr, hop_length=512))  # Convert frame to time

# Step 5: Scatter Plot of Detected Notes Over Time
plt.figure(figsize=(12, 6))
plt.scatter(detected_times, detected_notes, color='red', s=10)  # Scatter plot with red dots
plt.xlabel("Time (s)")
plt.ylabel("Hindustani Swaras")
plt.title(f"Detected Swaras Over Time (Sa = {sa_freq:.2f} Hz)")
plt.grid(True)

plt.show()

# Print Detected Notes with Time Stamps
print(f"Detected Sa (S) Frequency: {sa_freq:.2f} Hz")
print("Detected Notes (Time in seconds):")
for time, note in zip(detected_times, detected_notes):
    print(f"{time:.2f}s -> {note}")
