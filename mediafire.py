from sys import argv
from re import findall
from threading import Thread
from os import path, makedirs
from requests import get as gt
from gazpacho import get, Soup

if len(argv) == 1:
    print(f"Usage: python {argv[0]} <mediafire_url>")
    quit()

url = argv[1]
download_folder = "mediafire download"
match = findall(r"folder\/([a-zA-Z0-9]+)", url)

# check if link is valid
if match:
    folder_key = match[0]
else:
    print("Invalid link.")
    quit()

    base_url = (
        f"https://www.mediafire.com/api/1.4/folder"
        f"/get_content.php?r=utga&content_type=files"
        f"&filter=all&order_by=name&order_direction=asc&chunk=1"
        f"&version=1.5&folder_key={folder_key}&response_format=json"
    )

def main():

    # creating the folder output folder in the current working directory
    if not path.exists(download_folder):
        makedirs(download_folder)

    # getting all the files
    try:
        data = gt(base_url).json()["response"]["folder_content"]["files"]
    except KeyError:
        print("Invalid link.")
        quit()

    threads = []

    # appending a new thread for downloading every link
    for file in data:
        html = get(file["links"]["normal_download"])
        soup = Soup(html)
        link = (
            soup.find("div", {"class": "download_link"})
            .find("a", {"class": "input popsok"})
            .attrs["href"]
        )
        threads.append(Thread(target=download, args=(link,)))

    # starting all threads
    for thread in threads:
        thread.start()

    # waiting for all threads to finish
    for thread in threads:
        thread.join()

    print("Folder download completed.")


def download(link):
    """
    used to download direct file links
    """
    filename = link.split("/")[-1]
    print(f"Downloading {filename}.")
    with open("/".join([download_folder, filename]), "wb") as f:
        f.write(gt(link).content)
    print(f"{filename} downloaded.")


if __name__ == "__main__":
    main()
