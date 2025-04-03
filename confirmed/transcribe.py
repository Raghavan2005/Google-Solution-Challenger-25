#transc 2 cents
import librosa
import numpy as np
from collections import defaultdict

# **Step 1: Load Audio (First 30 Seconds)**
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with your song
y, sr = librosa.load(audio_path, sr=16000, duration=30)  # Trim to 30 seconds

# **Step 2: Extract Pitch Using YIN Algorithm**
pitches = librosa.yin(y, fmin=40, fmax=800, sr=sr, frame_length=1024, hop_length=256)

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
    if f > 0 and not np.isnan(f):
        note = hz_to_note_name(f)
        if note:
            note_frequencies[note].append(f)
            filtered_notes.append(note)

# **Step 5: Compute Average Frequency for Each Note**
average_frequencies = {note: np.mean(freqs) for note, freqs in note_frequencies.items()}

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

# Handle case when no stable note is found
if note_durations:
    most_stable_note = max(note_durations, key=lambda x: x[1])[0]
    shruti_freq = average_frequencies.get(most_stable_note, 208)  # Default to G#3 if missing
else:
    most_stable_note = "G#"
    shruti_freq = 208

print(f"\nMost Stable Note (Shruti): {most_stable_note}")

# **Step 7: Filter Pitches in the 196 Hz (G3) to 440 Hz (A4) Range**
valid_pitches = np.array([p if 196 <= p <= 440 else np.nan for p in pitches])

# **Step 8: carnatic Svara Ratios**
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

# **Step 9: Calculate Frequencies for Each Svara**
svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}

# **Step 10: Map Detected Pitches to Swaras**
def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    return min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))

mapped_swaras = [map_pitch_to_swara(p) for p in valid_pitches]
mapped_positions = [svara_positions[s] if s else np.nan for s in mapped_swaras]

# **Step 11: Print Mapped Swaras**
import textwrap

mapped_swaras_str = " ".join([s for s in mapped_swaras if s])
print("\nMapped Swaras:\n" + textwrap.fill(mapped_swaras_str, width=40))
