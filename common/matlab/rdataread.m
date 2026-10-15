function [data, header, ts] = rdataread(filename, frames)
% reads and returns Clarius data
%
% Example
%       [Im, header] = rdataread(filename, frame);
%
% Inputs:  
%       filename    The path of the data to open
%       frame       The frames to read, if this number is larger than
%       the total number of frames in the file it be rest to maximum number
%       of frames.
%
% Return:
%     data          The image data returned into an array (h, w, numframes)
%     header        The file header information   
%     ts            The time stamp
%
% Author: Reza Zahiri
%
% See also RunMe

% open the file
fid= fopen(filename, 'r');

if( fid == -1)
    error('Cannot open file');
end

% read the header info
hinfo = fread(fid, 5, 'int32');
header.id = hinfo(1);
header.frames = hinfo(2);
header.lines = hinfo(3);
header.samples = hinfo(4);
header.sampleSize = hinfo(5);

if frames > header.frames
    frames = header.frames;
end

% disp(header);
% header.id numbering differs between releases, so the sample size decides the format
if header.sampleSize == 4 % iq: interleaved int16 I and Q
    ts = zeros(1,frames);
    data = zeros(frames, header.samples*2, header.lines);
    for f = 1: frames
        % read time stamp
        ts(f) = fread(fid, 1,'int64');
        % read one frame
        oneline = fread(fid, [header.samples * 2, header.lines],'int16');
        data(f,:,:) = oneline;
    end
elseif header.sampleSize == 1 % env
    ts = zeros(1,frames);
    data = zeros(frames,header.samples, header.lines);
    for f = 1: frames
        % read time stamp
        ts(f) = fread(fid, 1,'int64');
        % read one frame
        oneline = fread(fid, [header.samples, header.lines],'uint8');
        data(f,:,:) = oneline;
    end
elseif header.sampleSize == 2 % rf or per-channel rf
    nsamples = header.samples;
    nlines = header.lines;
    ts = zeros(1,frames);
    data = zeros(frames, nsamples, nlines);
    for f = 1:frames
        % read the time stamp
        ts(f) = fread(fid, 1,'int64');
        % read the frame
        data(f, :, :) = fread(fid, [nsamples, nlines],'int16');
    end
end

% close the file
fclose(fid);
