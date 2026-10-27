# QUS Preset

**Software:** Clarius 13.1 and later
**Access:** Clarius App (with Cast), Solum SDK
**Audience:** Researchers acquiring RF for quantitative ultrasound (attenuation, backscatter, spectral, texture)

QUS is an application preset built for quantitative RF work. It acquires RF on every frame and fixes the RF acquisition settings, so they don't change with any of the image-optimisation controls. This replaces most of the manual locking that the released 12.x Research preset needs; for that workflow, see [QUS Reproducibility, L15HD3 and C3HD3](qus-reproducibility.md).

The RF is 16-bit **beamformed** scanlines (delay-and-sum on the probe), the same format as any other Clarius RF capture. See [raw-data-format.md](raw-data-format.md) for the package layout.

---

## Enabling QUS

QUS requires the **research** feature on the probe. Once it's enabled, QUS appears in the preset list for every supported probe.

| Interface | How to load |
|---|---|
| Clarius App | Select the **QUS** preset. RF mode is on automatically. |
| Cast API | Select QUS in the App, then connect with Cast as usual. RF streams to the Cast client. |
| Solum SDK | `solumLoadApplication("<probe model>", "qus", 0)`. Use array `0` (automatic) for PAL probes, which run QUS on the phased array. |

---

## What QUS fixes

These apply on every supported probe:

| Setting | Value | Notes |
|---|---|---|
| Transmit pulse | `+-` (single cycle) | No multi-cycle or penetration pulse |
| Transmit frequency | Probe centre frequency | Does not slide with depth (see the per-probe table for the frequency actually fired) |
| Transmit F-number | 1 | |
| Transmit aperture | Up to 64 elements | Limited by the F-number at shallow focus |
| Transmit focus | Mid-point of the imaging depth | Moves with imaging depth |
| Receive F-number | 1 (dynamic aperture) | |
| Receive apodization | Hamming | |
| RF lines | One per element | Spans the full B-mode field of view; there is no RF ROI |
| Analog TGC | **Flat 20 dB** at all depths | |
| Digital TGC on RF | 0 dB | |
| TGC sliders, Gain, auto gain | Do not affect RF | Auto gain is off by default; Gain and the sliders act only on B-mode display |
| Speed of sound | **1540 m/s** | No speed-of-sound option in this preset |
| RF streaming | On by default | |
| Compounding, harmonics, MLA on RF | Off | |

What still changes with **imaging depth**: transmit focus, RF sampling rate (below), and on some linear probes the anti-alias filter (per-probe table). Keep the imaging depth fixed between reference and sample acquisitions.

---

## Per-probe settings (HD3 probes)

All values are for HD3 probes (120 MHz transmit clock, 60 MHz receive clock, 14-bit ADC, TI AFE5828 front end).

### Array and transmit

| Probe | Array | Elements | Pitch | Radius | Lens | Centre freq (preset) | Freq fired* | Depth range (default) | Tx voltage |
|---|---|---|---|---|---|---|---|---|---|
| C3HD3 | curved | 192 | 300 µm | 45 mm | — | 3.5 MHz | 3.53 MHz | 3–40 cm (15) | 30 V |
| C7HD3 | curved | 192 | 205 µm | 20 mm | — | 6.0 MHz | 6.0 MHz | 1–15 cm (6) | 30 V |
| EC7HD3 | curved | 192 | 150 µm | 10 mm | — | 6.5 MHz | 6.67 MHz | 2–15 cm (8) | 37 V |
| L7HD3 | linear | 192 | 200 µm | — | 0.800 mm | 7.5 MHz | 7.5 MHz | 1–15 cm (5) | 30 V |
| L15HD3 | linear | 192 | 260 µm | — | 0.465 mm | 10 MHz | 10 MHz | 1–10 cm (4) | 30 V |
| L20HD3 | linear | 192 | 130 µm | — | 0.305 mm | 14 MHz | 15 MHz | 0.5–6 cm (2) | 30 V |
| PA2HD3 | phased | 80 | 250 µm | — | — | 2.4 MHz | 2.4 MHz | 3–40 cm (15) | 30 V |
| PALHD3 (phased array) | phased | 80 | 260 µm | — | 0.802 mm | 2.4 MHz | 2.4 MHz | 3–40 cm (15) | 30 V |

