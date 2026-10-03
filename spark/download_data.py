import os
import zipfile
import requests

DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-32m.zip"
TARGET_DIR = "./data/raw"
ZIP_PATH = os.path.join(TARGET_DIR, "ml-32m.zip")

def download_and_extract():
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    if not os.path.exists(ZIP_PATH):
        print("Downloading MovieLens 32M (~267MB compressed)...")
        with requests.get(DATA_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    else:
        print("Archive already exists, skipping download.")

    print("Extracting files...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(TARGET_DIR)
    
    extracted_folder = os.path.join(TARGET_DIR, "ml-32m")
    if os.path.exists(extracted_folder):
        for file_name in os.listdir(extracted_folder):
            src = os.path.join(extracted_folder, file_name)
            dst = os.path.join(TARGET_DIR, file_name)
            if not os.path.exists(dst):
                os.rename(src, dst)
        os.rmdir(extracted_folder)

    print("Data extraction complete. Files saved in ./data/raw/")

if __name__ == "__main__":
    download_and_extract()
