# In-App Research Tools

The Clarius App exposes research features for capturing raw data, streaming RF, and
emitting a hardware sync pulse. This page covers how to drive them from the App. For the
on-disk format of what you capture, see [raw-data-format.md](raw-data-format.md); for
programmatic low-level control, see [low-level-parameters.md](low-level-parameters.md).

## Capture modes

Raw data capture is toggled from the **modes menu**:

- **Buffer** — press the Buffer icon to have the scanner buffer raw data while imaging.

  ![Buffer Raw Data](../blob/buffer.png)

- **RF** — press the RF icon to engage internal RF frame capture while scanning in B
  mode. RF data is collected within the region-of-interest (ROI) placed over the
  grayscale image.

  ![RF Mode](../blob/rf.png)

What gets captured depends on whether RF mode is engaged:

- **RF off:** IQ and envelope data are captured by default.
- **RF on:** RF and envelope data are captured by default.

## RF streaming

RF streaming is enabled by default when RF mode is engaged, and is toggled with the
**Stream** icon.

![RF Stream](../blob/stream.png)

- While streaming is **on**, RF frames are interleaved every 3 B/grayscale frames, so RF
  streams (and buffers) at a lower frame rate than B.
- While streaming is **off**, RF frames are interleaved with *every* B frame, increasing
  the RF frame rate; capture is then governed by the buffering control only.
- Streamed RF is used **only** for visualization in the App and is not stored. However,
  if a client connects with the [Cast API](https://github.com/clariusdev/cast) while RF
  is streaming, the RF signals are automatically routed to that client.

## Downloading captured data

Once imaging is **frozen** with raw-data capture engaged, the capture-image or
capture-cine buttons automatically download the data from the scanner.

- Data is always packaged as a `.tar` using LZO compression internally. Ensure your OS
  has the right tools to decompress it (see [raw-data-format.md](raw-data-format.md)).
- Downloads over the wireless link take time: ~1–3 s for a single frame; up to a minute
  for cines of hundreds of frames. Wait for the on-screen progress to complete before
  imaging again.
- Buffers are sized for stable imaging: typically up to **10 s** of raw IQ/RF and up to
  **20 s** of raw envelope. The App can store a cine of up to **30 s**.
- **The downloaded raw data always corresponds to the latest frames in time.** If your
  cine markers select an early window (e.g. 0–10 s of a 20 s capture), it's possible no
  raw data is downloaded for that window.

## Accessing captured data

Once an exam is completed and submitted, raw data can be accessed via:

- **Clarius Cloud** — view the exam online and download the packaged `.tar` directly from
  a browser.

  ![Raw Data Download](../blob/raw_cloud.png)

- **Local export** — export the exam to device storage when ending the exam or from the
  Exams page. (As of App v8.6, iOS can also store non-image data to the file system.)

  ![Raw Data Export](../blob/save_device.png)

- **Cast API** — if available for the device, raw data can be downloaded by a custom
  C/C++ program with immediate access once it comes off the scanner. See the
  [Cast API raw data flow](https://github.com/clariusdev/cast/blob/master/docs/getting-started.md#6-capture-raw-data).

## Hardware sync output

The probe can emit a **3.3 V CMOS** sync signal from the pins on its rear, marking the
start of each frame acquisition. Pin 9 outputs the signal; pins 5 and 8 are ground. The
HD3 fan CAD can be used as a basis for a custom connector that routes the pulse to a BNC.

To enable it, open the **research menu** and press the **Sync** button (two circular
arrows). The signal is output at the start of each frame.

> Clarius' ultrasound sequencing is semi-asynchronous with respect to frame acquisition:
> the interval between frames is not exactly constant, but is generally within 1 ms.

![Pin Output](../blob/pins.png)

The transmit/receive timing relationship:

![Tx Rx Timing](../blob/TxRx_timing.png)

A scope capture of the single-ended 3.3 V CMOS sync pulse:

![Sync Pulse](../blob/sync_pulse.png)
