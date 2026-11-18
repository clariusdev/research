"""Scan convert Clarius raw data (envelope, RF or IQ) to a Cartesian image.

Each line of a .raw starts at its receive element on the array and runs at its steering angle, as listed under
`lines` in the .yml. A sample's depth along its line is (delay samples + sample) / sampling rate * c / 2. On a
curved array, element e sits at pitch * (e - (elements - 1) / 2) / radius radians around the arc, and a line's
steering adds to that angle. On a linear or phased array, element e sits at pitch * (e - (elements - 1) / 2) mm
across. Every output pixel is traced back to a fractional line and sample, and interpolated bilinearly.

Probe geometry comes from the .yml's probe block (13.1 and later); --elements, --pitch and --radius override it
and are needed for older files. Sample timing includes the trip through the lens, so depth is measured from the
lens face, as on the App's depth scale, by taking off the probe's lens thickness (--lens, 0 to measure from the
elements).

As a library:
    meta, hdr, data = scanconvert.load("../../data/convex/convex_rf.raw")
    convert = scanconvert.converter(meta, hdr["samples"])
    image = convert(scanconvert.bmode(meta["type"], data[:, :, 0]))   # extent in mm: convert.extent_mm

From the command line (writes a PNG per frame; needs Pillow):
    python scanconvert.py ../../data/convex/convex_env.raw --frames all
    python scanconvert.py ../../data/linear/linear_rf.raw --dynamic-range 50 --pixel 0.05
    python scanconvert.py old_capture_env.raw --elements 192 --pitch 300 --radius 45
"""

import argparse
import os
import re

import numpy as np

import rdataread as rd


def _number(text, pattern, default=None):
    match = re.search(pattern, text, re.MULTILINE)
    return float(match.group(1)) if match else default


def read_meta(path):
    """Reads what scan conversion needs from a .yml: data type, sampling, lines, and the probe block if any."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    lines = []
    for entry in re.findall(r"^\s*-\s*\{([^}]*rx element[^}]*)\}", text, re.MULTILINE):
        lines.append((_number(entry, r"rx element:\s*([-+\d.eE]+)"), _number(entry, r"angle:\s*([-+\d.eE]+)", 0.0)))
    if len(lines) < 2:
        raise ValueError(f"{path} lists fewer than two lines")
    type_match = re.search(r"^type:\s*(.+)$", text, re.MULTILINE)
    probe_match = re.search(r"^probe:\s*\n((?:[ \t]+.*\n?)+)", text, re.MULTILINE)
    probe = {}
    if probe_match:
        block = probe_match.group(1)
        probe = {
            "elements": _number(block, r"^\s*elements:\s*([\d.]+)"),
            "pitch": _number(block, r"^\s*pitch:\s*([\d.]+)"),
            "radius": _number(block, r"^\s{2}radius:\s*([\d.]+)", 0.0),
            "lens": _number(block, r"^\s*lens thickness:\s*([\d.]+)", 0.0),
            "v1": bool(re.search(r"^\s*version:\s*v?1\b", block, re.MULTILINE)),
        }
    return {
        "type": type_match.group(1).strip().lower() if type_match else "",
        "sampling_mhz": _number(text, r"^sampling rate:\s*([\d.]+)"),
        "delay_samples": _number(text, r"^delay samples:\s*([-\d.]+)", 0.0),
        "vsound": _number(text, r"^(?:vsound|speed of sound)[^:]*:\s*([\d.]+)"),
        "rx": np.array([rx for rx, _ in lines]),
        "angle_deg": np.array([angle for _, angle in lines]),
        "probe": probe,
    }


def load(raw_path, yml_path=None):
    """Reads a .raw with the reader its .yml's type names; returns (meta, header, data indexed [line, sample, frame])."""
    meta = read_meta(yml_path or os.path.splitext(raw_path)[0] + ".yml")
    kind = meta["type"]
    if kind.startswith("rf"):
        hdr, _, data = rd.read_rf(raw_path)
    elif kind.startswith("iq"):
        hdr, _, data = rd.read_iq(raw_path)
    else:
        hdr, _, data = rd.read_env(raw_path)
    if len(meta["rx"]) != hdr["lines"]:
        raise ValueError(f"the .yml lists {len(meta['rx'])} lines but the .raw has {hdr['lines']}")
    return meta, hdr, data


def line_rays(rx, angle_deg, elements, pitch_um, radius_mm, flip=1):
    """Returns each line's start (x, z in mm, z down from the array's centre element) and direction (radians from +z).

    A curved array's centre of curvature is above it, so its outer elements sit higher than its centre one.
    """
    half = (elements - 1) / 2.0
    offset_mm = flip * (rx - half) * pitch_um / 1000.0
    steer = np.radians(angle_deg)
    if radius_mm > 0:
        theta = offset_mm / radius_mm
        return radius_mm * np.sin(theta), radius_mm * (np.cos(theta) - 1), theta + flip * steer
    return offset_mm, np.zeros_like(offset_mm), flip * steer


