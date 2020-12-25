from sys import argv
from re import findall
from threading import Thread
from os import path, makedirs, chdir
from requests import get as gt
from gazpacho import get, Soup
from gazpacho.utils import HTTPError

def main():

    if len(argv) == 1:
        print(f"Usage: python {argv[0]} <mediafire_url>")
        quit()

    url = argv[1]
    download_folder = "mediafire download"
    match = findall(r"folder\/([a-zA-Z0-9]+)", url)

    # check if link is valid
    if match:
        folder_key = get_folders(match[0])
    else:
        print("Invalid link.")
        quit()


def files_or_folders(filefolder, folder_key):
    return (
        f"https://www.mediafire.com/api/1.4/folder"
        f"/get_content.php?r=utga&content_type={filefolder}"
        f"&filter=all&order_by=name&order_direction=asc&chunk=1"
        f"&version=1.5&folder_key={folder_key}&response_format=json"
    )



def get_folders(folder_key, folder_name="mediafire download"):

    # if the folder not exist, create and enter it
    if not path.exists(folder_name):
        makedirs(folder_name)
    chdir(folder_name)

    # downloading all the files in the main folder
    download_folder(folder_key, folder_name)

    # searching for other folders
    folder_content = gt(files_or_folders('folders', folder_key)).json()["response"]["folder_content"]
    
    # downloading other folders
    if 'folders' in folder_content:
        for folder in folder_content['folders']:
            get_folders(folder['folderkey'], folder['name'])
            chdir("..")



def download_folder(folder_key, folder_name):
    # getting all the files
    try:
        data = gt(files_or_folders('files', folder_key)).json()["response"]["folder_content"]["files"]
    except KeyError:
        print("Invalid link.")
        quit()

    threads = []

    # appending a new thread for downloading every link
    for file in data:
        threads.append(Thread(target=download, args=(file,)))

    # starting all threads
    for thread in threads:
        thread.start()

    # waiting for all threads to finish
    for thread in threads:
        thread.join()

    print(f"{folder_name} download completed.")

def download(file):
    """
    used to download direct file links
    """
    try:
        html = get(file["links"]["normal_download"])
    except HTTPError:
        print("Deleted file or Dangerous File Blocked")
        return

    soup = Soup(html)
    link = (
        soup.find("div", {"class": "download_link"})
        .find("a", {"class": "input popsok"})
        .attrs["href"]
    )
    filename = link.split("/")[-1]
    print(f"Downloading {filename}.")
    with open(filename, "wb") as f:
        f.write(gt(link).content)
    print(f"{filename} downloaded.")


if __name__ == "__main__":
    main()
