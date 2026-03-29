from pathlib import Path
import matplotlib.pyplot as plt
import mne

import brain_loader

GRAPH_DIR = Path(__file__).resolve().parent / 'generated_graphs'
GRAPH_DIR.mkdir(exist_ok=True)


def generate_psd_graph(raw: mne.io.BaseRaw, subject: str = '01', session: str = 'EEG') -> Path:
    """Generate and save a PSD plot for the provided raw EEG data."""
    fig = raw.plot_psd(show=False)
    image_path = GRAPH_DIR / f'psd_sub-{subject}_ses-{session}.png'
    fig.savefig(image_path)
    plt.close(fig)
    return image_path


def generate_graph(subject: str = '01', session: str = 'EEG', task: str = 'inner') -> Path | None:
    """Load ds004196 EEG and write a PSD image; returns the image path or None."""
    try:
        info = brain_loader.load_raw_data(subject=subject, session=session, task=task)
        return generate_psd_graph(info['raw'], subject=subject, session=session)
    except Exception as exc:
        print(f"Error generating graph: {exc}")
        return None


if __name__ == '__main__':
    path = generate_graph()
    if path:
        print(f"PSD saved to {path}")
    else:
        print("Failed to generate PSD")