class ScanConverter:
    """Maps a lines x samples frame onto a Cartesian grid; the mapping is built once and reused per frame."""

    def __init__(self, ox, oz, phi, samples, sampling_mhz, delay_samples, vsound=1540.0, pixel_mm=0.1):
        self.lines = len(ox)
        self.samples = samples
        mm_per_sample = vsound / (2.0 * sampling_mhz * 1000.0)
        r_min = delay_samples * mm_per_sample
        r_max = (delay_samples + samples - 1) * mm_per_sample

        # bounds from the frame's outline, sampled along every line
        r = np.linspace(r_min, r_max, 32)[None, :]
        xs = ox[:, None] + r * np.sin(phi)[:, None]
        zs = oz[:, None] + r * np.cos(phi)[:, None]
        self.x = np.arange(xs.min(), xs.max() + pixel_mm, pixel_mm)
        self.z = np.arange(zs.min(), zs.max() + pixel_mm, pixel_mm)
        px, pz = np.meshgrid(self.x, self.z)

        # the signed distance from a pixel to a line changes sign once across the lines, so bisect for the line
        index = np.arange(self.lines, dtype=float)

        def side(t):
            a = np.interp(t, index, phi)
            return (px - np.interp(t, index, ox)) * np.cos(a) - (pz - np.interp(t, index, oz)) * np.sin(a)

        lo = np.zeros(px.shape)
        hi = np.full(px.shape, self.lines - 1.0)
        f_lo, f_hi = side(lo), side(hi)
        inside = f_lo * f_hi <= 0
        for _ in range(24):
            mid = (lo + hi) / 2
            f_mid = side(mid)
            left = np.sign(f_mid) == np.sign(f_lo)
            lo = np.where(left, mid, lo)
            f_lo = np.where(left, f_mid, f_lo)
            hi = np.where(left, hi, mid)
        t = (lo + hi) / 2

        a = np.interp(t, index, phi)
        depth = (px - np.interp(t, index, ox)) * np.sin(a) + (pz - np.interp(t, index, oz)) * np.cos(a)
        s = depth / mm_per_sample - delay_samples
        self.valid = inside & (s >= 0) & (s <= samples - 1)
        self.t = np.where(self.valid, t, 0)
        self.s = np.where(self.valid, s, 0)

    @property
    def extent_mm(self):
        """(left, right, bottom, top) of the image in mm, as matplotlib's imshow takes it."""
        return self.x[0], self.x[-1], self.z[-1], self.z[0]

    def __call__(self, frame, fill=0.0):
        """Converts one frame indexed [line, sample]."""
        frame = np.asarray(frame, dtype=float)
        l0 = np.clip(np.floor(self.t).astype(int), 0, self.lines - 2)
        s0 = np.clip(np.floor(self.s).astype(int), 0, self.samples - 2)
        wl = self.t - l0
        ws = self.s - s0
        out = ((1 - wl) * (1 - ws) * frame[l0, s0] + wl * (1 - ws) * frame[l0 + 1, s0]
               + (1 - wl) * ws * frame[l0, s0 + 1] + wl * ws * frame[l0 + 1, s0 + 1])
        return np.where(self.valid, out, fill)


def converter(meta, samples, pixel_mm=0.1, elements=None, pitch=None, radius=None, lens=None, flip=False,
              vsound=None):
    """Builds the converter for a .raw from its metadata; the arguments given override the .yml's probe block."""
    probe = meta["probe"]
    elements = int(elements or probe.get("elements") or 0)
    pitch = pitch or probe.get("pitch")
    if not elements or not pitch:
        raise ValueError("the .yml has no probe block; give elements and pitch (and radius for a curved array)")
    radius = radius if radius is not None else probe.get("radius", 0.0)
    lens = lens if lens is not None else probe.get("lens", 0.0)
    sign = -1 if flip or probe.get("v1") else 1
    ox, oz, phi = line_rays(meta["rx"], meta["angle_deg"], elements, pitch, radius, sign)
    convert = ScanConverter(ox, oz - lens, phi, samples, meta["sampling_mhz"], meta["delay_samples"],
                            vsound or meta["vsound"] or 1540.0, pixel_mm)
    convert.description = (f"{'curved' if radius > 0 else 'linear'} array, {elements} elements, {pitch:g} µm pitch"
                           + (f", {radius:g} mm radius" if radius > 0 else "")
                           + (f", {lens:g} mm lens" if lens else ""))
    return convert


