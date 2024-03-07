# Mediafire Bulk Downloader

⚠ I made a rust async version of this, check it out [HERE](https://github.com/nickoehler/mediafire_rs)! ⚠

This Python script enables bulk downloading of files and folders from Mediafire.

## Quick Installation

```bash
pip install git+https://github.com/NicKoehler/mediafire_bulk_downloader.git
```

## Setup

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/NicKoehler/mediafire_bulk_downloader.git
    ```

2. Navigate into the project directory:

    ```bash
    cd mediafire_bulk_downloader
    ```

3. Create a virtual environment (optional but recommended):

    ```bash
    python3 -m venv venv
    ```

4. Activate the virtual environment:

    - On Windows:

    ```bash
    venv\Scripts\activate
    ```

    - On macOS and Linux:

    ```bash
    source venv/bin/activate
    ```

5. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script with the following command:

```bash
python mediafire.py <mediafire_url> [-o OUTPUT] [-t THREADS]
```

- `<mediafire_url>`: The URL of the file or folder to be downloaded from Mediafire.
- `-o OUTPUT, --output OUTPUT`: (Optional) The path of the desired output folder. Default is the current directory.
- `-t THREADS, --threads THREADS`: (Optional) Number of threads to use for downloading. Default is 10.

Example usage:

```bash
python mediafire.py https://www.mediafire.com/folder/example_folder -o /path/to/output/folder -t 20
```

## Notes

- Make sure you have Python 3 installed on your system.
- This script requires an active internet connection to download files from Mediafire.
- If downloading a folder, the script will create a directory structure similar to the one on Mediafire.
- You may encounter rate limiting or connection issues, especially when downloading a large number of files.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