\* Each half-cycle is a whole number of 120 MHz transmit clocks, so the frequency fired is `60 / round(60 / f)` MHz.

### Receive

| Probe | LNA + PGA gain | Anti-alias filter | Receive tracking (shallow → deep over depth) |
|---|---|---|---|
| C3HD3 | 18 + 21 = 39 dB | 20 MHz | 5 → 2.5 MHz over 300 mm |
| C7HD3 | 21 + 27 = 48 dB | 20 MHz | 8 → 3 MHz over 120 mm |
| EC7HD3 | 21 + 24 = 45 dB | 20 MHz | 10 → 4 MHz over 50 mm |
| L7HD3 | 21 + 21 = 42 dB | 20 MHz | 12 → 5 MHz over 120 mm |
| L15HD3 | 21 + 21 = 42 dB | 30 MHz below ~7.4 cm imaging depth, 20 MHz deeper | 15 → 7 MHz over 70 mm |
| L20HD3 | 21 + 24 = 45 dB | 30 MHz | 18 → 10 MHz over 50 mm |
| PA2HD3 | 21 + 24 = 45 dB | 20 MHz | 4.5 → 2.5 MHz over 250 mm |
| PALHD3 (phased array) | 21 + 24 = 45 dB | 20 MHz | 4.5 → 2.5 MHz over 250 mm |

- **Front-end gain** is fixed per probe. It does not change with depth, Gain or TGC.
- **Receive tracking** shifts the receive band linearly from the shallow to the deep frequency over the stated round-trip depth, then holds. It shapes the RF spectrum with depth, so normalise against a reference phantom captured at the same imaging depth.
- **The anti-alias filter** on L15 follows the B-mode transmit frequency, which slides with imaging depth even though the RF transmit frequency doesn't.

---

## RF sampling rate

The probe has a fixed RF buffer per line, so deeper imaging needs more decimation:

```
decimation   = ceil(imaging depth / 3.8 cm), with 2 rounded up to 3
sampling rate = 60 MHz / decimation
```

| Imaging depth | Decimation | Sampling rate |
|---|---|---|
| up to 3.8 cm | 1 | 60 MHz |
| 3.8 – 11.4 cm | 3 | 20 MHz |
| 11.4 – 15.2 cm | 4 | 15 MHz |
| 15.2 – 19.0 cm | 5 | 12 MHz |
| 19.0 – 22.8 cm | 6 | 10 MHz |
| 22.8 – 26.6 cm | 7 | 8.57 MHz |
| 26.6 – 30.4 cm | 8 | 7.5 MHz |
| 30.4 – 34.2 cm | 9 | 6.67 MHz |
| 34.2 – 38.0 cm | 10 | 6 MHz |
| 38.0 – 40.0 cm | 11 | 5.45 MHz |

The rate applied to every capture is in the `sampling rate` field of the `_rf.yml`, and in `CusRawImageInfo.samplingRate` when streaming through Solum.

---

## Converting samples to depth

```
delay samples = round( 2 × (lens thickness + RF start depth) / vsound × fs )
depth below the lens (sample i) = (delay samples + i) × vsound / (2 × fs) − lens thickness
```

With QUS, `vsound` is always 1540 m/s. The lens thickness is converted at the tissue speed of sound, not a lens-specific value.

---

## Recommended workflow

1. Load QUS on the probe and fix the **imaging depth** for the study.
2. Acquire **reference phantom** data with QUS at the same depth, on the same probe model and software version.
3. Acquire sample data without changing depth.
4. Normalise sample spectra by reference spectra at matching depth. This removes pulse, aperture, diffraction, front-end gain, TGC and receive-tracking effects together.
5. Check each capture's `_rf.yml` for `transmit frequency`, `imaging depth`, `focal depth` and `sampling rate` before accepting it.

References acquired with other presets, or with 12.x, are not valid for QUS data.

---

## Known issue in 13.1

The `tgc:` line in the 13.1 `_rf.yml` may show the B-mode TGC curve instead of the flat 20 dB curve QUS applies to RF. The RF data is acquired at a flat 20 dB analog TGC regardless of what that line shows. This will be corrected in a future release.
