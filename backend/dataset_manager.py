"""Dataset manager — ensures ds004196 BIDS dataset is available."""
import os
import sys
from pathlib import Path

# Try to import and use openneuro-py for automated download
try:
    from openneuro import download
    HAS_OPENNEURO = True
except ImportError:
    HAS_OPENNEURO = False


def get_dataset_path() -> Path:
    """Return path to ds004196 dataset, downloading if necessary."""
    _HERE = Path(__file__).resolve().parent.parent  # project root
    candidates = [
        _HERE / "ds004196",
        _HERE / "brain_data" / "ds004196",
    ]
    
    # Check if already exists
    for candidate in candidates:
        if candidate.exists() and (candidate / "dataset_description.json").exists():
            print(f"✓ Dataset found at: {candidate}")
            return candidate
    
    # Not found, attempt download
    target = _HERE / "ds004196"
    
    if not HAS_OPENNEURO:
        print("⚠️  openneuro-py not installed. Install with:")
        print("   pip install openneuro-py")
        print("")
        print("Then download manually from:")
        print("   https://openneuro.org/datasets/ds004196")
        print(f"   and extract to: {target}")
        return None
    
    print("🔄 Downloading ds004196 dataset...")
    print("   This may take 5-10 minutes on first run (large dataset)")
    
    try:
        download(
            dataset="ds004196",
            target_dir=str(_HERE),
            workers=4,
            verify=True,
        )
        print(f"✓ Dataset downloaded to: {target}")
        return target
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print(f"   Manual download: https://openneuro.org/datasets/ds004196")
        return None


if __name__ == "__main__":
    path = get_dataset_path()
    if path:
        print(f"\nDataset ready at: {path}")
        sys.exit(0)
    else:
        print("\n❌ Dataset not available")
        sys.exit(1)
