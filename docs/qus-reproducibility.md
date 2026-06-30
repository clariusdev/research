# Reproducible RF Acquisition for QUS on Clarius

**Probes:** L15HD3 (linear) and C3HD3 (curved)
**Software:** Released 12.x (Clarius App + Cast API)
**Audience:** Researchers running quantitative ultrasound (attenuation, backscatter, spectral, texture) on raw RF data.

This guide explains exactly which acquisition parameters the released **Research** preset already pins for you on these two probes, which ones still vary (and how), what changes with depth or ROI, and how to use the Cast API to lock the rest and verify each capture's resolved values via the recorded `.yml` metadata. A short Python example using `pyclariuscast` is at the end.

---

## TL;DR — the locking recipe

1. **Select the Research preset** on the probe (it pins ~85% of what matters by itself).
2. In the Clarius App, **disable Auto Focus** and set a **manual Focus Depth**; **disable Auto Gain**; verify TGC sliders are at a fixed reference (e.g. flat 0/0/0 dB).
3. **Fix imaging depth** for the entire study, and stay within **one decimation regime** — *do not cross the depth boundary* below (20 cm for C3, 6 cm for L15) without re-validating, because RF sampling rate changes across that boundary.
4. **Fix the sector / FOV width** — narrowing it changes line density and aperture coverage.
5. (Optional, advanced) **Pin further parameters via the Cast API** with `castSetParameter` / `castEnableParameter` / `castSetPulse` for any value you want to override beyond what the preset gives you.
6. **Parity-check every capture's `.yml`** to confirm the resolved values are what you locked.

If you follow steps 1–4 you already have a highly reproducible RF acquisition. Step 5 is for studies that need additional control beyond the preset defaults.

---

## What the Research preset pins for you

These values are **fixed by the Research preset** on each probe and do not change between captures as long as you stay on that preset:

### C3HD3 — Research preset

| Parameter | Pinned value | Notes |
|---|---|---|
| Transmit centre frequency (`txFreq`) | **3.5 MHz** | Equal to the probe's centre frequency; does not slide with depth on this preset. |
| Transmit voltage (`vpp` / `vnn`) | 30 V / 30 V | Symmetric drive. |
| Transmit pulse (`txPulse`) | `+-` | Single half-cycle. |
| Transmit aperture (`txApt`) | 64 elements | Maximum aperture. |
| Transmit f-number (`txFn`) | 2 | |
| Receive f-number (`rxFn`) | 1 | |
| Receive demodulation (`rxFreqShallow` / `rxFreqDeep`) | 5 MHz / 2.5 MHz | |
| Dynamic range (`dynRange`) | 50 dB (+ user offset) | |
| Noise floor (`noiseFloor`) | 7 dB | |
| TGC curve | 10 dB → 35 dB across 0 → 150 mm | This is the *preset's* TGC; the App's TGC sliders can override. Verify they are at a known fixed position before scanning. |
| Receive channels (`rxc`) | 64 | |
| Multi-line acquisition (`mla`) | 4 | 4 parallel beams per transmit. |
| Pulse-inversion harmonics (`pih`) | off | |
| Low-pass filter ID (`lpfid`) | 17 | |

### L15HD3 — Research preset

| Parameter | Pinned value | Notes |
|---|---|---|
| Transmit centre frequency (`txFreq`) | **10 MHz** | Equal to the probe's centre frequency. |
| Transmit voltage (`vpp` / `vnn`) | 30 V / 30 V | |
| Transmit pulse (`txPulse`) | `+-` | |
| Transmit aperture (`txApt`) | 64 elements | |
| Transmit f-number (`txFn`) | 2 | |
| Receive f-number (`rxFn`) | 1 | |
| Receive demodulation (`rxFreqShallow` / `rxFreqDeep`) | 12 MHz / 8 MHz | |
| Dynamic range (`dynRange`) | 60 dB (+ user offset) | |
| Noise floor (`noiseFloor`) | 10 dB | |
| TGC curve | 15 dB at 0 mm → 25 dB at imaging depth | The bottom-point depth tracks endDepth — see "What varies with depth" below. |
| Receive channels (`rxc`) | 64 | |
| Multi-line acquisition (`mla`) | 4 | |
| Pulse-inversion harmonics (`pih`) | off | |
| Low-pass filter ID (`lpfid`) | 0 | |

