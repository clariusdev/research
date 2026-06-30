# Clarius Research Tools

This repository contains scripts and reference code to read and process data collected
from Clarius scanners, plus documentation for the App's research features. Each folder
holds a specific project with sample data and MATLAB/Python scripts to read, process, and
display the data.

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
- [QUS Reproducibility — L15HD3 and C3HD3](docs/qus-reproducibility.md) — what the
  released Research preset pins, what varies with depth or FOV, and how to lock RF
  acquisition for quantitative ultrasound studies (with a Python / Cast API example)

## Repository layout

```
.
├── common      shared readers (rdataread.py / rdataread.m)
├── viewer      runnable examples (python / matlab / jupyter) + sample data
└── docs        documentation
```

## Quick start

Read and display the bundled sample data:

```bash
cd viewer/python
python runme.py
```

The reader (`common/python/rdataread.py`) exposes `read_rf`, `read_iq`, and `read_env`;
see [Raw Data Format](docs/raw-data-format.md) for the binary layout and conversion to
B-mode.

## Related repositories

- [clariusdev/cast](https://github.com/clariusdev/cast) — Cast API for real-time
  streaming and raw-data download (App must be running)
- [clariusdev/solum](https://github.com/clariusdev/solum) — Solum OEM SDK for direct
  probe control and raw-data download
- [clariusdev/texo](https://github.com/clariusdev/texo) — script-driven research imaging
  (pre-release)
