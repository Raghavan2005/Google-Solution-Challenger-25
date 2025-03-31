% MATLAB Script for Multi-Pitch Analysis and Tonic Estimation,
% Incorporating Tanpura and Singer's Dominant Pitch

% 1. Load Audio File
audioFilePath = 'kal.mp3';  % Replace with the actual path
fprintf('Executing: Loading audio file\n');
[y, sr] = audioread(audioFilePath);
y = y(:,1);%Convert to mono, only runs with mono track

% 2. Limit to 30 Seconds
analysis_duration = 30; % seconds
y = y(1:min(length(y), sr * analysis_duration));
fprintf('Executing: Limiting audio to 30 seconds\n');

% --- Parameters ---
frameLength = 2048;
hopLength   = 512;
fmin = 80;  % Minimum frequency to consider (Hz)
fmax = 800; % Maximum frequency to consider (Hz)

% --- Cepstral Analysis Pitch Tracking (Revised) ---

fprintf('Executing: Cepstral Analysis Pitch Tracking\n');

% Preallocate for pitch estimates
pitchEstimates = zeros(1, floor((length(y) - frameLength) / hopLength) + 1);
T = (0:length(pitchEstimates)-1) * hopLength / sr; % Time vector

for i = 1:length(pitchEstimates)
    % Extract the frame
    startIndex = (i - 1) * hopLength + 1;
    endIndex = min(startIndex + frameLength - 1, length(y));
    frame = y(startIndex:endIndex);

    % Apply windowing
    windowedFrame = frame .* hann(length(frame));

    % Compute the power cepstrum
    fftFrame = fft(windowedFrame, frameLength);
    powerSpectrum = abs(fftFrame).^2;
    logPowerSpectrum = log(powerSpectrum + eps); % Add a small value to avoid log(0)
    cepstrum = ifft(logPowerSpectrum);
    cepstrum = abs(cepstrum);

    % Find the peak in the cepstrum (excluding the very beginning)
    searchRange = round(sr/fmax):round(sr/fmin);  % More principled search range
    searchRange = searchRange(searchRange <= frameLength/2); % Ensure within bounds

    if isempty(searchRange)
        pitchEstimates(i) = NaN;
        continue;
    end
    [~, peakIndex] = max(cepstrum(searchRange));
    peakIndex = peakIndex + searchRange(1) - 1;
    estimatedPeriod = peakIndex;

    estimatedFrequency = sr / estimatedPeriod;

    % Store the pitch estimate
    pitchEstimates(i) = estimatedFrequency;
end

% --- Tanpura-Informed Tonic Estimation ---
fprintf('Executing: Tanpura-Informed Tonic Estimation\n');

% Analyze the entire audio to find the lowest prominent tanpura frequency.
fft_y = fft(y);
powerSpectrum_y = abs(fft_y).^2;
frequencies_y = (0:length(y)-1) * (sr / length(y));

% Limit the frequency range for the tanpura (adjust if needed). This focuses on the lowest octave sound.
tanpura_fmin = 50;
tanpura_fmax = 300;
tanpura_indices = (frequencies_y >= tanpura_fmin) & (frequencies_y <= tanpura_fmax);

frequencies_tanpura = frequencies_y(tanpura_indices);
powerSpectrum_tanpura = powerSpectrum_y(tanpura_indices);

% Find the peak frequency in the tanpura range.  This assumes the lowest tanpura sound is the loudest
[~, max_index] = max(powerSpectrum_tanpura);
tanpura_tonic_estimate = frequencies_tanpura(max_index);

fprintf('Tanpura Tonic Estimate: %.2f Hz\n', tanpura_tonic_estimate);

% --- Singer's Dominant Pitch Estimation ---
fprintf('Executing: Singer Dominant Pitch Estimation\n');

valid_pitch_indices = find(~isnan(pitchEstimates) & pitchEstimates > fmin & pitchEstimates < fmax);

if ~isempty(valid_pitch_indices)
    valid_pitches = pitchEstimates(valid_pitch_indices);

    % Histogram Analysis to find prominent peaks
    numBins = 36;  % Number of bins (3 per semitone)
    binEdges = linspace(fmin, fmax, numBins + 1);
    [N, edges] = histcounts(valid_pitches, binEdges);

    % Find peaks in histogram
    minPeakProminence = 0.1 * max(N); % Adjust for prominence
    [peaks, peakLocations] = findpeaks(N, 'MinPeakProminence', minPeakProminence, 'MinPeakDistance', 2);

    peakFrequencies = edges(peakLocations);

    if isempty(peakFrequencies)
        singer_dominant_pitch = median(valid_pitches); % Use median if no clear peak
        fprintf('No prominent peaks found. Using median frequency for Singer: %.2f Hz\n', singer_dominant_pitch);
    else
        [~, maxPeakIndex] = max(peaks);
        singer_dominant_pitch = peakFrequencies(maxPeakIndex);
        fprintf('Prominent Peak found. Singer Dominant Pitch: %.2f Hz\n', singer_dominant_pitch);
    end
else
    singer_dominant_pitch = NaN;
    fprintf('No valid pitch estimates for the singer.\n');
end

% --- Combined Tonic Estimation ---
fprintf('Executing: Combined Tonic Estimation\n');

% Prioritize the Tanpura; if not available, use the singer's dominant pitch.
if ~isnan(tanpura_tonic_estimate) && tanpura_tonic_estimate > 0
    tonicEstimate = tanpura_tonic_estimate;
    fprintf('Using Tanpura tonic estimate.\n');
elseif ~isnan(singer_dominant_pitch)
    tonicEstimate = singer_dominant_pitch;
    fprintf('Using Singer dominant pitch.\n');
else
    tonicEstimate = NaN;
    fprintf('No valid tonic estimate found.\n');
end

% --- Tonic Verification and Western Pitch Value (Combined) ---
if ~isnan(tonicEstimate)
    A4 = 440;
    semitone_offset = 12*log2(tonicEstimate/A4);
    pitch_class_number = mod(round(semitone_offset), 12);
    pitch_class_names = {'A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#'};
    estimated_pitch_class = pitch_class_names{pitch_class_number+1};

    fprintf('Estimated Pitch Class (Combined): %s\n', estimated_pitch_class);
else
    fprintf('Could not determine pitch class.\n');
end

% Cleanup
clearvars S F T magnitudeSpectrogram peakThreshold peakIndices majorScale chromaticScale N edges peaks peakLocations peakFrequencies pitchEstimates;
clearvars fft_y powerSpectrum_y frequencies_y tanpura_fmin tanpura_fmax tanpura_indices frequencies_tanpura powerSpectrum_tanpura max_index;