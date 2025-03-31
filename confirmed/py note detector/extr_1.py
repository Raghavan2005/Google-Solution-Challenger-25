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
    if frequency <= 0:
        return None  # Ignore unvoiced frames
    note_number = round(12 * np.log2(frequency / 16.35)) % 12  # 16.35 Hz = C0
    return note_labels[note_number]

# **Step 4: Collect Frequencies for Each Note**
note_frequencies = defaultdict(list)
filtered_notes = []

for f in pitches:
    if f > 0:
        note = hz_to_note_name(f)
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

# Find the most stable note (longest duration)
most_stable_note = max(note_durations, key=lambda x: x[1])[0]

# **Step 7: Plot Pitch vs Time Graph**
time = np.arange(len(pitches)) * (512 / sr)  # Convert frames to time in seconds
note_map = {note: i for i, note in enumerate(note_labels)}  # Map notes to Y-axis values
note_indices = [note_map[note] for note in filtered_notes if note]  # Convert notes to numerical values

plt.figure(figsize=(10, 4))
for i, (t, note) in enumerate(zip(time[:len(note_indices)], filtered_notes)):
    color = 'r' if note == most_stable_note else 'b'  # Red for most stable note, Blue for others
    plt.scatter(t, note_map[note], color=color, s=5)

plt.xlabel("Time (s)")
plt.ylabel("Pitch (Octave-Independent)")
plt.title("Pitch vs Time Graph for 30 Seconds")
plt.yticks(range(len(note_labels)), note_labels)  # Set y-axis to note names
plt.legend(["Detected Pitch", f"Most Stable Note ({most_stable_note})"], loc="upper right")
plt.grid(True)
plt.show()

# **Step 8: Print Average Frequency for Each Note**
print("\nAverage Frequency for Each Detected Note:")
for note, avg_freq in sorted(average_frequencies.items()):
    print(f"Note: {note}, Average Frequency: {avg_freq:.2f} Hz")

# Print the most stable note
print(f"\nMost Stable Note (Shruti): {most_stable_note}")
