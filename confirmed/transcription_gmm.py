import librosa
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from sklearn.mixture import GaussianMixture

# **Step 1: Load Audio (First 30 Seconds)**
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with your song
y, sr = librosa.load(audio_path, sr=16000, duration=30)  # Trim to 30 seconds

pitches = librosa.yin(y, fmin=40, fmax=800, sr=sr, frame_length=1024, hop_length=256)
times = np.arange(len(pitches)) * (256 / sr)  # Compute time in seconds


# **Step 3: Apply GMM Filtering**
valid_pitches = pitches[~np.isnan(pitches)].reshape(-1, 1)  # Remove NaNs
gmm = GaussianMixture(n_components=3, covariance_type="full", random_state=42)
gmm.fit(valid_pitches)
filtered_pitches = gmm.predict(valid_pitches)
smoothed_pitches = gmm.means_[filtered_pitches].flatten()

# **Step 4: Convert Pitches to Octave-Independent Notes**
note_labels = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def hz_to_note_name(frequency):
    """Convert frequency (Hz) to octave-independent note name."""
    if frequency <= 0 or np.isnan(frequency):
        return None  
    note_number = round(12 * np.log2(frequency / 16.35)) % 12  
    return note_labels[note_number]

# **Step 5: Find the Most Stable Note (Shruti)**
note_frequencies = defaultdict(list)
for f in smoothed_pitches:
    note = hz_to_note_name(f)
    if note:
        note_frequencies[note].append(f)

average_frequencies = {note: np.mean(freqs) for note, freqs in note_frequencies.items()}
most_stable_note = max(average_frequencies, key=lambda n: len(note_frequencies[n]), default="G#")
shruti_freq = average_frequencies.get(most_stable_note, 208)  # Default to G#3 if missing

print(f"Most Stable Note (Shruti): {most_stable_note}")

# **Step 6: Define Hindustani Swaras**
svara_ratios = {
    "S": 1, "R1": 16/15, "R2": 9/8, "R3": 6/5, 
    "G1": 9/8, "G2": 6/5, "G3": 5/4, 
    "M1": 4/3, "M2": 17/12, 
    "P": 3/2, "D1": 8/5, "D2": 5/3, "D3": 9/5, 
    "N1": 5/3, "N2": 9/5, "N3": 15/8, "S'": 2
}

# **Step 7: Compute Swara Frequencies**
svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}

# **Step 8: Map Smoothed Pitches to Swaras**
def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    return min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))

mapped_swaras = [map_pitch_to_swara(p) for p in smoothed_pitches]
mapped_positions = [svara_positions[s] if s else np.nan for s in mapped_swaras]

# **Step 9: Plot Svara vs. Time**
plt.figure(figsize=(12, 6))
plt.scatter(times[:len(mapped_positions)], mapped_positions, c="b", s=5)
plt.yticks(range(len(svara_positions)), svara_positions.keys())
plt.xlabel("Time (s)")
plt.ylabel("Swaras")
plt.title("Filtered Swara Mapping (GMM Smoothed)")
plt.grid()
plt.show()
