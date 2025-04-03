import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display

# Load first 15 seconds of audio
audio_file = r"C:\Users\drivi\Downloads\kal.mp3"  # Change this to your actual file path
y, sr = librosa.load(audio_file, sr=44100, duration=15)

# Step 1: Compute Constant-Q Transform (CQT) with correct range
sa4_freq = 280  # Set Sa4 as 280 Hz
cqt = np.abs(librosa.cqt(y, sr=sr, hop_length=512, bins_per_octave=12, n_bins=24, fmin=sa4_freq))  # 2 octaves

# Define Hindustani swaras based on Sa4 = 280 Hz
swaras_ratios = [1, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8, 2]  # S, R, G, m, P, D, N, S'
swaras_labels = ["S", "R", "G", "m", "P", "D", "N", "S'"]

# Generate **frequency list** for exactly **S4 and S5**
octaves = [4, 5]  # Display S4 and S5
swaras_freqs = []
swaras_names = []

for octave in octaves:
    for i, ratio in enumerate(swaras_ratios):
        freq = sa4_freq * (2 ** (octave - 4)) * ratio  # Shift octaves correctly
        swaras_freqs.append(freq)
        swaras_names.append(swaras_labels[i] + str(octave))  # Append octave number

# Convert swaras to logarithmic scale (to match CQT scale)
swaras_log = np.log2(swaras_freqs)

# Get CQT frequencies for reference
freqs = librosa.cqt_frequencies(n_bins=24, fmin=sa4_freq, bins_per_octave=12)
freqs_log = np.log2(freqs)

# Step 2: Plot CQT Spectrogram with Hindustani Swaras (S4 and S5)
plt.figure(figsize=(12, 6))  # Bigger figure for better Y-axis visibility
librosa.display.specshow(librosa.amplitude_to_db(cqt, ref=np.max), sr=sr, hop_length=512, x_axis="time", y_axis="cqt_hz")

# 🔥 **Replace Y-axis with Hindustani Swaras (S4, S5)**
plt.yticks(swaras_log, swaras_names)
plt.ylim(swaras_log[0], swaras_log[-1])  # Limit to just S4-S5 range
plt.xlabel("Time (s)")
plt.ylabel("Hindustani Swaras (S4 & S5)")
plt.title("CQT Spectrogram with Hindustani Swaras (S4, S5)")
plt.colorbar(label="Amplitude (dB)")
plt.show()
