import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# **Step 1: Load Audio (First 30 Seconds)**
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with your song
y, sr = librosa.load(audio_path, sr=16000, duration=30)  # Trim to 30 seconds

# **Step 2: Extract Pitch Using YIN Algorithm**
pitches = librosa.yin(y, fmin=40, fmax=800, sr=sr, frame_length=2048, hop_length=512)

# **Step 3: Convert Pitches to Octave-Independent Notes**
note_labels = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def hz_to_note_name(frequency):
    """Convert frequency (Hz) to octave-independent note name."""
    if frequency <= 0 or np.isnan(frequency):
        return None  # Ignore unvoiced frames
    note_number = round(12 * np.log2(frequency / 16.35)) % 12  # 16.35 Hz = C0
    return note_labels[note_number]

# **Step 4: Collect Frequencies for Each Note**
note_frequencies = defaultdict(list)
filtered_notes = []

for f in pitches:
    if f > 0:
        note = hz_to_note_name(f)
        if note is not None:
            note_frequencies[note].append(f)
            filtered_notes.append(note)

# **Step 5: Compute Average Frequency for Each Note**
average_frequencies = {note: sum(freqs) / len(freqs) for note, freqs in note_frequencies.items() if freqs}

# **Step 6: Identify the Most Stable Note (Longest Continuous Pitch)**
note_durations = []
current_note = None
current_length = 0

for note in filtered_notes:
    if note == current_note:
        current_length += 1
    else:
        if current_note:
            note_durations.append((current_note, current_length))
        current_note = note
        current_length = 1

# Append last counted note
if current_note:
    note_durations.append((current_note, current_length))

# Handle empty note_durations case
if note_durations:
    most_stable_note = max(note_durations, key=lambda x: x[1])[0]
    shruti_freq = average_frequencies.get(most_stable_note, 208)  # Default to G#3 = 208 Hz if missing
else:
    most_stable_note = "G#"  # Default stable note
    shruti_freq = 208  # Default frequency for Sa

# Print the most stable note
print(f"\nMost Stable Note (Shruti): {most_stable_note}")

# **Step 7: Filter Pitches in the 196 Hz (G3) to 440 Hz (A4) Range**
valid_pitches = np.array([p if 196 <= p <= 440 else np.nan for p in pitches])

# **hindusthani this**
"""svara_ratios = {
    "S": 1, "r1": 256/243, "r2": 16/15, "R1": 10/9, "R2": 9/8,
    "g1": 32/27, "g2": 6/5, "G1": 5/4, "G2": 81/64,
    "M1": 4/3, "M2": 27/20, "m1": 45/32, "m2": 729/512,
    "P": 3/2, "d1": 128/81, "d2": 8/5, "D1": 5/3, "D2": 27/16,
    "n1": 16/9, "n2": 9/5, "N1": 15/8, "N2": 243/128, "S'": 2
}"""
svara_ratios = {
    "S": 1, 
    "R1": 16/15, "R2": 9/8, "R3": 6/5, 
    "G1": 9/8, "G2": 6/5, "G3": 5/4, 
    "M1": 4/3, "M2": 17/12, 
    "P": 3/2, 
    "D1": 8/5, "D2": 5/3, "D3": 9/5, 
    "N1": 5/3, "N2": 9/5, "N3": 15/8, 
    "S'": 2
}



# **Step 9: Calculate Frequencies & Assign Fixed Positions**
svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}

# Assign discrete Y-axis positions (avoid log scale issues)
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}

# **Step 10: Convert Pitches to Time**
time = np.arange(len(valid_pitches)) * (512 / sr)

# **Step 11: Map Detected Pitches to Swaras**
def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    closest_swara = min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))
    return closest_swara

# Convert detected pitches to swara labels
mapped_swaras = [map_pitch_to_swara(p) for p in valid_pitches]
mapped_positions = [svara_positions[s] if s else np.nan for s in mapped_swaras]

# **Step 12: Plot Graph**
plt.figure(figsize=(12, 8))

# 🎼 **Plot Swara Grid (Fixed Positions)**
for svara, pos in svara_positions.items():
    plt.axhline(y=pos, color='gray', linestyle='--', linewidth=0.7)
    plt.text(-0.5, pos, svara, verticalalignment='center', fontsize=10, color='black')

# 🎤 **Plot Detected Pitch as Swaras (Red dots)**
plt.scatter(time, mapped_positions, color='red', s=5, alpha=0.5)

# **Set Y-axis labels to Swara names**
plt.yticks(list(svara_positions.values()), list(svara_positions.keys()))

plt.xlabel("Time (s)")
plt.ylabel("Indian Swaras")
plt.title(f"Pitch vs Time with Fixed Swaras (Sa = {most_stable_note})")
plt.grid(True)
plt.show()
