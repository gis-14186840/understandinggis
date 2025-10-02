"""
* This script is a workaround for the IT problems in the computer lab. 
* It manually downloads the data needed for the course
"""
from pathlib import Path
from zipfile import ZipFile
from urllib.request import urlretrieve

# Dropbox URL
URL = "https://www.dropbox.com/scl/fo/su9a1ealwe1gvl93n1w6t/APVPuR7LbETkatdqLDCSljs?rlkey=2e72itmofnegoo7sv43ybbao5&dl=1"

# Destination folder
dest = Path(__file__).resolve().parent.parent / "data"

# Skip if ../data already exists
if dest.exists():
    print(f"Skipping download and extract: {dest} already exists.")
    print("If you want to download it again, delete the data file first.")
    exit(0)

# Create ../data directory
print(f"Creating {dest}...")
dest.mkdir(parents=True, exist_ok=True)

# Temporary zip file path
zip_path = Path("archive.zip")

# Download file
print("Downloading file (be patient, this can take a while)...")
urlretrieve(URL, zip_path)

# Extract contents into ../data
print(f"Extracting into {dest}...")
with ZipFile(zip_path, "r") as zf:
    zf.extractall(dest)

# Cleanup
print("Cleaning up...")
zip_path.unlink()

print(f"Done! Files extracted to {dest}")
