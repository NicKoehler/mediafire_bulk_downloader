#!/usr/bin/env python3

import hashlib
from re import findall
from time import sleep
from requests import get as gt
from gazpacho import get, Soup
from argparse import ArgumentParser
from gazpacho.utils import HTTPError
from os import path, makedirs, remove, chdir
from threading import BoundedSemaphore, Thread, Event


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Non-alphanumeric (str.isalphanum()) characters allowed in a file or folder name
NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTERS = "-_. "
# What to replace bad characters with.
NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTER_REPLACEMENT = "-"
# Premium files links downloads directly
NORMAL_FILE = "https://www.mediafire.com/file/"

import hashlib


def hash_file(filename: str) -> str:
    """
    Calculate the SHA-256 hash digest of a file.

    Args:
        filename (str): The path to the file.

    Returns:
        str: The hexadecimal representation of the hash digest.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If the user does not have permission to read the file.
    """
    # make a hash object
    h = hashlib.sha256()

    # open file for reading in binary mode
    with open(filename, "rb") as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def normalize_file_or_folder_name(filename: str) -> str:
    """
    Normalize a file or folder name by replacing non-alphanumeric characters.

    Args:
        filename (str): The original file or folder name.

    Returns:
        str: The normalized file or folder name.

    Note:
        If you want to disable normalization, uncomment the return statement at the beginning of the function.

    Example:
        >>> normalize_file_or_folder_name("my_file$%")
        'my_file_'

    """
    return "".join(
        [
            char
            if (char.isalnum() or char in NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTERS)
            else NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTER_REPLACEMENT
            for char in filename
        ]
    )


def print_error(link: str):
    """
    Prints an error message indicating that a file has been deleted or blocked due to being dangerous.

    Parameters:
        link (str): The link to the file or resource that caused the error.

    Returns:
        None

    Example:
        >>> print_error("https://example.com/dangerous_file.txt")
        Deleted file or Dangerous File Blocked
        Take a look if you want to be sure: https://example.com/dangerous_file.txt
    """
    print(
        f"{bcolors.FAIL}Deleted file or Dangerous File Blocked\n"
        f"{bcolors.WARNING}Take a look if you want to be sure: {link}{bcolors.ENDC}"
    )


def main():
    """
    Mediafire Bulk Downloader

    Parses command-line arguments to download files or folders from Mediafire.

    Usage:
        python mediafire.py <mediafire_url> [-o <output_path>] [-t <num_threads>]

    Arguments:
        mediafire_url (str): The URL of the file or folder to be downloaded from Mediafire.

    Options:
        -o, --output (str): The path of the desired output folder. Default is the current directory.
        -t, --threads (int): Number of threads to use for downloading. Default is 10.

    Returns:
        None

    Example:
        To download a file:
        $ python mediafire.py https://www.mediafire.com/file/example_file.txt

        To download a folder:
        $ python mediafire.py https://www.mediafire.com/folder/example_folder -o /path/to/output -t 20
    """
    parser = ArgumentParser(
        "mediafire_bulk_downloader", usage="python mediafire.py <mediafire_url>"
    )
    parser.add_argument(
        "mediafire_url", help="The URL of the file or folder to be downloaded"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The path of the desired output folder",
        required=False,
        default=".",
    )
    parser.add_argument(
        "-t",
        "--threads",
        help="Number of threads to use",
        type=int,
        default=10,
        required=False,
    )

    args = parser.parse_args()

    folder_or_file = findall(
        r"mediafire\.com/(folder|file)\/([a-zA-Z0-9]+)", args.mediafire_url
    )

    if not folder_or_file:
        print(f"{bcolors.FAIL}Invalid link{bcolors.ENDC}")
        exit(1)

    t, key = folder_or_file[0]

    if t == "file":
        get_file(key, args.output)
    elif t == "folder":
        get_folders(key, args.output, args.threads, first=True)
    else:
        print(f"{bcolors.FAIL}Invalid link{bcolors.ENDC}")
        exit(1)

    print(f"{bcolors.OKGREEN}{bcolors.BOLD}All downloads completed{bcolors.ENDC}")
    exit(0)


