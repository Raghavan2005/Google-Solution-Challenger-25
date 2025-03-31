% MATLAB script for multi-pitch analysis and tonic estimation with note mapping

% 1. Load Audio File
audioFilePath = 'kal.mp3';  % Replace with the actual path
[y, sr] = audioread(audioFilePath);           % y: audio data, sr: sampling rate
y = y(:, 1);   % mono version if audio is stereo

% 2. Parameters
frameLength = 2048;   % Length of each analysis frame (samples)
hopLength   = 512;    % Hop size between frames (samples)
fmin = 50;  % Minimum frequency to consider (Hz) - adjust as needed
fmax = 800; % Maximum frequency to consider (Hz) - adjust as needed
numHarmonics = 5; % Number of harmonics to consider for multi-pitch detection

% 3. Note Mapping Parameters (A4 = 440Hz)
A4 = 440.0;
A4_INDEX = 57;
notes = {
    "C0","C#0","D0","D#0","E0","F0","F#0","G0","G#0","A0","A#0","B0",
    "C1","C#1","D1","D#1","E1","F1","F#1","G1","G#1","A1","A#1","B1",
    "C2","C#2","D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2",
    "C3","C#3","D3","D#3","E3","F3","F#3","G3","G#3","A3","A#3","B3",
    "C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","A#4","B4",
    "C5","C#5","D5","D#5","E5","F5","F#5","G5","G#5","A5","A#5","B5",
    "C6","C#6","D6","D#6","E6","F6","F#6","G6","G#6","A6","A#6","B6",
    "C7","C#7","D7","D#7","E7","F7","F#7","G7","G#7","A7","A#7","B7",
    "C8","C#8","D8","D#8","E8","F8","F#8","G8","G#8","A8","A#8","B8",
    "C9","C#9","D9","D#9","E9","F9","F#9","G9","G#9","A9","A#9","B9"
    };

% 4. Multi-Pitch Analysis
numFrames = floor((length(y) - frameLength) / hopLength) + 1; % Number of frames

estimatedFrequencies = zeros(numFrames, numHarmonics); %Store estimated frequencies of harmonics
confidenceScores = zeros(numFrames,numHarmonics);      %Store confidence of each harmonic
noteNames = strings(numFrames, numHarmonics);   % Store estimated note names

for i = 1:numFrames

    startIndex = (i - 1) * hopLength + 1;
    endIndex   = startIndex + frameLength - 1;
    frame      = y(startIndex:endIndex);

    % Windowing (e.g., Hanning window)
    window = hann(frameLength);
    frame  = frame .* window;

    % Compute the Spectrum (FFT)
    N = length(frame);
    fft_frame = fft(frame, N);
    P2 = abs(fft_frame/N);
    P1 = P2(1:N/2+1);
    P1(2:end-1) = 2*P1(2:end-1);
    f = sr*(0:(N/2))/N;  % frequency axis

    % Harmonic Product Spectrum (HPS) inspired
    hps_spectrum = P1;
    for h = 2:numHarmonics
        downsampled_indices = 1:h:length(P1);  % downsample indices
        if (length(downsampled_indices) > length(hps_spectrum))
            downsampled_indices = downsampled_indices(1:length(hps_spectrum));
        elseif (length(downsampled_indices) < length(hps_spectrum))
            hps_spectrum = hps_spectrum(1:length(downsampled_indices));
        end

        hps_spectrum = hps_spectrum .* P1(downsampled_indices);
    end

    % Estimate the Fundamental Frequency (F0)
    [peak_value, peak_index] = max(hps_spectrum);
    estimatedF0 = f(peak_index);  % in Hz

    % Store the estimated frequencies and their confidence scores
    for harmonic = 1:numHarmonics
        harmonicFrequency = estimatedF0 * harmonic;
        [~, harmonicIndex] = min(abs(f - harmonicFrequency)); % Find the nearest frequency bin

        estimatedFrequency = f(harmonicIndex);
        estimatedFrequencies(i, harmonic) = estimatedFrequency;
        confidenceScores(i, harmonic) = P1(harmonicIndex); % using spectral magnitude as confidence

        % Map to Note
        noteName = frequencyToNote(estimatedFrequency, A4, A4_INDEX, notes);
        noteNames(i, harmonic) = noteName;
    end
end


% 5. Tonic Estimation
%   - Average across all frames and harmonics

% Weight each harmonic based on its relative spectral power

frequency_weights = mean(confidenceScores ./ sum(confidenceScores, 2), 1);  % Normalize the power for each frame so that total is 1, then take the mean across all frames for each Harmonic
weighted_frequencies = estimatedFrequencies .* frequency_weights;

% Histogram Analysis to find prominent peaks
[N,edges] = histcounts(weighted_frequencies(:), 50);
[peaks,peakLocations] = findpeaks(N, 'MinPeakDistance', 5); % Adjust 'MinPeakDistance' as needed

% Convert peak locations to frequency values
peakFrequencies = edges(peakLocations);

%If peak frequencies are empty, use the mean to estimate tonic
if isempty(peakFrequencies)
   tonicEstimate = mean(weighted_frequencies(:));
   fprintf('No prominent peaks found. Using mean frequency: %.2f Hz\n', tonicEstimate);
else
   [~, maxPeakIndex] = max(peaks);
   tonicEstimate = peakFrequencies(maxPeakIndex);  % Find the frequency with the most prominent peak
   fprintf('Prominent Peak found. Tonic Estimated from largest peak in distribution : %.2f Hz\n', tonicEstimate);

end

% Find note name of tonic Estimate
tonicNoteName = frequencyToNote(tonicEstimate, A4, A4_INDEX, notes);
fprintf("Estimated Tonic Note: %s\n", tonicNoteName);



% 6. Visualization

%Time Axis
timeAxis = (0:numFrames-1) * hopLength / sr;


figure;

% Subplot 1: Spectrogram
subplot(3, 1, 1);
spectrogram(y, hamming(frameLength), hopLength, frameLength, sr, 'yaxis');
title('Spectrogram of the Audio');
colorbar;

% Subplot 2: Multi-pitch over time
subplot(3, 1, 2);
hold on;
for harmonic = 1:numHarmonics
    plot(timeAxis, estimatedFrequencies(:, harmonic), 'DisplayName', sprintf('Harmonic %d', harmonic));
end
hold off;
xlabel('Time (s)');
ylabel('Frequency (Hz)');
title('Estimated Frequencies over Time');
legend show;
ylim([fmin, fmax*numHarmonics]);

% Subplot 3: Histogram of Estimated Frequencies and Tonic
subplot(3, 1, 3);
histogram(weighted_frequencies(:), edges); %Use the edges to make both histograms consistent.
hold on;
xline(tonicEstimate, 'r', 'LineWidth', 2, 'DisplayName', sprintf('Tonic Estimate: %.2f Hz (%s)', tonicEstimate, tonicNoteName));
xline(peakFrequencies, 'g', 'LineWidth', 1, 'DisplayName', sprintf('Peaks from distribution: %.2f Hz', peakFrequencies));
hold off;
xlabel('Frequency (Hz)');
ylabel('Count');
title('Histogram of Estimated Frequencies and Prominent Peaks');
legend show;

sgtitle('Multi-Pitch Analysis and Tonic Estimation');



