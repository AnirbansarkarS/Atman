import mne
import matplotlib.pyplot as plt
import os

# Directory to save graph images
GRAPH_DIR = 'generated_graphs'
if not os.path.exists(GRAPH_DIR):
    os.makedirs(GRAPH_DIR)

def generate_psd_graph(raw_file_path):
    """
    Generates a Power Spectral Density (PSD) plot from a raw EEG file.
    """
    try:
        raw = mne.io.read_raw_fif(raw_file_path, preload=True)
        fig = raw.plot_psd(show=False)
        
        image_path = os.path.join(GRAPH_DIR, 'psd_graph.png')
        fig.savefig(image_path)
        plt.close(fig)
        print(f"PSD graph saved to {image_path}")
        return image_path
    except Exception as e:
        print(f"Error generating PSD graph: {e}")
        return None

def generate_graph():
    """
    Main function to generate a graph.
    This is a placeholder and should be adapted to your needs.
    """
    # This assumes you have a file in brain_data
    # You might need to run brain_loader.py first
    data_file = '../brain_data/subject_1_run_1.fif'
    if os.path.exists(data_file):
        return generate_psd_graph(data_file)
    else:
        print("Data file not found. Run brain_loader.py to download it.")
        return None

if __name__ == '__main__':
    generate_graph()
