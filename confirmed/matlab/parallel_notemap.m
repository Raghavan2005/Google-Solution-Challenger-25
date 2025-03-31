% MATLAB script for multi-pitch analysis and tonic estimation with note mapping, GPU accelerated and multithreaded
% with tonic estimation on GPU and corrected for parfor/spmd

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

% 3. Note Mapping Parameters (initial A4 assumption)
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

% 4. Multi-Pitch Analysis - GPU Accelerated and Parallelized
numFrames = floor((length(y) - frameLength) / hopLength) + 1; % Number of frames

estimatedFrequencies = zeros(numFrames, numHarmonics, 'gpuArray'); %Store estimated frequencies of harmonics
confidenceScores = zeros(numFrames,numHarmonics, 'gpuArray');      %Store confidence of each harmonic
noteIndices = zeros(numFrames, numHarmonics, 'gpuArray');  %Store note index directly to convert back to cell strings later

% Prepare data for GPU
y_gpu = gpuArray(y);
window = gpuArray(hann(frameLength));
f = gpuArray(sr*(0:(frameLength/2))/frameLength);  % frequency axis
numNotes = length(notes); %store to prevent multiple calls

spmd % Start parallel pool for data parallelism
    local_estimatedFrequencies = zeros(numFrames, numHarmonics, 'gpuArray');
    local_confidenceScores = zeros(numFrames, numHarmonics, 'gpuArray');
    local_noteIndices = zeros(numFrames, numHarmonics, 'gpuArray');

    for i = labindex:numlabs:numFrames % Distribute frames across labs

        startIndex = (i - 1) * hopLength + 1;
        endIndex   = startIndex + frameLength - 1;
        frame      = y_gpu(startIndex:endIndex);

        % Windowing
        frame  = frame .* window;

        % Compute the Spectrum (FFT)
        N = length(frame);
        fft_frame = fft(frame, N);
        P2 = abs(fft_frame/N);
        P1 = P2(1:N/2+1);
        P1(2:end-1) = 2*P1(2:end-1);

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


        % Prepare inputs for arrayfun
        harmonic_indices = gpuArray((1:numHarmonics)); % Harmonic indices on the GPU

        %Task Parallelism using arrayfun and a GPU function
        [local_estimatedFrequencies(i,:), local_confidenceScores(i,:), local_noteIndices(i,:)] = ...
            analyzeHarmonics(estimatedF0, f, P1, A4, A4_INDEX, numNotes, harmonic_indices);


    end

    estimatedFrequencies = local_estimatedFrequencies;
    confidenceScores = local_confidenceScores;
    noteIndices = local_noteIndices;
end

estimatedFrequencies = gather(estimatedFrequencies);
confidenceScores = gather(confidenceScores);
noteIndices = gather(noteIndices);


noteNames = cell(numFrames, numHarmonics);
for i = 1:numFrames
    for h = 1:numHarmonics
        noteIndex = noteIndices(i,h);
        if(noteIndex >= 1 && noteIndex <= length(notes))
            noteNames{i,h} = notes{noteIndex};
        else
            noteNames{i,h} = "N/A";
        end
    end
end

noteNames = string(noteNames);



% 5. Tonic Estimation (GPU Accelerated)
frequency_weights = mean(confidenceScores ./ sum(confidenceScores, 2), 1);  % Normalize the power for each frame so that total is 1, then take the mean across all frames for each Harmonic
weighted_frequencies = estimatedFrequencies .* frequency_weights;

% Histogram Analysis to find prominent peaks (on GPU)
numBins = 50;

[N,edges] = histcounts(weighted_frequencies(:), numBins); % Generate histcounts on CPU since no gpu version exist

%Move to gpu
N = gpuArray(N);
edges = gpuArray(edges);

%Find peaks (GPU)
minPeakDistance = 5;
[peaks,peakLocations] = findpeaks_gpu(N, minPeakDistance); % Custom GPU peak finding

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

tonicEstimate = gather(tonicEstimate); % get value back from GPU
peakFrequencies = gather(peakFrequencies);

% Find note name of tonic Estimate
tonicNoteName = frequencyToNote(tonicEstimate, A4, A4_INDEX, notes);

%Redefine A4 based on tonic estimation.
A4 = tonicEstimate;
A4_INDEX = frequencyToNoteIndex(A4,A4, A4_INDEX, numNotes);

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
histogram(gather(weighted_frequencies(:)), gather(edges)); %Use the edges to make both histograms consistent.
hold on;
xline(tonicEstimate, 'r', 'LineWidth', 2, 'DisplayName', sprintf('Tonic Estimate: %.2f Hz (%s)', tonicEstimate, tonicNoteName));
xline(peakFrequencies, 'g', 'LineWidth', 1, 'DisplayName', sprintf('Peaks from distribution: %.2f Hz', peakFrequencies));
hold off;
xlabel('Frequency (Hz)');
ylabel('Count');
title('Histogram of Estimated Frequencies and Prominent Peaks');
legend show;

sgtitle('Multi-Pitch Analysis and Tonic Estimation');

