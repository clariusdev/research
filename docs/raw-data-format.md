# Raw Data Format

How Clarius raw data is packaged on disk, the binary layout of each `.raw` file, the
metadata that accompanies it, and how to read it in Python or MATLAB. For how to *capture*
the data, see [in-app-tools.md](in-app-tools.md).

Clarius scanners can produce three kinds of raw data:

- **RF** — raw radiofrequency, 16-bit beamformed samples
- **IQ** — quadrature data, interleaved 16-bit I and Q
- **Envelope** — B-mode grayscale, 8-bit, pre-scan-converted (ultrasound coordinates)

## Package layout

Accessed data arrives as a `.tar` package; each raw stream inside is LZO-compressed
(`.lzo`). Decompress with any LZO tool before reading. After extraction:

```
raw_data.tar
├── <timestamp>_env.raw[.lzo]   envelope / B grayscale
├── <timestamp>_env.yml         envelope metadata
├── <timestamp>_env.tgc.yml     per-frame TGC (present if auto gain was used)
├── <timestamp>_iq.raw[.lzo]    IQ (Doppler data when color/power mode is on)
├── <timestamp>_iq.yml          IQ metadata
├── <timestamp>_rf.raw[.lzo]    RF (RF mode only)
├── <timestamp>_rf.yml          RF metadata
└── <timestamp>_rf.tgc.yml      per-frame TGC for RF (if auto gain was used)
```

In a grayscale/Doppler capture you get `env` + `iq`; in RF mode you get `env` + `rf`.

## `.raw` binary layout

Every `.raw` file uses the same structure: a header, then a timestamp + data block per
frame.

```
Header
Timestamp 0
Data 0
Timestamp 1
Data 1
...
Timestamp N
Data N
```

The header is five little-endian `uint32` fields:

```
uint32 id
uint32 numFrames
uint32 numScanLines
uint32 numSamplesPerLine
uint32 sampleSizeInBytes
```

Each timestamp is a little-endian `uint64` in nanoseconds:

```
uint64 timeInNanoSeconds
```

Each data block is `numScanLines * numSamplesPerLine * sampleSizeInBytes` bytes, so the
total file size is:

```
sizeof(Header) + numFrames * (sizeof(Timestamp) + numScanLines * numSamplesPerLine * sampleSizeInBytes)
```

## Sample formats

| Type | Sample | Notes |
|------|--------|-------|
| **Envelope (B)** | 8-bit grayscale | Pre-scan-converted (ultrasound, not pixel, coordinates). |
| **IQ** | 32-bit pairs (16-bit I + 16-bit Q) | Demodulation frequency depends on scanner/workflow and may vary with depth and parameters. In a `.raw` row the I and Q samples are interleaved (`I,Q,I,Q,…`). |
| **RF** | 16-bit beamformed | Clarius digitizes natively at 60 MHz; the stored sampling rate is reported in the `.yml`. |

RF sampling adapts to depth so the data can be captured, buffered, and transferred:

| Depth | RF sampling |
|-------|-------------|
| < 2 cm | 60 MHz |
| 2–4 cm | 30 MHz |
| > 4 cm | 15 MHz |

## `.yml` metadata

Each `.raw` has a sibling `.yml` describing acquisition. Example (RF):

```yaml
frames: 13
frame rate: 11 Hz
transmit frequency: 10 MHz
imaging depth: 40 mm
focal depth: 20 mm
tgc: { 0.00mm, 30.00dB }{ 40.00mm, 35.00dB }
size: {samples per line: 3120, number of lines: 192, sample size: 2 bytes}
type: RF
compression: none
sampling rate: 60 MHz
delay samples: 62
lines:
  - {rx element: 0, tx element: 1.5, angle: 0 °}
  - {rx element: 1, tx element: 1.5, angle: 0 °}
  ...
```

Key fields:

| Field | Meaning |
|-------|---------|
| `frames` | Number of frames in the `.raw`. |
| `frame rate` | Acquisition frame rate. |
| `transmit frequency` | Transmit center frequency. |
| `imaging depth` | Imaging depth. |
| `focal depth` | Transmit focal depth. |
| `tgc` | Depth/gain points of the nominal TGC curve. |
| `size` | `samples per line`, `number of lines`, `sample size` (bytes) — mirrors the `.raw` header. |
| `type` | `RF`, `IQ`, or `envelope`. |
| `compression` | Compression of the samples (`none` once decompressed). |
| `sampling rate` | Sample rate of the acquired data (see RF table above). |
| `delay samples` | Leading samples before the first valid sample (acquisition delay). |
| `lines` | Per-line geometry: receive element, transmit element, and steering angle. Use it to map scan lines to aperture positions. |

### `.tgc.yml` per-frame TGC

Because Clarius defaults to **automated** TGC, each frame can be acquired with a slightly
different analog gain curve. The `.tgc.yml` records the curve applied to each frame, keyed
by the frame timestamp that matches the `.raw` timestamps:

```
timestamp: 235855423246 { 7.00mm, 15.70dB }{ 21.00mm, 26.46dB }{ 35.00mm, 26.82dB } ...
```

It is only present when auto gain (auto TGC) was active during the capture.

## Reading the data

This repo ships reference readers and runnable examples:

- [`common/python/rdataread.py`](../common/python/rdataread.py) — `read_rf`, `read_iq`,
  `read_env`
- [`common/matlab/rdataread.m`](../common/matlab/rdataread.m) — MATLAB equivalents
- [`viewer/python/runme.py`](../viewer/python/runme.py),
  [`viewer/matlab/runme.m`](../viewer/matlab/runme.m),
  [`viewer/jupyter/runme.ipynb`](../viewer/jupyter/runme.ipynb) — load and display the
  bundled sample data in [`viewer/data`](../viewer/data)

### Python: read and convert to B

The reader parses the header, then each timestamp + frame into a
`lines × samples × frames` array (IQ has `samples * 2` columns: interleaved I/Q).

```python
import numpy as np
from scipy.signal import hilbert
import rdataread as rd

# RF -> B (envelope detection + log compression)
hdr, timestamps, data = rd.read_rf("phantom_rf.raw")
b = 20 * np.log10(np.abs(1 + hilbert(data[:, :, 0])))

# IQ -> B (magnitude + log compression)
hdr, timestamps, data = rd.read_iq("phantom_iq.raw")
i, q = data[:, 0::2, :], data[:, 1::2, :]
b = 10 * np.log10(1 + i[:, :, 0] ** 2 + q[:, :, 0] ** 2)

# Envelope is already 8-bit B data
hdr, timestamps, data = rd.read_env("phantom_env.raw")
```

See [`viewer/python/runme.py`](../viewer/python/runme.py) for the full display pipeline
(RF, IQ, and envelope frames side by side).

> Remember the data is in ultrasound (polar/array) coordinates — scan conversion to pixel
> space is up to you and depends on the probe geometry reported in the `.yml`.