> **No depth-driven transmit-frequency slide on the Research preset.** Newer software adds a depth-vs-frequency slide for clinical presets; the released Research preset does not have it. `txFreq` stays at the probe's centre frequency regardless of how you change imaging depth.

---

## What still varies, and how

Even on the Research preset, a small number of parameters change with depth or with ROI. These are the only things you need to control directly.

### Varies with imaging depth

| Parameter | Behaviour | C3HD3 | L15HD3 |
|---|---|---|---|
| `txFocus` (transmit focal depth) | Tracks half the imaging depth when Auto Focus is on. Set Auto Focus **off** in the App and choose a manual focus to fix it. | `endDepth / 2` | `endDepth / 2` |
| `rfDecimation` (RF decimation factor) | Piecewise — **single step** at one depth boundary. Sampling rate after the step is roughly halved. Keep your study within one regime. | 10 below 20 cm → 16 above 20 cm | 3 below 6 cm → 4 above 6 cm |
| `envDecimation` (envelope decimation) | Tracks `rfDecimation` | same as `rfDecimation` | `rfDecimation + 1` |
| `rxFiltDepth` (receive filter depth) | Tracks the imaging depth `endDepth` | — | — |
| TGC bottom-point depth | L15 only: the second TGC depth point follows `endDepth` | (fixed at 150 mm) | `tgcDepth2 = endDepth` |

**Practical implication:** sampling rate is depth-driven by hardware design — the on-probe buffer can only hold a fixed number of samples per acquisition, so deeper depths require more decimation. This is unavoidable; the goal is to **stay in one regime** so it doesn't switch on you mid-study. The exact effective sampling rate for every capture is in the `.yml` (see "verification" below).

### Varies with sector / FOV width

The App's ROI / sector control sets a fraction `sector` (0..1), which feeds the beamformer config:

