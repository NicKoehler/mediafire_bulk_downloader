#!/usr/bin/env python3

from re import findall
from time import sleep
from queue import Queue
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


def print_error(link: str):
    print(
        f"{bcolors.FAIL}Deleted file or Dangerous File Blocked\n"
        f"{bcolors.WARNING}Take a look if you want to be sure: {link}{bcolors.ENDC}"
    )


def main():

    parser = ArgumentParser(
        "mediafire_bulk_downloader", usage="python mediafire.py <mediafire_url>"
    )

    parser.add_argument("folder_url", help="The url of the folder to be downloaded")
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

    match = findall(r"folder\/([a-zA-Z0-9]+)", args.folder_url)

    # check if link is valid
    if match:
        get_folders(match[0], args.output, args.threads, first=True)
    else:
        print(f"{bcolors.FAIL}Invalid link{bcolors.ENDC}")
        exit(1)

    print(f"{bcolors.OKGREEN}{bcolors.BOLD}All downloads completed{bcolors.ENDC}")


def files_or_folders(filefolder, folder_key, chunk=1, info=False):
    return (
        f"https://www.mediafire.com/api/1.4/folder"
        f"/{'get_info' if info else 'get_content'}.php?r=utga&content_type={filefolder}"
        f"&filter=all&order_by=name&order_direction=asc&chunk={chunk}"
        f"&version=1.5&folder_key={folder_key}&response_format=json"
    )


def get_folders(folder_key, folder_name, threads_num, first=False):

    if first:
        folder_name = path.join(
            folder_name,
            gt(files_or_folders("folder", folder_key, info=True)).json()["response"][
                "folder_info"
            ]["name"],
        )

    # if the folder not exist, create and enter it
    if not path.exists(folder_name):
        makedirs(folder_name)
    chdir(folder_name)

    # downloading all the files in the main folder
    download_folder(folder_key, threads_num)

    # searching for other folders
    folder_content = gt(files_or_folders("folders", folder_key)).json()["response"][
        "folder_content"
    ]

    # downloading other folders
    if "folders" in folder_content:
        for folder in folder_content["folders"]:
            get_folders(folder["folderkey"], folder["name"], threads_num)
            chdir("..")


def download_folder(folder_key, threads_num):

    # getting all the files
    data = []
    chunk = 1
    more_chunks = True

    try:
        # if there are more than 100 files makes another request
        # and append the result to data
        while more_chunks:
            r_json = gt(files_or_folders("files", folder_key, chunk=chunk)).json()
            more_chunks = r_json["response"]["folder_content"]["more_chunks"] == "yes"
            data += r_json["response"]["folder_content"]["files"]
            chunk += 1

    except KeyError:
        print("Invalid link")
        return

    event = Event()

    threadLimiter = BoundedSemaphore(threads_num)

    total_threads: list[Thread] = []

    # appending a new thread for downloading every link
    for file in data:
        total_threads.append(
            Thread(
                target=download,
                args=(
                    file,
                    event,
                    threadLimiter,
                ),
            )
        )

    # starting all threads
    for thread in total_threads:
        thread.start()

    # handle being interrupted
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


def download(file: dict, event: Event, limiter: BoundedSemaphore):
    """
    used to download direct file links
    """

    limiter.acquire()

    if event.is_set():
        limiter.release()
        return

    file_link = file["links"]["normal_download"]

    try:
        html = get(file_link)
    except HTTPError:
        print_error(file_link)
        limiter.release()
        return

    soup = Soup(html)
    try:
        link = (
            soup.find("div", {"class": "download_link"})
            .find("a", {"class": "input popsok"})
            .attrs["href"]
        )
    except Exception:
        print_error(file_link)
        limiter.release()
        return

    filename = file["filename"]

    if path.exists(filename):
        print(
            f"{bcolors.WARNING}{bcolors.BOLD}{filename}{bcolors.ENDC}{bcolors.WARNING} already exists, skipping{bcolors.ENDC}"
        )
        limiter.release()
        return

    print(f"{bcolors.OKBLUE}Downloading {bcolors.BOLD}{filename}{bcolors.ENDC}")

    if event.is_set():
        limiter.release()
        return

    with gt(link, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                if event.is_set():
                    break
                if chunk:
                    f.write(chunk)

    if event.is_set():
        remove(filename)
        print(
            f"{bcolors.WARNING}Deteleted partially downloaded {bcolors.BOLD}{filename}{bcolors.ENDC}"
        )
        limiter.release()
        return

    print(
        f"{bcolors.OKGREEN}{bcolors.BOLD}{filename}{bcolors.ENDC}{bcolors.OKGREEN} downloaded{bcolors.ENDC}"
    )
    limiter.release()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
