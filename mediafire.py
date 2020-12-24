from sys import argv
from re import findall
from threading import Thread
from os import path, makedirs
from requests import get as gt
from gazpacho import get, Soup

url = argv[1]
download_folder = "mediafire download"
folder_key = findall(r"folder\/([a-zA-Z0-9]+)", url)[0]

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
        print("Link non valido")
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

    print("Download della cartella completato.")


def download(link):
    """
    used to download direct file links
    """
    filename = link.split("/")[-1]
    print(f"Sto scaricando {filename}")
    with open("/".join([download_folder, filename]), "wb") as f:
        f.write(gt(link).content)
    print(f"{filename} scaricato.")


if __name__ == "__main__":
    main()
