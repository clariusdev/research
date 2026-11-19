# Low-Level Parameters

Beyond the standard imaging controls (depth, gain, PRF, …), Clarius scanners expose a set
of **low-level parameters** for fine acoustic and signal-processing control. They are
intended for research and device bring-up.

> ⚠️ **Safety.** These parameters bypass the optimized presets that the App and SDKs
> normally manage for you. Changing them can alter the **acoustic output** of the
> transducer and push imaging **outside the safety limits Clarius validates**, degrade
> image quality, or destabilize the system. Parameters marked **\*\*** directly affect
> acoustic output. Use appropriate test equipment and stay within your regulatory
> obligations. Separate licensing may be required.

## How to set them

The same parameter set is reachable from both research-facing APIs:

**Cast API** ([clariusdev/cast](https://github.com/clariusdev/cast)) — requires the
Clarius App running and connected:

```c
castSetParameter("txFreq", 5.0, returnFn);    // numeric
castEnableParameter("sa", 1, returnFn);       // boolean
castSetPulse("txPulseGen", "+-", returnFn);   // transmit pulse shape
```

**Solum SDK** ([clariusdev/solum](https://github.com/clariusdev/solum)) — connects to the
probe directly (OEM):

```c
solumSetLowLevelParam("txFreq", 5.0);
solumEnableLowLevelParam("sa", 1);
solumSetLowLevelPulse("txPulseGen", "+-");
double v = solumGetLowLevelParam("txFreq");   // booleans read back as 0/1
```

Parameter names and semantics are identical across both. The lists below are the
supported, publicly accessible low-level parameters; they are not exhaustive of every
internal sequencing knob, and ranges vary by probe and preset.

## Numeric parameters

### Generic

| Parameter | Meaning |
|-----------|---------|
| `maxFrameRate` | Frame-rate limit in Hz (0–100, `0` = no limit). |

### Greyscale

| Parameter | Meaning |
|-----------|---------|
| `txFreq` ** | Transmit frequency (MHz). |
| `txFreqInv` ** | Transmit frequency for the inversion pulse (MHz). |
| `txFn` ** | Transmit f-number. |
| `txApt` ** | Maximum transmit aperture in elements (2–64). |
| `txFocus` ** | Focus depth (cm). |
| `vpp` ** | Positive amplitude (V, 10–37). |
| `vnn` ** | Negative amplitude (V, 10–37). |
| `ceVpp` ** | Positive amplitude for CEUS (V, 10–37). |
| `ceVnn` ** | Negative amplitude for CEUS (V, 10–37). |
| `steer` ** | Image steering (degrees). |
| `rxFn` | Receive f-number. |
| `rxFreqShallow` | Start demodulation frequency (MHz). |
| `rxFreqDeep` | End demodulation frequency (MHz). |
| `speedOfSound` | Speed-of-sound correction (m/s). |
| `iqDecimation` | Decimation factor used for IQ data. |
| `envDecimation` | Decimation factor used for envelope/grayscale data. |
| `dyn` | Dynamic range (dB). |
| `nf` | Noise floor (dB). |

### RF

These apply to the RF stream (the QUS preset, or RF in the Research preset).

| Parameter | Meaning |
|-----------|---------|
| `rfTxFreq` ** | RF transmit frequency (MHz). |
| `rfFocus` ** | RF transmit focus depth (cm). |
| `rfTgc` | RF analog gain (dB), flat at all depths. Default 20 dB; the usable range is 5–40 dB, and values outside it act as the nearest limit. The App's TGC sliders, Gain and auto gain do not affect RF. |
| `rfDecimation` | RF decimation factor. The sampling rate is the probe's receive clock divided by this (60 MHz on HD3), and is reported as `sampling rate` in each capture's `_rf.yml`. The presets choose it from imaging depth and skip 2, which shows a small artefact on every sample. |

A change to `rfTgc` takes effect within a frame or two without interrupting imaging. A
change to `rfFocus`, `rfTxFreq` or `rfDecimation` reloads the acquisition, so imaging
pauses briefly.

`rfFocus` and `rfDecimation` are calculated from the imaging depth by the presets. A value
you set overrides that calculation until one of its inputs changes, such as the imaging
depth, so set them again after a depth change. In the Breast preset the RF focus follows
the RF depth range and cannot currently be held at another value.

### Color / Power Doppler

| Parameter | Meaning |
|-----------|---------|
| `cfiPrf` ** | Pulse repetition frequency (kHz; range varies per probe/preset). |
| `cfiTxFreq` ** | Transmit frequency (MHz). |
| `color steer` | Steering angle (degrees). |
| `cfiEnsemble` ** | Ensemble / transmits per line (6–16). |

### Pulsed-Wave Doppler

| Parameter | Meaning |
|-----------|---------|
| `pwPrf` ** | Pulse repetition frequency (kHz; range varies per probe/preset). |
| `pwTxFreq` ** | Transmit frequency (MHz). |
| `pw gate size` | Gate size (mm). |
| `pw steer` | Steering angle (degrees). |
| `pw angle correct` | Correction angle (degrees). |

## Boolean parameters

### Greyscale

| Parameter | Meaning |
|-----------|---------|
| `sa` | Synthetic aperture. |
| `pih` | Pulse-inversion harmonics. |
| `trapezoidal` | Extended field of view for linear probes. |

## Pulse-shape (string) parameters

Set with `castSetPulse` / `solumSetLowLevelPulse`. The shape string encodes the transmit
waveform (e.g. `+-`, `+-+-+-+-`).

| Parameter | Meaning |
|-----------|---------|
| `txPulseGen` ** | Transmit pulse. |
| `txPulsePen` ** | Transmit pulse when penetration mode is active. |
| `txPulseInv` ** | Transmit pulse for the inversion pulse. |
| `cfiPulse` ** | Color/power transmit pulse. |
| `pwPulse` ** | PW transmit pulse. |

---

** Changing this parameter may alter the acoustic output of the transducer, making
imaging operate outside the safety parameters Clarius has programmed into the device.
