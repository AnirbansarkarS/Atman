from pathlib import Path
import mne

BASE_DIR = Path(__file__).resolve().parent
BIDS_ROOT = BASE_DIR.parent / 'brain_data' / 'ds004196'


def get_eeg_file(subject: str = '01', session: str = 'EEG', task: str = 'inner') -> Path:
    """Return the path to the BIDS EEG recording for the given subject/session."""
    eeg_dir = BIDS_ROOT / f'sub-{subject}' / f'ses-{session}' / 'eeg'
    if not eeg_dir.exists():
        raise FileNotFoundError(f"EEG directory not found: {eeg_dir}")

    # Dataset uses the pattern: sub-XX_ses-EEG_task-inner_eeg.bdf
    pattern = f"sub-{subject}_ses-{session}_task-{task}_eeg.bdf"
    eeg_file = eeg_dir / pattern
    if eeg_file.exists():
        return eeg_file

    # Fallback to the first BDF in the folder if the exact task name differs.
    fallback = next(eeg_dir.glob('*.bdf'), None)
    if fallback:
        return fallback

    raise FileNotFoundError(f"No EEG .bdf file found in {eeg_dir}")


def load_raw_data(subject: str = '01', session: str = 'EEG', task: str = 'inner', preload: bool = True):
    """Load the ds004196 EEG recording as an MNE Raw object."""
    eeg_file = get_eeg_file(subject=subject, session=session, task=task)
    raw = mne.io.read_raw_bdf(eeg_file, preload=preload, verbose='ERROR')

    # Events can be extracted from annotations if present.
    events, event_id = None, None
    try:
        events, event_id = mne.events_from_annotations(raw, verbose='ERROR')
    except Exception:
        # Keep going if annotations are absent; caller can handle None.
        pass

    return {
        'raw': raw,
        'events': events,
        'event_id': event_id,
        'path': eeg_file,
    }


if __name__ == '__main__':
    info = load_raw_data()
    print(f"Loaded EEG recording from {info['path']}")
