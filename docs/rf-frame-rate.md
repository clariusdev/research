# Beamformed RF Acquisition: Frame Rate & Data Volume (HD3)

> Reference note for Clarius Solum / research SDK users. Figures are typical and approximate for
> HD3 probes and may change between software releases. Applies to released HD3 probes.

This note explains what limits the frame rate and data volume when acquiring **beamformed RF**
data (one summed RF trace per scan line) on Clarius HD3 probes through the low‑level SDK, and how
to trade field of view, resolution, and depth for higher frame rate or longer captures.

For how to *capture* and *stream* RF, see [in-app-tools.md](in-app-tools.md); for the on‑disk RF
binary layout, see [raw-data-format.md](raw-data-format.md).

---

## 1. Key principles

- **There is no fixed frame‑rate ceiling.** The frame‑rate *limit* control accepts `0` to mean
  "no software cap"; with no cap the achieved rate is set purely by physics and data handling.
  Values such as "100 Hz" in an SDK field are the maximum *explicit* limit you can request, not a
  ceiling on what the hardware can reach — set the limit to `0` for unlimited.
- **Acquisition rate is time‑of‑flight bound.** Each transmit/receive event must wait for echoes
  to return from the deepest sample. Frame rate therefore scales with **imaging depth** and the
  **number of transmit events per frame** (≈ scan lines ÷ multi‑line factor).
- **For RF, the practical limit is usually data offload, not the frame rate.** Beamformed RF is
  uncompressed 16‑bit data and is large. Sustained real‑time streaming is bandwidth‑limited, and
  high‑rate bursts are bounded by the on‑probe capture buffer (see §6).
- **Acoustic output and thermal limits still apply** and behave differently from frame rate — see §2.

**Beamformed RF vs. raw channel data:** beamformed RF applies dynamic receive focusing and outputs
one RF line per scan line. Raw per‑channel data (no receive beamforming) is a different, much larger
acquisition mode and is not covered here.

---

## 2. Acoustic output & thermal safety — MI, TI, and probe heating

Three distinct limits apply, and they respond very differently to frame rate. Read this before
raising frame rate, line density, or capture duration.

- **MI (Mechanical Index)** — a **per‑pulse** metric (peak rarefactional pressure), set by transmit
  voltage and pulse shape. It is essentially **independent of frame rate**. Low‑voltage / low‑MI
  operation (e.g. MI < 0.21) limits per‑pulse mechanical bioeffects but says nothing about
  time‑averaged heating.
- **TI (Thermal Index)** and time‑averaged intensity (e.g. I<sub>SPTA</sub>) — **time‑averaged**
  metrics that scale with the acoustic power delivered per unit time, i.e. with **frame rate, line
  rate, transmit aperture/voltage, and duty cycle**. **Raising the frame rate raises TI even when MI
  is unchanged.** A low‑MI sequence run at a high frame rate can still produce a high TI /
  time‑averaged intensity.
- **Probe self‑heating** — a device‑safety limit on the transducer / patient‑contact temperature,
  enforced by an automatic freeze if the probe gets too hot. It protects the device and contact
  surface; it is **not** a substitute for acoustic‑output (TI) compliance, and at low transmit
  voltage it typically does not bind for short acquisitions.

> ⚠️ **Safety — we cannot guarantee TI at elevated frame rates.** Clarius characterizes and regulates the
> acoustic output (MI and TI) of its **standard clinical presets** to within the applicable limits.
> **Custom low‑level / research sequences — particularly at elevated frame rates, high line
> densities, or during continuous acquisition — operate outside those characterized points, and
> Clarius does not guarantee MI, TI, or time‑averaged intensity in those modes.** Verifying acoustic
> output and thermal safety for a specific sequence, probe, and application is the researcher's
> responsibility.

**Ophthalmic use:** the eye is subject to substantially lower acoustic‑output limits than general
imaging. Because TI and time‑averaged intensity rise with frame rate, a high‑frame‑rate sequence can
exceed ophthalmic thermal limits **even at low MI**. Ocular acquisition parameters must be
independently verified against ophthalmic limits — do not assume that low MI alone keeps a high‑rate
sequence within ophthalmic thermal limits.

---

## 3. Per‑line timing and data vs. depth

The table below is **probe‑independent** (HD3, 60 MHz receive clock, sound speed 1540 m/s). It gives,
per scan line: round‑trip time of flight, the minimum per‑line time (time of flight + ~30 µs fixed
overhead), the maximum sustainable transmit‑event rate, and the RF sample count / size **at the full
60 MHz sampling rate**.

