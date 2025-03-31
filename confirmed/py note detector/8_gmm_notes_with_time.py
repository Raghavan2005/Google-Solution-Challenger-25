import librosa
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from scipy.signal import find_peaks
import matplotlib.colors as mcolors

# Load Audio (First 30 Seconds)
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with your song
y, sr = librosa.load(audio_path, sr=16000, duration=30)

# Autocorrelation-Based Pitch Detection
def autocorrelation_pitch_detection(signal, sr, frame_length=1024, hop_length=256):
    pitches = []
    times = []
    for i in range(0, len(signal) - frame_length, hop_length):
        frame = signal[i:i + frame_length]
        frame -= np.mean(frame)
        frame *= np.hanning(len(frame))
        autocorr = np.correlate(frame, frame, mode='full')[len(frame) - 1:]
        autocorr /= np.max(autocorr)
        peaks, _ = find_peaks(autocorr, height=0.5)
        if len(peaks) > 0:
            lag = peaks[0]
            pitch = sr / lag
            pitches.append(pitch)
        else:
            pitches.append(np.nan)
        times.append(i / sr)  # Time in seconds
    return np.array(pitches), np.array(times)

# Extract pitch and time
pitches, times = autocorrelation_pitch_detection(y, sr)
filtered_pitches = pitches[~np.isnan(pitches)]
shruti_freq = np.median(filtered_pitches) if len(filtered_pitches) > 0 else 208  # Stable frequency as base note

# Define Hindustani Notes
svara_ratios = {
    "S": 1, "R": 9/8, "G": 5/4, "M": 4/3,
    "P": 3/2, "D": 5/3, "N": 15/8, "S'": 2
}

svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}  # Assign Y-axis values

def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    return min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))

# Apply GMM for Clustering (8 clusters for 8 notes)
valid_pitches = filtered_pitches.reshape(-1, 1)
gmm = GaussianMixture(n_components=8, random_state=42)
gmm.fit(valid_pitches)
cluster_labels = gmm.predict(valid_pitches)
cluster_means = gmm.means_.flatten()

# Convert clustered pitches to swaras
cluster_to_swara = {i: list(svara_ratios.keys())[i] for i in range(len(cluster_means))}
clustered_swaras = [cluster_to_swara[label] for label in cluster_labels]
mapped_positions = [svara_positions[s] for s in clustered_swaras]

# Normalize time for color mapping (0 to 1)
time_min, time_max = times.min(), times.max()
norm_times = (times - time_min) / (time_max - time_min)  # Normalized time (0 to 1)

# Use Reds colormap, where early notes are bright red and later ones are duller
cmap = plt.get_cmap("Reds")
colors = cmap(1 - norm_times[:len(mapped_positions)])  # Flip so earliest is brightest

# Plot Hindustani Notes Over Time
plt.figure(figsize=(12, 6))
scatter = plt.scatter(times[:len(mapped_positions)], mapped_positions, c=colors, label="Notes")
plt.xlabel("Time (s)")
plt.ylabel("Hindustani Notes")
plt.yticks(range(len(svara_ratios)), list(svara_ratios.keys()))
plt.title("Notes Over Time with Time-Based Color Mapping")

plt.legend()
plt.show()