def envelope_db(rf):
    """Envelope of RF lines (last axis is samples) in dB, through the analytic signal."""
    n = rf.shape[-1]
    spectrum = np.fft.fft(rf, axis=-1)
    h = np.zeros(n)
    h[0] = 1
    h[1:(n + 1) // 2] = 2
    if n % 2 == 0:
        h[n // 2] = 1
    return 20 * np.log10(np.abs(np.fft.ifft(spectrum * h, axis=-1)) + 1)


SPECKLE_GRAY = 0.12  # where the median (speckle) sits between black and white, as on the App's B image


def to_gray(db, dynamic_range, anchor="speckle"):
    """Maps dynamic_range dB of a frame to 0..255.

    With anchor "speckle" the frame's median sits at a low grey and the range runs up from there, so the image's
    brightness does not depend on its brightest reflector; with "peak" the range runs down from the 99.9th percentile.
    """
    if anchor == "peak":
        black = np.percentile(db, 99.9) - dynamic_range
    else:
        black = np.median(db) - SPECKLE_GRAY * dynamic_range
    return np.clip((db - black) / dynamic_range, 0, 1) * 255


def _without_dc(lines):
    return lines - lines.mean(axis=-1, keepdims=True)


def bmode(kind, lines, dynamic_range=50, anchor="speckle"):
    """B image of one frame [line, sample] of the given .yml type: RF and IQ log compressed, envelope as it is.

    Each line's DC offset is removed from RF, and from I and Q, before detection.
    """
    lines = np.asarray(lines, dtype=float)
    if kind.startswith("rf"):
        return to_gray(envelope_db(_without_dc(lines)), dynamic_range, anchor)
    if kind.startswith("iq"):
        i, q = _without_dc(lines[:, 0::2]), _without_dc(lines[:, 1::2])
        return to_gray(10 * np.log10(i ** 2 + q ** 2 + 1), dynamic_range, anchor)
    return lines


def parse_frames(spec, count):
    if spec == "all":
        return list(range(count))
    frames = []
    for part in spec.split(","):
        first, _, last = part.partition("-")
        frames.extend(range(int(first), int(last or first) + 1))
    return [f for f in frames if 0 <= f < count]


def main():
    from PIL import Image

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw", help=".raw file (envelope, RF or IQ)")
    parser.add_argument("--yml", help="metadata file (default: the .raw's name with .yml)")
    parser.add_argument("--elements", type=int, help="element count")
    parser.add_argument("--pitch", type=float, help="element pitch in µm")
    parser.add_argument("--radius", type=float, help="array radius in mm; 0 for linear and phased arrays")
    parser.add_argument("--flip", action="store_true", help="elements count right to left, as on V1 scanners")
    parser.add_argument("--lens", type=float, help="lens thickness in mm taken off depth (default: the .yml's, else 0)")
    parser.add_argument("--vsound", type=float, help="speed of sound in m/s (default: the .yml's, else 1540)")
    parser.add_argument("--pixel", type=float, default=0.1, help="output pixel size in mm (default 0.1)")
    parser.add_argument("--frames", default="0", help="'all', or frames such as 0,3,5-9 (default 0)")
    parser.add_argument("--dynamic-range", type=float, default=50, help="displayed dB for RF and IQ (default 50)")
    parser.add_argument("--anchor", choices=("speckle", "peak"), default="speckle",
                        help="place RF and IQ's range from the median speckle up (default) or from the peak down")
    parser.add_argument("--out", help="output folder (default: beside the .raw)")
    parser.add_argument("--npz", action="store_true", help="also save each converted frame as .npz with its mm axes")
    args = parser.parse_args()

    meta, hdr, data = load(args.raw, args.yml)
    try:
        convert = converter(meta, hdr["samples"], args.pixel, args.elements, args.pitch, args.radius, args.lens,
                            args.flip, args.vsound)
    except ValueError as e:
        parser.error(str(e))
    left, right, bottom, top = convert.extent_mm
    print(f"{convert.description}; image {right - left:.1f} x {bottom - top:.1f} mm at {args.pixel:g} mm/pixel"
          f" (x {left:.1f} to {right:.1f}, z {top:.1f} to {bottom:.1f})")

    out_dir = args.out or os.path.dirname(os.path.abspath(args.raw))
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.raw))[0]
    for frame in parse_frames(args.frames, hdr["frames"]):
        image = convert(bmode(meta["type"], data[:, :, frame], args.dynamic_range, args.anchor))
        path = os.path.join(out_dir, f"{stem}_sc_{frame:04d}.png")
        Image.fromarray(np.round(image).astype(np.uint8)).save(path)
        if args.npz:
            np.savez(os.path.join(out_dir, f"{stem}_sc_{frame:04d}.npz"), image=image, x_mm=convert.x, z_mm=convert.z)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
