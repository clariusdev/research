"""Load and display the bundled Clarius raw data.

For each sample capture (a linear and a convex array) and each data type it holds (RF, IQ, envelope), shows the
first frame as recorded, in lines and samples, next to the same frame scan converted to millimetres.

Needs numpy and matplotlib.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(here, "..", "..", "common", "python"))
import scanconvert as sc  # noqa: E402

DATA = os.path.join(here, "..", "..", "data")
CAPTURES = ("linear", "convex")
TYPES = ("rf", "iq", "env")


def show(name, kind, path, frame=0):
    meta, hdr, data = sc.load(path)
    lines = data[:, :, frame]
    b = sc.bmode(meta["type"], lines)
    convert = sc.converter(meta, hdr["samples"])

    panels = 3 if kind in ("rf", "iq") else 2
    fig, axes = plt.subplots(1, panels, figsize=(5 * panels, 5))
    fig.suptitle(f"{name} {kind}, frame {frame}: {convert.description}")
    if kind == "rf":
        limit = np.percentile(np.abs(lines), 99)
        axes[0].imshow(lines.T, cmap="seismic", aspect="auto", vmin=-limit, vmax=limit)
        axes[0].set_title("RF")
    elif kind == "iq":
        magnitude = np.hypot(lines[:, 0::2], lines[:, 1::2])
        axes[0].imshow(magnitude.T, cmap="viridis", aspect="auto", vmax=np.percentile(magnitude, 99))
        axes[0].set_title("IQ magnitude")
    if kind in ("rf", "iq"):
        axes[0].set_xlabel("line")
        axes[0].set_ylabel("sample")
    axes[-2].imshow(b.T, cmap="gray", aspect="auto", vmin=0, vmax=255)
    axes[-2].set_title("B, pre-scan")
    axes[-2].set_xlabel("line")
    axes[-2].set_ylabel("sample")
    axes[-1].imshow(convert(b), cmap="gray", vmin=0, vmax=255, extent=convert.extent_mm)
    axes[-1].set_title("B, scan converted")
    axes[-1].set_xlabel("mm")
    axes[-1].set_ylabel("depth (mm)")
    axes[-1].set_facecolor("black")
    fig.tight_layout()


if __name__ == "__main__":
    for name in CAPTURES:
        for kind in TYPES:
            path = os.path.join(DATA, name, f"{name}_{kind}.raw")
            if os.path.exists(path):
                show(name, kind, path)
    plt.show()
