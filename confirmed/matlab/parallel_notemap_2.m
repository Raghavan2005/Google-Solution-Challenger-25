% MATLAB/Octave script for multi-pitch analysis and tonic estimation with note mapping, attempting GPU acceleration and multithreading

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
numWorkers = 4; % or however many cores you wish to use

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

% ----------------------- Helper Functions --------------------------
% Helper function to convert a note to its index

function noteIndex = frequencyToNoteIndex(inputFrequency, A4, A4_INDEX,numNotes)
        MINUS = 0;
        PLUS = 1;

        frequency = A4;
        r = 2^(1/12);  % Semitone ratio
        cent = 2^(1/1200); % Cent ratio

        r_index = 0;
        cent_index = 0;
        side = 0;

        if inputFrequency >= frequency
            while inputFrequency >= r * frequency
                frequency = r * frequency;
                r_index = r_index + 1;
            end
            while inputFrequency > cent * frequency
                frequency = cent * frequency;
                cent_index = cent_index + 1;
            end

            if (cent * frequency - inputFrequency) < (inputFrequency - frequency)
                cent_index = cent_index + 1;
            end

            if cent_index > 50
                r_index = r_index + 1;
                cent_index = 100 - cent_index;
                if cent_index ~= 0
                    side = MINUS;
                else
                    side = PLUS;
                end
            else
                side = PLUS;
            end
        else
            while inputFrequency <= frequency / r
                frequency = frequency / r;
                r_index = r_index - 1;
            end
            while inputFrequency < frequency / cent
                frequency = frequency / cent;
                cent_index = cent_index + 1;
            end

            if (inputFrequency - frequency/cent) < (frequency - inputFrequency)
                cent_index = cent_index + 1;
            end

            if cent_index >= 50
                r_index = r_index - 1;
                cent_index = 100 - cent_index;
                side = PLUS;
            else
                if cent_index ~= 0
                    side = MINUS;
                else
                    side = PLUS;
                end
            end
        end
         noteIndex = A4_INDEX + r_index;

            % Check index bounds (IMPORTANT: Prevent errors)
            if noteIndex < 1
                noteIndex = 1;
            elseif noteIndex > numNotes
                noteIndex = numNotes;
            end
        end

%Corrected Analyze Harmonics
function [estimatedFrequencies, confidenceScores, noteIndices] = analyzeHarmonics(estimatedF0, f, P1, A4, A4_INDEX, numNotes, harmonic_indices)

    harmonicFrequencies = estimatedF0 .* harmonic_indices;
    harmonicIndices=zeros(size(harmonicFrequencies));
    for i =1:length(harmonicFrequencies)
        [~, harmonicIndices(i)] = min(abs(f - harmonicFrequencies(i)));
    end

    estimatedFrequencies = f(harmonicIndices);
    confidenceScores = P1(harmonicIndices);
     noteIndices = zeros(size(estimatedFrequencies));
        for i =1:length(estimatedFrequencies)
             noteIndices(i) = frequencyToNoteIndex(estimatedFrequencies(i), A4, A4_INDEX,numNotes);
        end

end

%Helper function to enforce minimum peak distance
function [peakCandidateIdx, prunedIdx] = enforceMinPeakDistance(peakCandidateIdx, data, minPeakDistance)
    prunedIdx = [];
    if ~isempty(peakCandidateIdx)
        % Sort peak candidates by amplitude
        [~, sortIdx] = sort(data(peakCandidateIdx), 'descend');
        peakCandidateIdx = peakCandidateIdx(sortIdx);

        % Initialize a flag to keep track of valid peaks
        isValid = true(size(peakCandidateIdx));

        for i = 1:numel(peakCandidateIdx)
            if isValid(i)
                currentIdx = peakCandidateIdx(i);
                % Find indices within the minimum peak distance
                withinDist = abs(peakCandidateIdx - currentIdx) <= minPeakDistance;
                % Mark all indices within the distance as invalid
                isValid(withinDist) = false;
                % Keep the current index as valid
                isValid(i) = true;
            end
        end

        % Return only the valid peak candidate indices
        peakCandidateIdx = peakCandidateIdx(isValid);
    end
end
% Helper function: frequencyToNote
function noteName = frequencyToNote(inputFrequency, A4, A4_INDEX, notes)
    %Converts a frequency to the nearest note name

    MINUS = 0;
    PLUS = 1;

    frequency = A4;
    r = 2^(1/12);  % Semitone ratio
    cent = 2^(1/1200); % Cent ratio

    r_index = 0;
    cent_index = 0;
    side = 0;

    if inputFrequency >= frequency
        while inputFrequency >= r * frequency
            frequency = r * frequency;
            r_index = r_index + 1;
        end
        while inputFrequency > cent * frequency
            frequency = cent * frequency;
            cent_index = cent_index + 1;
        end

        if (cent * frequency - inputFrequency) < (inputFrequency - frequency)
            cent_index = cent_index + 1;
        end

        if cent_index > 50
            r_index = r_index + 1;
            cent_index = 100 - cent_index;
            if cent_index ~= 0
                side = MINUS;
            else
                side = PLUS;
            end
        else
            side = PLUS;
        end
    else
        while inputFrequency <= frequency / r
            frequency = frequency / r;
            r_index = r_index - 1;
        end
        while inputFrequency < frequency / cent
            frequency = frequency / cent;
            cent_index = cent_index + 1;
        end

        if (inputFrequency - frequency/cent) < (frequency - inputFrequency)
            cent_index = cent_index + 1;
        end

        if cent_index >= 50
            r_index = r_index - 1;
            cent_index = 100 - cent_index;
            side = PLUS;
        else
            if cent_index ~= 0
                side = MINUS;
            else
                side = PLUS;
            end
        end
    end

    % Get the note
    noteIndex = A4_INDEX + r_index;

    % Check index bounds (IMPORTANT: Prevent errors)
    if noteIndex < 1
        noteIndex = 1;
    elseif noteIndex > length(notes)
        noteIndex = length(notes);
    end

    result = notes{noteIndex}; % Use curly braces for cell array indexing

    % Append cents value
    if side == PLUS
        result = result + " + " + cent_index + " cents";
    else
        result = result + " - " + cent_index + " cents";
    end
    noteName = result;