| Effect | What it does |
|---|---|
| `b line density` | Scales as `probe-default line density × sector`. Narrowing the FOV reduces the number of scan lines proportionally. |
| `b first / last element` | Shifts inward as sector shrinks (the active aperture narrows). |
| `b first / last angle` | Scales with sector (phased-array probes — does not affect the L15 linear array's lateral steering). |

**Practical implication:** for QUS that's sensitive to lateral sampling (lateral spectral analysis, texture), **lock the sector / FOV width** in addition to depth. Capture the same FOV every time.

### Does not change with depth on the Research preset

These do not move with depth — they remain at the pinned values in the tables above:
- Transmit centre frequency
- Transmit voltage, pulse shape, aperture, f-number
- Receive f-number, demodulation frequencies
- Dynamic range, noise floor
- Multi-line acquisition setting

---

## Reproducibility checklist for a QUS study

App-side, once per session:
- [ ] **Preset:** Research, on the C3HD3 or L15HD3.
- [ ] **Cast Permission → Research** (forces Cast on port 5828, deterministic).
- [ ] **Auto Focus:** off → set a fixed manual **Focus Depth**.
- [ ] **Auto Gain:** off.
- [ ] **TGC sliders:** verify they are at the fixed reference position you chose for the study (e.g. centred / flat).
- [ ] **Imaging Depth:** fixed at study value; **do not cross the decimation boundary** during the study (20 cm for C3, 6 cm for L15).
- [ ] **Sector / FOV:** fixed.

Then for each capture, verify the `.yml` matches your locked configuration before accepting the data into your processing pipeline.

---

## Verifying each capture via the `.yml`

Every captured `.raw` file ships with a sibling `.yml` that records the *actually applied* values for that capture. This is your primary read-back today (the Cast API does not yet expose a runtime parameter-read API — that's coming in the next release; see below).

Fields to parity-check at the start of your processing pipeline:

```yaml
transmit frequency:    # must equal your locked value (3.5 MHz for C3, 10 MHz for L15)
imaging depth:         # must equal your locked depth
focal depth:           # must equal your manual Focus Depth (with Auto Focus off)
tgc:                   # the actual curve applied (verify against your locked sliders)
size:                  # samples per line, number of lines, sample size
  samples per line:    # changes with depth + decimation
  number of lines:     # changes with sector / line density
  sample size: 2 bytes # 16-bit RF samples
type: RF
compression:           # 'none' once decompressed
sampling rate:         # effective RF sample rate; verify the decimation regime
delay samples:         # leading samples before the first valid sample (acquisition delay)
lines:                 # per-line geometry: rx element, tx element, angle
```

Reject (or at least flag) any capture whose `sampling rate`, `transmit frequency`, `focal depth`, or `tgc` deviates from your locked expected values. The `.tgc.yml` sidecar (present when auto-gain was modifying TGC during capture) is what you want to be **empty** — its presence with non-empty entries means TGC moved between frames.

---

## Cast API — Python example with `pyclariuscast`

If you want to go beyond what the Research preset pins (or simply assert your locked values programmatically), use the Cast API. Below is a minimal sketch using the `pyclariuscast` Python binding (shipped with the Cast release packages: https://github.com/clariusdev/cast/releases).

```python
import pyclariuscast
import time

# Callbacks (only the ones you need)
def on_new_image(image, width, height, sz, micronsPerPixel, timestamp, angle, imu):
    pass  # B-mode display path — not used for QUS

def on_new_raw_image(image, lines, samples, bps, axial, lateral, timestamp, jpg, rf, angle):
    pass  # raw path — used by RF buffered download later

def on_freeze(state):
    print(f"freeze state: {state}")

def on_buttons(button, clicks):
    pass

# 1. Initialize. The Clarius App must already be running and connected to the probe.
cast = pyclariuscast.Caster(
    on_new_image, on_new_raw_image, None, on_freeze, on_buttons
)
cast.init("/tmp/clarius-keys", 1024, 768)

# 2. Connect to the App's Cast port. Get IP from the App's status page;
#    port is 5828 when 'Cast Permission' is set to Research.
ok = cast.connect("192.168.1.1", 5828, "research")
assert ok, "cast.connect failed"

# 3. Optional explicit pinning beyond the Research preset's defaults.
#    Each of these overrides the preset value. Mind the safety caveats —
#    transmit-side changes can move you outside the validated acoustic envelope.
cast.setParam("txFreq", 10.0)           # MHz (L15 already pinned; this is belt + braces)
cast.setParam("txFocus", 2.0)           # cm — your fixed focal depth
cast.setParam("txApt", 64)              # elements — full aperture
cast.setPulse("txPulseGen", "+-")       # fundamental
cast.setParam("rfDecimation", 3)        # lock decimation regime explicitly
cast.setParam("vpp", 30); cast.setParam("vnn", 30)
cast.setParam("dyn", 60)                # dB
cast.setParam("nf", 10)                 # dB
cast.enableParam("sa", 0)               # synthetic aperture off
cast.enableParam("pih", 0)              # pulse-inversion harmonics off
cast.userFunction(pyclariuscast.UserFunction.AutoGain, 0)  # confirm auto-gain off

# 4. Freeze and buffer raw data on the probe (do this via the App's Buffer button,
#    or programmatically below).
cast.userFunction(pyclariuscast.UserFunction.Freeze, 0)
time.sleep(0.5)

# 5. List buffered timestamps, then request the package as an LZO tarball.
def on_avail(res, b_timestamps, iqrf_timestamps):
    print(f"avail rf/iq frames: {len(iqrf_timestamps)}")

def on_req(res, extension):
    print(f"raw request size: {res} bytes, ext={extension}")
    buf = bytearray(res)
    def on_read(n): print(f"read {n} bytes")
    cast.readRawData(buf, on_read)

cast.rawDataAvailability(on_avail)
cast.requestRawData(0, 0, 1, on_req)  # 0,0 = all buffered; lzo=1

# 6. Disconnect cleanly when done.
cast.disconnect()
cast.destroy()
```

Notes on this example:

- **`setParam` / `setPulse` / `enableParam`** write values to the probe. On released software they push but **do not read back**. The next Cast release will add a read API; until then, use the `.yml` of each capture as the read-back path.
- **`userFunction`** is the higher-level command channel (freeze, set depth, set gain, mode toggle). Use it for App-state-level changes (AutoGain off, freeze) and `setParam` for low-level acquisition pinning.
- **Each parameter you write is recorded in the resulting capture's `.yml`**, so even without read-back you have full audit at processing time.

A full working example is in the Cast release package under `examples/python/pycaster.py`; that's the place to copy and adapt the connect-and-stream loop. See https://github.com/clariusdev/cast/blob/master/docs/getting-started.md for the canonical walkthrough.

---

## Current limitations on released software

1. **Cast API write-only.** `setParam` etc. can write but cannot read back. Use the `.yml` for read-back today. *Coming in the next release: parameter read-back through the Cast API for runtime verification.*
2. **No user-locked preset at the App level.** You configure the Research preset + manual overrides each session. *Coming in the next release: a dedicated Research preset with stronger out-of-the-box locking for QUS.*
3. **Sampling rate must vary with depth.** This is a hardware constraint — the on-probe buffer has a fixed capacity, and deeper depths require more decimation. The Research preset minimises the surface (single boundary at 20 cm for C3, 6 cm for L15) but cannot eliminate it. The exact value applied is always in the `.yml`.
4. **AutoFocus toggle and TGC curve setting** are App-side configurations; the Cast API can disable AutoGain via `userFunction(AutoGain)` but does not have a `castSetTgc` analogue. Set TGC sliders in the App.
5. **Pre-/post-beamformed RF** — the Clarius FPGA performs delay-and-sum on-probe, so the RF you receive is 16-bit *beamformed scanlines*, not raw per-channel data. Raw per-channel access is on a longer-term roadmap.
6. **Beamforming mode** is fixed in the FPGA (delay-and-sum) and not configurable.

---

## What's coming in the next release

(Roadmap items Kris confirmed during the call, in active development; specific timing tied to App store approval cycle.)

- **Dedicated fixed Research preset** with stronger parameter locking out of the box, intended for QUS workflows.
- **Cast API parameter read-back**, so your acquisition script can confirm at runtime that the values you wrote actually took effect, without waiting for the `.yml` after a capture.
- **B-mode TGC on / RF TGC off** capture mode (a separate research request) — independent of these QUS changes but relevant if you want truly TGC-free RF in future work.

---

## Differences between L15HD3 and C3HD3 — at a glance

| | C3HD3 (curved) | L15HD3 (linear) |
|---|---|---|
| Geometry | curved, 45 mm radius, 192 elements, 300 µm pitch | linear, 192 elements, 260 µm pitch |
| Centre frequency | 3.5 MHz | 10 MHz |
| Frequency band | 2 – 6 MHz | 5 – 15 MHz |
| Default depth | 10 cm | 3 cm |
| Decimation boundary | 20 cm | 6 cm |
| Research preset depth range | 3 – 30 cm | 1 – 11 cm |
| TGC bottom-point depth | Fixed at 150 mm | Tracks imaging depth |
| Typical QUS use | abdominal / phantom liver-equivalent | superficial / phantom shallow attenuation |

Lock the same probe + same depth + same FOV for the entire study. Don't mix probes within a single QUS comparison without separate calibration.

---

## Where to go from here

- Cast API canonical walkthrough: https://github.com/clariusdev/cast/blob/master/docs/getting-started.md
- Cast parameter reference (including all the `setParam` names): https://github.com/clariusdev/cast/blob/master/docs/parameters.md
- Research repo — raw-data format and `.yml` field reference: https://github.com/clariusdev/research/blob/master/docs/raw-data-format.md
- Research repo — full low-level parameter reference: https://github.com/clariusdev/research/blob/master/docs/low-level-parameters.md
- Imaging-parameter automation (this is the **dev-branch / future** behaviour for context — released doesn't have most of this cascade yet): https://github.com/clariusdev/research/blob/master/docs/imaging-parameter-automation.md

For follow-up on anything specific to your study (e.g., particular parameter values to pin for a given attenuation phantom, or running into a `.yml` field whose meaning isn't obvious), reach back out — happy to iterate.
