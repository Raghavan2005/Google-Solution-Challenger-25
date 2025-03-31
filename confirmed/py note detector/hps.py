import librosa
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from scipy.signal import find_peaks
import matplotlib.colors as mcolors

# Load Audio (First 30 Seconds)
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with your song
y, sr = librosa.load(audio_path, sr=16000, duration=10)

# Pole Focusing Technique
def pole_focusing_spectrum(y, sr, r=0.99):
    n = len(y)
    # Create the z-plane points
    z = r * np.exp(1j * 2 * np.pi * np.fft.fftfreq(n, 1/sr))
    # Compute the Z-transform for all frequencies
    z_transform = np.array([np.sum(y * (z ** (-k))) for k in range(n)])
    return np.abs(z_transform)

# Harmonic Product Spectrum (HPS) with Pole Focusing
def harmonic_product_spectrum_with_pole_focusing(y, sr, num_harmonics=5, r=0.99):
    spectrum = pole_focusing_spectrum(y, sr, r)  # Apply pole focusing
    hps_spectrum = np.copy(spectrum)

    for h in range(2, num_harmonics + 1):
        downsampled = spectrum[::h]  # Downsampled spectrum
        length = len(downsampled)  # Get correct length
        hps_spectrum[:length] *= downsampled  # Truncate before multiplication

    fundamental_idx = np.argmax(hps_spectrum)  # Find peak index
    fundamental_freq = fundamental_idx * sr / len(spectrum)  # Convert index to frequency
    return fundamental_freq

# Extract pitch and time using HPS with Pole Focusing
def hps_pole_focusing_pitch_detection(signal, sr, frame_length=1024, hop_length=256, r=0.99):
    pitches = []
    times = []
    for i in range(0, len(signal) - frame_length, hop_length):
        frame = signal[i:i + frame_length]
        frame -= np.mean(frame)
        frame *= np.hanning(len(frame))
        pitch = harmonic_product_spectrum_with_pole_focusing(frame, sr, r=r)
        pitches.append(pitch)
        times.append(i / sr)  # Time in seconds
    return np.array(pitches), np.array(times)

# Extract pitch and time
pitches, times = hps_pole_focusing_pitch_detection(y, sr)
filtered_pitches = pitches[~np.isnan(pitches)]
shruti_freq = np.median(filtered_pitches) if len(filtered_pitches) > 0 else 208  # Use median as tonic

# Define Hindustani Notes (Only S, R, G, M, P, D, N, S')
svara_ratios = {
    "S": 1, "R": 9/8, "G": 5/4, "M": 4/3,
    "P": 3/2, "D": 5/3, "N": 15/8, "S'": 2
}

svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}  # Assign Y-axis values

# Function to map pitch to swara, accounting for octave (S vs S')
def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    # Check if the frequency is approximately double the tonic (S')
    if abs(frequency - 2 * svara_frequencies["S"]) < abs(frequency - svara_frequencies["S"]):
        return "S'"
    # Otherwise, find the closest note
    return min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))

# Apply GMM for Clustering (8 clusters for 8 notes)
valid_pitches = filtered_pitches.reshape(-1, 1)
gmm = GaussianMixture(n_components=8, random_state=42)
gmm.fit(valid_pitches)
cluster_labels = gmm.predict(valid_pitches)
cluster_means = gmm.means_.flatten()

# Convert clustered pitches to swaras
cluster_to_swara = {}  # Map cluster IDs to actual notes
for i, freq in enumerate(sorted(cluster_means)):
    cluster_to_swara[i] = list(svara_ratios.keys())[i]  # Assign closest note in order

clustered_swaras = [cluster_to_swara[label] for label in cluster_labels]

# Function to print detected notes 7 per line
def print_notes_7_per_line(notes):
    for i in range(0, len(notes), 7):
        print(" ".join(notes[i:i+7]))

# Print detected notes
print("Detected Notes (7 per line):")
print_notes_7_per_line(clustered_swaras)

# Define fixed colors for each note
svara_colors = {
    "S": "red", "R": "blue", "G": "green", "M": "orange",
    "P": "purple", "D": "brown", "N": "pink", "S'": "red"
}

# Create a colormap for clusters
cmap = mcolors.ListedColormap([svara_colors[note] for note in cluster_to_swara.values()])
bounds = list(range(len(cluster_to_swara) + 1))
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Plot Hindustani Notes Over Time
plt.figure(figsize=(12, 6))
scatter = plt.scatter(times[:len(clustered_swaras)], [svara_positions[s] for s in clustered_swaras], c=cluster_labels, cmap=cmap, label="Notes")
plt.xlabel("Time (s)")
plt.ylabel("Hindustani Notes")
plt.yticks(range(len(svara_ratios)), list(svara_ratios.keys()))  # Set Y-axis to swaras
plt.title("GMM Clustered Notes Over Time (Mapped to Hindustani Scale)")

# Add a colorbar with note labels
cb = plt.colorbar(scatter, ticks=bounds[:-1])
cb.set_ticklabels([cluster_to_swara[i] for i in range(len(cluster_to_swara))])
cb.set_label("Hindustani Notes")

plt.legend()
plt.show()