def get_files_or_folders_api_endpoint(
    filefolder: str, folder_key: str, chunk: int = 1, info: bool = False
) -> str:
    """
    Constructs the API endpoint URL for retrieving files or folders information from Mediafire.

    Parameters:
        filefolder (str): Type of content to retrieve. Either 'file' or 'folder'.
        folder_key (str): The unique identifier of the folder.
        chunk (int): The chunk number to retrieve. Default is 1.
        info (bool): If True, gets folder info; otherwise, gets content. Default is False.

    Returns:
        str: The constructed API endpoint URL.

    Example:
        >>> get_files_or_folders_api_endpoint('folder', 'folder_key_123', chunk=2, info=True)
        'https://www.mediafire.com/api/1.4/folder/get_info.php?r=utga&content_type=folder&filter=all&order_by=name&order_direction=asc&chunk=2&version=1.5&folder_key=folder_key_123&response_format=json'
    """
    return (
        f"https://www.mediafire.com/api/1.4/folder"
        f"/{'get_info' if info else 'get_content'}.php?r=utga&content_type={filefolder}"
        f"&filter=all&order_by=name&order_direction=asc&chunk={chunk}"
        f"&version=1.5&folder_key={folder_key}&response_format=json"
    )


def get_info_endpoint(file_key: str) -> str:
    """
    Constructs the API endpoint URL for retrieving information about a specific file from Mediafire.

    Parameters:
        file_key (str): The unique identifier of the file.

    Returns:
        str: The constructed API endpoint URL.

    Example:
        >>> get_info_endpoint('file_key_123')
        'https://www.mediafire.com/api/file/get_info.php?quick_key=file_key_123&response_format=json'
    """
    return f"https://www.mediafire.com/api/file/get_info.php?quick_key={file_key}&response_format=json"


def get_folders(
    folder_key: str, folder_name: str, threads_num: int, first: bool = False
) -> None:
    """
    Recursively downloads folders and files from Mediafire.

    Parameters:
        folder_key (str): The unique identifier of the folder.
        folder_name (str): The name of the folder.
        threads_num (int): Number of threads to use for downloading.
        first (bool): If True, it's the first folder being processed. Default is False.

    Returns:
        None

    Example:
        >>> get_folders('folder_key_123', '/path/to/download', 5, first=True)
    """
    if first:
        folder_name = path.join(
            folder_name,
            normalize_file_or_folder_name(
                gt(
                    get_files_or_folders_api_endpoint("folder", folder_key, info=True)
                ).json()["response"]["folder_info"]["name"]
            ),
        )

    # If the folder doesn't exist, create and enter it
    if not path.exists(folder_name):
        makedirs(folder_name)
    chdir(folder_name)

    # Downloading all the files in the main folder
    download_folder(folder_key, threads_num)

    # Searching for other folders
    folder_content = gt(
        get_files_or_folders_api_endpoint("folders", folder_key)
    ).json()["response"]["folder_content"]

    # Downloading other folders recursively
    if "folders" in folder_content:
        for folder in folder_content["folders"]:
            get_folders(folder["folderkey"], folder["name"], threads_num)
            chdir("..")


def download_folder(folder_key: str, threads_num: int) -> None:
    """
    Downloads all files from a Mediafire folder.

    Parameters:
        folder_key (str): The unique identifier of the folder.
        threads_num (int): Number of threads to use for downloading.

    Returns:
        None

    Example:
        >>> download_folder('folder_key_123', 5)
    """
    # Getting all the files
    data = []
    chunk = 1
    more_chunks = True

    try:
        # If there are more than 100 files, make another request
        # and append the result to data
        while more_chunks:
            r_json = gt(
                get_files_or_folders_api_endpoint("files", folder_key, chunk=chunk)
            ).json()
            more_chunks = r_json["response"]["folder_content"]["more_chunks"] == "yes"
            data += r_json["response"]["folder_content"]["files"]
            chunk += 1

    except KeyError:
        print("Invalid link")
        return

    event = Event()
    threadLimiter = BoundedSemaphore(threads_num)
    total_threads: list[Thread] = []

    # Appending a new thread for downloading every link
    for file in data:
        total_threads.append(
            Thread(
                target=download_file,
                args=(
                    file,
                    event,
                    threadLimiter,
                ),
            )
        )

    # Starting all threads
    for thread in total_threads:
        thread.start()

    # Handle being interrupted
    try:
        while True:
            if all(not t.is_alive() for t in total_threads):
                break
            sleep(0.01)
    except KeyboardInterrupt:
        print(f"{bcolors.WARNING}Closing all threads{bcolors.ENDC}")
        event.set()
        for thread in total_threads:
            thread.join()
        print(f"{bcolors.WARNING}{bcolors.BOLD}Download interrupted{bcolors.ENDC}")
        exit(0)


