% The following script reads Clarius research data (RF/IQ/B) acquired using
% the Clarius scanner and downloaded from clarius cloud
%
% Note: code is tested on mac, for other operating systems you may need to
% use backslash (\) instead of (/) for relative paths to work. 
%
% Author: Reza Zahiri

close all 
clear all
clc

% add library
addpath('../../common/matlab');

% set data path
path = '../../data/convex/';

%% read rf data 
filenameRF = 'convex_rf.raw';

numFrames = 50;
[dataRF, header] = rdataread([path, filenameRF], numFrames);
if (numFrames > header.frames)
    numFrames = header.frames;
end

% display rf images
figure; 
colormap(gray)
for i = 1:numFrames
    RF = squeeze(dataRF(i,:,:));
    BB = 20*log10(1 + abs(hilbert(RF)));
    subplot(1,2,1), imagesc(RF, [-1000 1000]); title('raw RF')
    subplot(1,2,2), imagesc(BB, [15 70]); title('sample B from RF')
    drawnow;
end

%% read iq data 
filenameIQ = 'convex_iq.raw';

numFrames = 50;
[dataIQ, header] = rdataread([path, filenameIQ], numFrames);
if (numFrames > header.frames)
    numFrames = header.frames;
end

% separate i and q data
idata = dataIQ(:,1:2:end,:);
qdata = dataIQ(:,2:2:end,:);

% display iq data
figure; 
colormap(gray)
for i = 1:numFrames
    I = squeeze(idata(i,:,:));
    Q = squeeze(qdata(i,:,:));
    BB = 20*log10(1 + sqrt(I.^2 + Q.^2));

    subplot(1,3,1), imagesc(I, [-100 100]); title('I')
    subplot(1,3,2), imagesc(Q, [-100 100]); title('Q')
    subplot(1,3,3), imagesc(BB, [15 70]); title('sample b for IQ')
    drawnow;
end

%% read b or envelope pre scanconversion data 
filenameB = 'convex_env.raw';

numFrames = 50;
[dataB, header] = rdataread([path, filenameB], numFrames);
if (numFrames > header.frames)
    numFrames = header.frames;
end

% display b/envelope data
figure; 
colormap(gray)
for i = 1:numFrames
    BB = squeeze(dataB(i,:,:));

    imagesc(BB, [0 255]); title('B pre scan')
    drawnow;
end
