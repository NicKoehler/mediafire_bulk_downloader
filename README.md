# Mediafire Bulk Downloader

_A simple tool that bulk downloads entire mediafire folders for free using python._

---

## Table of contents:

- [Installation](#installation)
- [Usage](#usage)

# Installation

Clone the repository and enter the folder

```sh
git clone https://github.com/NicKoehler/mediafire_bulk_downloader

cd mediafire_bulk_downloader
```

[Optional] Create a virtual enviroment and activate it

```sh
python -m venv venv

```

Linux and macos

```sh
source venv/bin/activate
```

Windows

```sh
.\venv\Scripts\activate.ps1

```

Install the dependencies

```sh
python -m pip install -r requirements.txt
```

# Usage

Help;

```sh
python mediafire.py -h
``` 

Basic usage;

```sh
python mediafire.py <FOLDER_URL>
``` 

With arguments usage;

```sh
python mediafire.py <FOLDER_URL> -t <THREADS> -o <OUTPUT_PATH>
``` 
