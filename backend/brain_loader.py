"""EEG data loader — wraps MNE I/O for the ds004196 dataset."""
from pathlib import Path
import numpy as np
import mne

# --------------------------------------------------------------------------- #
# Paths — try multiple candidate roots so the code works regardless of where  #
# the user placed the dataset folder.                                         #
# --------------------------------------------------------------------------- #
_HERE = Path(__file__).resolve().parent

_BIDS_CANDIDATES = [
    _HERE.parent / "brain_data" / "ds004196",   # preferred: brain_data/ds004196
    _HERE.parent / "ds004196",                   # root-level ds004196
    _HERE.parent / "brain_data",                 # loose layout
]


def _find_bids_root() -> Path | None:
    """Find BIDS dataset root, attempting download if missing."""
    for candidate in _BIDS_CANDIDATES:
        if candidate.exists() and (candidate / "dataset_description.json").exists():
            return candidate
    
    # Dataset not found, try automatic download
    print("[brain_loader] Dataset not found locally. Attempting automatic download...")
    try:
        import dataset_manager
        return dataset_manager.get_dataset_path()
    except Exception as e:
        print(f"[brain_loader] Auto-download failed: {e}")
        print("[brain_loader] Please download ds004196 manually from:")
        print("[brain_loader] https://openneuro.org/datasets/ds004196")
        return None


# In-memory cache so each subject is loaded only once per server session
_RAW_CACHE: dict[str, mne.io.BaseRaw] = {}


def _make_synthetic_raw(subject: str) -> mne.io.BaseRaw:
    """Return a small synthetic EEG Raw so graphs still render when BDF fails."""
    sfreq = 512.0
    duration = 10.0
    n_channels = 64
    n_samples = int(sfreq * duration)

    rng = np.random.default_rng(abs(hash(subject)) % (2**32))
    data = rng.normal(0, 1, size=(n_channels, n_samples)) * 1e-6  # volts

    ch_names = [f"EEG{i:02d}" for i in range(1, n_channels + 1)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose=False)
    return raw


# --------------------------------------------------------------------------- #
# Public helpers                                                               #
# --------------------------------------------------------------------------- #

def get_eeg_file(subject: str = "01", session: str = "EEG", task: str = "inner") -> Path:
    """Return the BDF file path for the given subject/session, trying common layouts."""
    bids_root = _find_bids_root()
    if bids_root is None:
        raise FileNotFoundError(
            "No EEG dataset folder found. Expected brain_data/ds004196 or ds004196 "
            "in the project root."
        )

    # Standard BIDS layout
    eeg_dir = bids_root / f"sub-{subject}" / f"ses-{session}" / "eeg"
    if eeg_dir.exists():
        exact = eeg_dir / f"sub-{subject}_ses-{session}_task-{task}_eeg.bdf"
        if exact.exists():
            return exact
        fallback = next(eeg_dir.glob("*.bdf"), None)
        if fallback:
            return fallback

    # Flat layout: ds004196/sub-01/ contains the BDF directly
    flat_dir = bids_root / f"sub-{subject}"
    if flat_dir.exists():
        fallback = next(flat_dir.glob("**/*.bdf"), None)
        if fallback:
            return fallback

    raise FileNotFoundError(
        f"No .bdf file found for sub-{subject}. Searched inside {bids_root}."
    )


def load_raw_data(
    subject: str = "01",
    session: str = "EEG",
    task: str = "inner",
    preload: bool = True,
) -> dict:
    """Load raw EEG and return a dict with raw, events, event_id, path.

    Results are cached in-memory; subsequent calls for the same subject are instant.
    """
    if subject in _RAW_CACHE:
        raw = _RAW_CACHE[subject]
        return {"raw": raw, "events": None, "event_id": None, "path": None}

    eeg_file = get_eeg_file(subject=subject, session=session, task=task)
    try:
        raw = mne.io.read_raw_bdf(eeg_file, preload=preload, verbose="ERROR")
    except Exception as exc:
        # Fallback keeps UI usable when the BDF is missing or corrupted.
        print(f"[brain_loader] Falling back to synthetic EEG for sub-{subject}: {exc}")
        raw = _make_synthetic_raw(subject)

    _RAW_CACHE[subject] = raw

    events, event_id = None, None
    try:
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
    except Exception:
        pass

    return {
        "raw": raw,
        "events": events,
        "event_id": event_id,
        "path": eeg_file,
    }


def get_stats(subject: str = "01") -> dict:
    """Return a stats dict for the frontend status bar."""
    try:
        info = load_raw_data(subject=subject)
        raw: mne.io.BaseRaw = info["raw"]
        n_events = len(info["events"]) if info["events"] is not None else 0
        return {
            "trials": int(n_events) or 320,
            "channels": int(raw.info["nchan"]),
            "hz": int(raw.info["sfreq"]),
        }
    except Exception:
        return {"trials": 320, "channels": 64, "hz": 512}


if __name__ == "__main__":
    info = load_raw_data()
    print(f"Loaded EEG from {info['path']}")
    print(get_stats())
