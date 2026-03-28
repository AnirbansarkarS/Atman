import mne
import os

# Path to the directory where EEG files will be stored
DATA_DIR = '../brain_data'

def download_eeg_data(subject_id=1, run=1):
    """
    Downloads EEG data for a specific subject and run from the MNE dataset.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Using a sample dataset from MNE
    # In a real scenario, you would download from a specific URL
    try:
        raw_fname = mne.datasets.sample.data_path() + '/MEG/sample/sample_audvis_raw.fif'
        raw = mne.io.read_raw_fif(raw_fname, preload=True)
        
        # Save the file to our local cache
        output_path = os.path.join(DATA_DIR, f'subject_{subject_id}_run_{run}.fif')
        raw.save(output_path, overwrite=True)
        print(f"Data saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading or saving data: {e}")
        return None

def load_data():
    """
    Loads the EEG data from the cache.
    """
    print("Checking for EEG data...")
    file_path = download_eeg_data()
    if file_path and os.path.exists(file_path):
        print("EEG data found and loaded.")
        # You can add more MNE processing steps here
    else:
        print("Could not load EEG data.")

if __name__ == '__main__':
    load_data()
