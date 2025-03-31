import librosa
import numpy as np
import matplotlib.pyplot as plt

# **Step 1: Load Audio File**
audio_path = r"C:\Users\drivi\Downloads\kal.mp3"  # Replace with actual file path
y, sr = librosa.load(audio_path, sr=16000, duration=30)  # Load first 30 sec

# **Step 2: Extract Pitch Using YIN Algorithm**
pitches = librosa.yin(y, fmin=40, fmax=800, sr=sr, frame_length=2048, hop_length=512)

# **Step 3: Filter Pitches in the 196 Hz (G3) to 440 Hz (A4) Range**
valid_pitches = np.array([p if 196 <= p <= 440 else np.nan for p in pitches])

# **Step 4: Assume S = G# (Shruti is fixed)**
shruti_freq = 208  # Sa is G#3 (208 Hz)

# **Step 5: Define Frequency Ratios for Swaras**
svara_ratios = {
    "S": 1, "r1": 256/243, "r2": 16/15, "R1": 10/9, "R2": 9/8,
    "g1": 32/27, "g2": 6/5, "G1": 5/4, "G2": 81/64,
    "M1": 4/3, "M2": 27/20, "m1": 45/32, "m2": 729/512,
    "P": 3/2, "d1": 128/81, "d2": 8/5, "D1": 5/3, "D2": 27/16,
    "n1": 16/9, "n2": 9/5, "N1": 15/8, "N2": 243/128, "S'": 2
}

# **Step 6: Calculate Frequencies & Assign Fixed Positions**
svara_frequencies = {s: shruti_freq * r for s, r in svara_ratios.items()}

# Assign discrete Y-axis positions (avoid log scale issues)
svara_positions = {s: i for i, s in enumerate(svara_ratios.keys())}

# **Step 7: Convert Pitches to Time**
time = np.arange(len(valid_pitches)) * (512 / sr)

# **Step 8: Map Detected Pitches to Swaras**
def map_pitch_to_swara(frequency):
    if np.isnan(frequency) or frequency <= 0:
        return None
    closest_swara = min(svara_frequencies, key=lambda s: abs(svara_frequencies[s] - frequency))
    return closest_swara

# Convert detected pitches to swara labels
mapped_swaras = [map_pitch_to_swara(p) for p in valid_pitches]
mapped_positions = [svara_positions[s] if s else np.nan for s in mapped_swaras]

# **Step 9: Plot Graph**
plt.figure(figsize=(12, 6))

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
plt.title("Pitch vs Time with Fixed Swaras (Sa = G#)")
plt.grid(True)
plt.show()
