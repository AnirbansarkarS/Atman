"""EEG graph generators — all 4 tab types, dark-themed matplotlib plots."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, must be before pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import mne

import brain_loader

# Output dir
GRAPH_DIR = Path(__file__).resolve().parent / "generated_graphs"
GRAPH_DIR.mkdir(exist_ok=True)

# Dark style for all plots
DARK_BG = "#0a0e1a"
ACCENT   = "#7C6FFF"
LINE_CLR = "#a78bfa"
TEXT_CLR = "#c4c9e2"

_STYLE = {
    "figure.facecolor": DARK_BG,
    "axes.facecolor":   "#0f1525",
    "axes.edgecolor":   "#2a2f50",
    "axes.labelcolor":  TEXT_CLR,
    "xtick.color":      TEXT_CLR,
    "ytick.color":      TEXT_CLR,
    "grid.color":       "#1e2540",
    "text.color":       TEXT_CLR,
    "lines.color":      LINE_CLR,
    "figure.dpi":       100,
}


def _apply_style():
    plt.rcParams.update(_STYLE)


# --------------------------------------------------------------------------- #
# EEG Raster                                                                  #
# --------------------------------------------------------------------------- #
def generate_eeg_raster(raw: mne.io.BaseRaw, subject: str = "01") -> Path:
    _apply_style()
    n_channels = min(12, raw.info["nchan"])
    duration   = min(5.0, raw.times[-1])
    n_samples  = int(duration * raw.info["sfreq"])

    data, times = raw[:n_channels, :n_samples]
    data *= 1e6  # V → µV

    fig, ax = plt.subplots(figsize=(10, 6))
    spacing = np.max(np.abs(data)) * 1.5 or 100

    for i, row in enumerate(data):
        ax.plot(times, row - i * spacing, color=LINE_CLR, lw=0.6, alpha=0.9)
        ax.text(
            -0.01, -i * spacing, raw.ch_names[i],
            ha="right", va="center", fontsize=7, color=TEXT_CLR,
            transform=ax.get_yaxis_transform(),
        )

    ax.set_xlim(0, duration)
    ax.set_xlabel("Time (s)")
    ax.set_yticks([])
    ax.set_title(f"EEG Raster  ·  sub-{subject}  ·  first {duration:.0f}s", pad=12)
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()

    path = GRAPH_DIR / f"raster_sub-{subject}.png"
    fig.savefig(path, facecolor=DARK_BG)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Power Spectrum (PSD)                                                        #
# --------------------------------------------------------------------------- #
def generate_psd_graph(raw: mne.io.BaseRaw, subject: str = "01") -> Path:
    _apply_style()
    spectrum = raw.compute_psd(method="welch", fmax=80, verbose=False)
    psds, freqs = spectrum.get_data(return_freqs=True)
    mean_psd = 10 * np.log10(psds.mean(axis=0) + 1e-30)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(freqs, mean_psd, color=ACCENT, lw=1.5)
    ax.fill_between(freqs, mean_psd, mean_psd.min(), alpha=0.15, color=ACCENT)

    for band, (lo, hi, clr) in {
        "δ": (0.5, 4,  "#60efff"),
        "θ": (4,   8,  "#4dffb0"),
        "α": (8,  13,  "#ffdd57"),
        "β": (13, 30,  "#ff9f43"),
        "γ": (30, 80,  "#ff6b9d"),
    }.items():
        ax.axvspan(lo, hi, alpha=0.07, color=clr, label=band)
        ax.text((lo + hi) / 2, ax.get_ylim()[0] + 1, band,
                ha="center", fontsize=8, color=clr)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (dB)")
    ax.set_title(f"Power Spectrum  ·  sub-{subject}  ·  mean across channels", pad=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = GRAPH_DIR / f"psd_sub-{subject}.png"
    fig.savefig(path, facecolor=DARK_BG)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Spectrogram                                                                 #
# --------------------------------------------------------------------------- #
def generate_spectrogram(raw: mne.io.BaseRaw, subject: str = "01") -> Path:
    _apply_style()
    # Pick the first EEG channel
    ch_idx = 0
    ch_name = raw.ch_names[ch_idx]
    data, times = raw[[ch_idx], :]
    signal = data[0]
    sfreq  = raw.info["sfreq"]

    # Limit to first 30 s for speed
    max_samples = int(30 * sfreq)
    signal = signal[:max_samples]

    from scipy import signal as sp_signal
    freqs, t, Sxx = sp_signal.spectrogram(
        signal, fs=sfreq, nperseg=int(sfreq), noverlap=int(sfreq * 0.75),
    )
    # Limit to 0-80 Hz
    freq_mask = freqs <= 80
    freqs, Sxx = freqs[freq_mask], Sxx[freq_mask, :]

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.pcolormesh(
        t, freqs, 10 * np.log10(Sxx + 1e-30),
        shading="gouraud", cmap="magma",
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Power (dB)", color=TEXT_CLR)
    cbar.ax.yaxis.set_tick_params(color=TEXT_CLR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_CLR)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(f"Spectrogram  ·  sub-{subject}  ·  ch {ch_name}", pad=12)
    fig.tight_layout()

    path = GRAPH_DIR / f"spectrogram_sub-{subject}.png"
    fig.savefig(path, facecolor=DARK_BG)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Topomap                                                                     #
# --------------------------------------------------------------------------- #
def generate_topomap(raw: mne.io.BaseRaw, subject: str = "01") -> Path:
    _apply_style()

    # Try to set a standard montage
    try:
        montage = mne.channels.make_standard_montage("standard_1020")
        raw_copy = raw.copy()
        raw_copy.set_montage(montage, on_missing="ignore", verbose=False)
        use_raw = raw_copy
    except Exception:
        use_raw = raw

    try:
        spectrum = use_raw.compute_psd(method="welch", fmax=30, verbose=False)
        psds, _ = spectrum.get_data(return_freqs=True)
        mean_power = psds.mean(axis=1)  # per-channel

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(6, 6))
            mne.viz.plot_topomap(
                mean_power,
                use_raw.info,
                axes=ax,
                show=False,
                cmap="plasma",
                vlim=(np.percentile(mean_power, 5), np.percentile(mean_power, 95)),
            )
            ax.set_title(f"Topomap · sub-{subject} · broad-band power", pad=12, color=TEXT_CLR)
            fig.patch.set_facecolor(DARK_BG)

        path = GRAPH_DIR / f"topomap_sub-{subject}.png"
        fig.savefig(path, facecolor=DARK_BG)
        plt.close(fig)
        return path

    except Exception as exc:
        # Fallback: heatmap-style synthetic topomap if channel positions missing
        print(f"[brain_graphs] Topomap fallback: {exc}")
        return _topomap_fallback(subject)


def _topomap_fallback(subject: str) -> Path:
    """Synthetic topomap placeholder when channel positions are unavailable."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    n = 64
    rng = np.random.default_rng(42)
    x, y = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    vals = rng.uniform(0, 1, n)

    ax.scatter(x, y, c=vals, cmap="plasma", s=180, zorder=3)
    circle = plt.Circle((0, 0), 1, fill=False, color=ACCENT, lw=1.5)
    ax.add_patch(circle)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Topomap (synthetic) · sub-{subject}", color=TEXT_CLR, pad=12)

    path = GRAPH_DIR / f"topomap_sub-{subject}.png"
    fig.savefig(path, facecolor=DARK_BG)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Dispatcher                                                                  #
# --------------------------------------------------------------------------- #
def generate_graph(graph_type: str = "eeg", subject: str = "01") -> Path | None:
    """Load EEG (uses cache) and generate the requested graph type."""
    try:
        info = brain_loader.load_raw_data(subject=subject)
        raw: mne.io.BaseRaw = info["raw"]

        dispatch = {
            "eeg":         generate_eeg_raster,
            "power":       generate_psd_graph,
            "spectrogram": generate_spectrogram,
            "topomap":     generate_topomap,
        }
        fn = dispatch.get(graph_type, generate_eeg_raster)
        return fn(raw, subject=subject)

    except Exception as exc:
        print(f"[brain_graphs] Error generating {graph_type}: {exc}")
        return None


if __name__ == "__main__":
    for t in ["eeg", "power", "spectrogram", "topomap"]:
        p = generate_graph(t)
        print(f"{t}: {p}")
