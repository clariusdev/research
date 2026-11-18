# Clarius Research Tools

This repository contains scripts and reference code to read, scan convert, and display
raw data collected from Clarius scanners, sample data, and documentation for the App's
research features.

Data that can be acquired from Clarius scanners includes:

- **RF** — raw radiofrequency data
- **IQ** — quadrature data
- **Envelope** — B-mode grayscale

## Documentation

- [In-App Research Tools](docs/in-app-tools.md) — capture raw data, stream RF, and emit
  the hardware sync pulse from the Clarius App
- [Raw Data Format](docs/raw-data-format.md) — package layout, the `.raw`/`.yml`/`.tgc`
  formats, sample types, and how to read them in Python/MATLAB
- [How Imaging Parameters Are Automated](docs/imaging-parameter-automation.md) — baseline
  knowledge on how depth, preset, and probe drive transmit frequency, sampling, and gain
- [Low-Level Parameters](docs/low-level-parameters.md) — the research parameters
  accessible through the Cast and Solum APIs
- [RF Frame Rate & Data Volume](docs/rf-frame-rate.md) — what limits beamformed‑RF frame
  rate (time of flight, line count, sector, MLA) and data volume (per‑depth tables, burst
  buffer, streaming), MI/TI/thermal caveats, and a probe reference
- [QUS Preset](docs/qus-preset.md) — the preset for quantitative RF: what it fixes,
  per-probe transmit/receive settings, sampling rate by depth, and the recommended workflow
- [QUS Reproducibility — L15HD3 and C3HD3](docs/qus-reproducibility.md) — what the
  released Research preset pins, what varies with depth or FOV, and how to lock RF
  acquisition for quantitative ultrasound studies (with a Python / Cast API example)

## Repository layout

```
.
├── common      shared readers (rdataread.py / rdataread.m) and scan conversion (scanconvert.py)
├── data        sample captures of a wire phantom: linear (L7HD3) and convex (C3HD3)
├── viewer      runnable examples (python / matlab / jupyter)
└── docs        documentation
```

## Quick start

Read and display the bundled sample data:

```bash
cd viewer/python
python runme.py
```

The reader (`common/python/rdataread.py`) exposes `read_rf`, `read_iq`, and `read_env`,
and `common/python/scanconvert.py` places a frame in millimetres from the probe geometry
in its `.yml`. To scan convert a capture of your own to PNGs:

```bash
python common/python/scanconvert.py path/to/capture_env.raw --frames all
```

See [Raw Data Format](docs/raw-data-format.md) for the binary layout, conversion to
B-mode, and scan conversion.

## Related repositories

- [clariusdev/cast](https://github.com/clariusdev/cast) — Cast API for real-time
  streaming and raw-data download (App must be running)
- [clariusdev/solum](https://github.com/clariusdev/solum) — Solum OEM SDK for direct
  probe control and raw-data download
- [clariusdev/texo](https://github.com/clariusdev/texo) — script-driven research imaging
  (pre-release)