The last two columns are example **frame rates** without multi‑line acquisition, for a full‑FOV
linear‑probe RF frame (≈192 RF lines) and a PA2 frame (160 lines). Multiply by the multi‑line factor
(e.g. ×4) and/or scale by (reference lines ÷ your lines) for other configurations.

| Depth (mm) | Round‑trip ToF (µs) | Min per‑line (µs) | Max events/s | Samples/line @60 MHz | KB/line (int16) | fps @192 lines | fps @160 lines |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10  | 13.0  | 43.0  | 23,300 | 780    | 1.5  | 121 | 145 |
| 20  | 26.0  | 56.0  | 17,900 | 1,560  | 3.0  | 93  | 112 |
| 30  | 39.0  | 69.0  | 14,500 | 2,340  | 4.6  | 76  | 91  |
| 40  | 51.9  | 81.9  | 12,200 | 3,120  | 6.1  | 64  | 76  |
| 50  | 64.9  | 94.9  | 10,500 | 3,900  | 7.6  | 55  | 66  |
| 60  | 77.9  | 107.9 | 9,270  | 4,675  | 9.1  | 48  | 58  |
| 70  | 90.9  | 120.9 | 8,270  | 5,455  | 10.7 | 43  | 52  |
| 80  | 103.9 | 133.9 | 7,470  | 6,234  | 12.2 | 39  | 47  |
| 90  | 116.9 | 146.9 | 6,810  | 7,013  | 13.7 | 35  | 43  |
| 100 | 129.9 | 159.9 | 6,260  | 7,792  | 15.2 | 33  | 39  |
| 110 | 142.9 | 172.9 | 5,790  | 8,571  | 16.7 | 30  | 36  |
| 120 | 155.8 | 185.8 | 5,380  | 9,351  | 18.3 | 28  | 34  |
| 130 | 168.8 | 198.8 | 5,030  | 10,130 | 19.8 | 26  | 31  |
| 140 | 181.8 | 211.8 | 4,720  | 10,909 | 21.3 | 25  | 30  |
| 150 | 194.8 | 224.8 | 4,450  | 11,688 | 22.8 | 23  | 28  |
| 160 | 207.8 | 237.8 | 4,205  | 12,468 | 24.4 | 22  | 26  |
| 170 | 220.8 | 250.8 | 3,990  | 13,247 | 25.9 | 21  | 25  |
| 180 | 233.8 | 263.8 | 3,790  | 14,026 | 27.4 | 20  | 24  |
| 190 | 246.8 | 276.8 | 3,610  | 14,805 | 28.9 | 19  | 23  |
| 200 | 259.7 | 289.7 | 3,450  | 15,584 | 30.4 | 18  | 22  |
| 210 | 272.7 | 302.7 | 3,300  | 16,364 | 32.0 | 17  | 21  |
| 220 | 285.7 | 315.7 | 3,170  | 17,143 | 33.5 | 17  | 20  |
| 230 | 298.7 | 328.7 | 3,040  | 17,922 | 35.0 | 16  | 19  |
| 240 | 311.7 | 341.7 | 2,930  | 18,701 | 36.5 | 15  | 18  |
| 250 | 324.7 | 354.7 | 2,820  | 19,481 | 38.0 | 15  | 18  |
| 260 | 337.7 | 367.7 | 2,720  | 20,260 | 39.6 | 14  | 17  |
| 270 | 350.6 | 380.6 | 2,630  | 21,039 | 41.1 | 14  | 16  |
| 280 | 363.6 | 393.6 | 2,540  | 21,818 | 42.6 | 13  | 16  |
| 290 | 376.6 | 406.6 | 2,460  | 22,597 | 44.1 | 13  | 15  |
| 300 | 389.6 | 419.6 | 2,380  | 23,377 | 45.7 | 12  | 15  |

> **Sampling‑rate note:** the sample counts above assume the full 60 MHz rate. The RF sampling rate
> (decimation) is **chosen automatically by the system for the imaging depth** — beyond roughly
> **40 mm** it is reduced to keep data volume within the probe's buffer/FIFO limits, so actual
> samples/line and KB/line beyond ~40 mm are **lower** than shown. Treat the deep‑depth figures as an
> undecimated upper bound; the sampling rate is not a recommended manual tuning parameter (see §7).

**Frame‑rate formula:**

```
frame rate  ≈  (max events/s from table)  ×  MLA  ÷  (scan lines in your frame)
```

where `MLA` is the multi‑line (parallel receive) factor (1, 4, …) and scan lines scale with your
lateral field of view.

---

## 4. Probe reference — 192‑element probes