def get_file(key: str, output_path: str = None) -> None:
    """
    Downloads a single file from Mediafire using the main thread.

    Parameters:
        key (str): The unique identifier of the file.
        output_path (str): The path where the file will be downloaded. If None, the current directory is used.

    Returns:
        None

    Example:
        >>> get_file('file_key_123', '/path/to/download')
    """
    # Retrieve file information
    file_data = gt(get_info_endpoint(key)).json()["response"]["file_info"]

    # Change directory if output_path is provided
    if output_path:
        chdir(output_path)

    # Download the file
    download_file(file_data)


def download_file(
    file: dict, event: Event = None, limiter: BoundedSemaphore = None
) -> None:
    """
    Downloads a file from a direct link obtained from Mediafire.

    Parameters:
        file (dict): A dictionary containing file information, including the direct download link.
        event (Event): An optional threading event used for handling interruptions.
        limiter (BoundedSemaphore): An optional semaphore for controlling the number of concurrent downloads.

    Returns:
        None

    Example:
        >>> download_file({'filename': 'example_file.txt', 'links': {'normal_download': 'https://www.mediafire.com/download/example_file.txt'}})
    """
    # Acquire semaphore if available
    if limiter:
        limiter.acquire()

    # Check for event and release semaphore if event is set
    if event:
        if event.is_set():
            if limiter:
                limiter.release()
            return

    # Extract direct download link from file information
    file_link = file["links"]["normal_download"]
    download_link = file_link

    if file_link.startswith(NORMAL_FILE):
        try:
            # Retrieve the HTML content of the file link
            html = get(file_link)
        except HTTPError:
            # Handle HTTP errors
            print_error(file_link)
            if limiter:
                limiter.release()
            return

        # Parse HTML content to extract the actual download link
        soup = Soup(html)
        try:
            download_link = (
                soup.find("div", {"class": "download_link"})
                .find("a", {"class": "input popsok"})
                .attrs["href"]
            )
        except Exception:
            # Handle errors in finding or extracting download link
            print_error(file_link)
            if limiter:
                limiter.release()
            return

    # Normalize filename
    filename = normalize_file_or_folder_name(file["filename"])

    # Check if file already exists and is not corrupted
    if path.exists(filename):
        if hash_file(filename) == file["hash"]:
            print(f"{bcolors.WARNING}{filename}{bcolors.ENDC} already exists, skipping")
            if limiter:
                limiter.release()
            return
        else:
            print(
                f"{bcolors.WARNING}{filename}{bcolors.ENDC} already exists but corrupted, downloading again"
            )

    # Start downloading the file
    print(f"{bcolors.OKBLUE}Downloading {filename}{bcolors.ENDC}")

    if event:
        if event.is_set():
            if limiter:
                limiter.release()
            return

    # Download file in chunks
    with gt(download_link, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                if event:
                    if event.is_set():
                        break
                if chunk:
                    f.write(chunk)

    # Check if download was interrupted
    if event:
        if event.is_set():
            remove(filename)
            print(
                f"{bcolors.WARNING}Partially downloaded {filename} deleted{bcolors.ENDC}"
            )
            if limiter:
                limiter.release()
            return

    # Print download success message
    print(f"{bcolors.OKGREEN}{filename}{bcolors.ENDC} downloaded")

    # Release semaphore if acquired
    if limiter:
        limiter.release()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