end
function [peaks, peakLocations] = findpeaks_gpu(data, minPeakDistance)
    %findpeaks_gpu - Octave-compatible peak finding function (no GPU used)

    % Ensure data is a column vector
    data = data(:);

    % Compute the differences between adjacent elements
    diffData = diff(data);

    % Find indices where the difference changes sign from positive to negative
    peakCandidateIdx = find(diffData(1:end-1) > 0 & diffData(2:end) <= 0) + 1;

    % If no candidates are found, return empty arrays
    if isempty(peakCandidateIdx)
        peaks = zeros(0, 1);
        peakLocations = zeros(0, 1);
        return;
    end

    % Enforce minimum peak distance
    if ~isempty(peakCandidateIdx) && minPeakDistance > 1
        [peakCandidateIdx, ~] = enforceMinPeakDistance(peakCandidateIdx, data, minPeakDistance);
    end

    % Extract peak values and locations
    peakLocations = peakCandidateIdx;
    peaks = data(peakLocations);

end

% 4. Multi-Pitch Analysis
numFrames = floor((length(y) - frameLength) / hopLength) + 1; % Number of frames

estimatedFrequencies = zeros(numFrames, numHarmonics); %Store estimated frequencies of harmonics
confidenceScores = zeros(numFrames,numHarmonics);      %Store confidence of each harmonic
noteIndices = zeros(numFrames, numHarmonics);   % Store estimated note index directly to convert back to cell strings later

% Prepare data
window = hann(frameLength);
f = sr*(0:(frameLength/2))/frameLength;  % frequency axis
numNotes = length(notes); %store to prevent multiple calls
timeAxis = (0:numFrames-1) * hopLength / sr;


parfor (i = 1:numFrames, numWorkers) % Attempt at parallelization

    startIndex = (i - 1) * hopLength + 1;
    endIndex   = startIndex + frameLength - 1;
    frame      = y(startIndex:endIndex);

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
    harmonic_indices = (1:numHarmonics); % Harmonic indices on the GPU

    %Task Parallelism using arrayfun and a GPU function
    [estimatedFrequencies(i,:), confidenceScores(i,:), noteIndices(i,:)] = ...
         analyzeHarmonics(estimatedF0, f, P1, A4, A4_INDEX, numNotes, harmonic_indices);

end

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



% 5. Tonic Estimation
frequency_weights = mean(confidenceScores ./ sum(confidenceScores, 2), 1);  % Normalize the power for each frame so that total is 1, then take the mean across all frames for each Harmonic
weighted_frequencies = estimatedFrequencies .* frequency_weights;

% Histogram Analysis to find prominent peaks
numBins = 50;
[N,edges] = histcounts(weighted_frequencies(:), numBins);

%Find peaks
minPeakDistance = 5;
[peaks,peakLocations] = findpeaks_gpu(N, minPeakDistance); % Custom GPU peak finding

% Convert peak locations to frequency values
peakFrequencies = edges(peakLocations);

%If peak frequencies are empty, use the mean to estimate tonic
if isempty(peaks)
   tonicEstimate = mean(weighted_frequencies(:));
   fprintf('No prominent peaks found. Using mean frequency: %.2f Hz\n', tonicEstimate);
else
   [~, maxPeakIndex] = max(peaks);
   tonicEstimate = peakFrequencies(peakLocations(maxPeakIndex));  % Find the frequency with the most prominent peak
   fprintf('Prominent Peak found. Tonic Estimated from largest peak in distribution : %.2f Hz\n', tonicEstimate);

end



% Find note name of tonic Estimate
tonicNoteName = frequencyToNote(tonicEstimate, A4, A4_INDEX, notes);

%Redefine A4 based on tonic estimation.
A4 = tonicEstimate;
A4_INDEX = frequencyToNoteIndex(A4,A4, A4_INDEX, length(notes));

fprintf("Estimated Tonic Note: %s\n", tonicNoteName);

% 6. Visualization

%Check if Graphics package is installed and load it, otherwise skip visualizaiton code,
if exist("graphics_toolkit", "builtin")
    graphics_toolkit("gnuplot")
end

figure;

% Subplot 1: Spectrogram
subplot(3, 1, 1);
spectrogram(y, hamming(frameLength), hopLength, sr, 'yaxis');
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