All HD3 probes below have **192 elements**, a **64‑element transmit / 32‑element receive** aperture,
and a **60 MHz** receive clock. Scan‑line count sets the maximum lateral sampling (and hence the
per‑frame transmit‑event count at full field of view).

| Probe | Array | Pitch (µm) | Aperture width (mm) | Max scan lines | Center freq (range) |
|---|---|---:|---:|---:|---|
| L20 HD3 | Linear | 130 | 25.0 | 384 | 14 MHz (8–20) |
| L15 HD3 | Linear | 260 | 49.9 | 384 | 10 MHz (5–15) |
| L7 HD3  | Linear | 200 | 38.4 | 384 | 7.5 MHz |
| EC7 HD3 | Curved (endocavity) | 150 | — | 384 | 6.5 MHz |
| C7 HD3  | Curved | 205 | — | 256 | 6 MHz |
| C3 HD3  | Curved | 300 | — | 192 | 3.5 MHz |
| PH HD3  | Curved | 300 | — | 192 | 5 MHz |

(Curved‑array "aperture width" is an arc and is omitted.)

## 5. Probe reference — phased‑array and PAL probes

These probes use the same **64‑element transmit / 32‑element receive** aperture and **60 MHz** receive
clock as the linear/curved family.

| Probe | Array | Elements | Pitch (µm) | Max scan lines | Center freq (range) |
|---|---|---:|---:|---:|---|
| PA2 HD3 | Phased (sector) | 80 | 250 | 160 | 2.4 MHz (1–5) |
| PAL HD3 — phased side | Phased (sector) | 80 | 260 | 160 | 2.4 MHz (1–5) |
| PAL HD3 — linear side | Linear | 112 | 260 | 224 | 10 MHz (5–15) |

**PAL is a dual‑array probe:** an 80‑element phased (sector) array for deep cardiac‑style imaging
(equivalent to PA2) plus a separate 112‑element linear array (10 MHz). Use the relevant array's row
above for the frame‑rate / data math in §3 and §6.

---

## 6. Data volume, buffering, and streaming

RF frame size and data rate:

```
KB/frame   =  (KB/line from §3)  ×  (scan lines in frame)
data rate  =  KB/frame  ×  frame rate
```

Example at 35 mm depth, full 60 MHz sampling (≈5.3 KB/line):

| Field of view | RF lines | KB/frame | @ 20 Hz | @ 70 Hz | @ 200 Hz |
|---|---:|---:|---:|---:|---:|
| ~25 mm (linear, full) | 192 | ~1,020 | 20 MB/s | 70 MB/s | 200 MB/s |
| ~12 mm (half FOV)     | 96  | ~510   | 10 MB/s | 35 MB/s | 100 MB/s |

Two limits govern how much of this you can actually move:

- **On‑probe capture buffer (~128 MB):** high‑rate bursts are captured here, then offloaded. At the
  data rates above this holds only **~0.5–2 s** at high frame rates. Because reducing the field of
  view shrinks each frame but proportionally raises the achievable frame rate, the **data rate stays
  roughly constant at maximum frame rate**, so trimming the FOV buys frame rate, not capture length.
- **Real‑time streaming:** the live RF stream is throttled well below the acquisition rate; sustained
  transfer of full‑rate RF over the wireless link is not possible at high frame rates.

**To extend capture length you must lower the data rate**, via any of:
- run at a lower frame rate,
- reduce imaging depth,
- reduce the field of view / line count.

(The RF sampling rate is already optimized automatically for the depth within the probe's buffer/FIFO
limits — it is not a recommended manual adjustment; see §3 and §7.)

---

## 7. Levers to raise frame rate (and their cost)

| Lever | Effect | Cost |
|---|---|---|
| Reduce field of view (`sector`) | Fewer scan lines → higher frame rate | Narrower image |
| Multi‑line acquisition (MLA) | N receive lines per transmit → up to ×N frame rate | Lateral resolution / MLA artifacts |
| Lower line density | Fewer scan lines → higher frame rate | Coarser lateral sampling |
| Reduce imaging depth | Shorter time of flight per line | Shallower image |

Notes:
- Transmit **aperture size** affects image quality (focusing/penetration) only — it does **not**
  change the number of transmit events, so it does not change frame rate.
- **RF sampling rate / decimation is not a recommended manual lever.** The system computes the
  optimal decimation for the imaging depth and must respect the probe's buffer/FIFO limits; overriding
  it is generally not supported and can violate those limits.
- Several of these levers raise the time‑averaged acoustic power and therefore the Thermal Index —
  review §2 before pushing frame rate, line density, or duration.
