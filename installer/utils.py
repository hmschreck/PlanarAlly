import logging
import os
import platform
import requests
import sys
import zipfile


def get_os():
    """
    Get the operating system.
    Returns windows, linux or osx.
    Use this instead of platform.system() to compare with json native names
    """
    if platform.system() == "Windows":
        return "windows"
    elif platform.system() == "Darwin":
        return "osx"
    elif platform.system() == "Linux":
        return "linux"


def get_arch():
    """
    Returns the architecture of the system in use. (32 or 64)
    """
    return "64" if platform.machine().endswith('64') else "32"


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Use this for resources that are bundled with the exe.
    Use the other path methods for downloaded resources.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def download_file(main_url):
    """
    Download a file from a given url.
    This method does NOT write anything to disk but returns the requests response,
    the contents of the file can be accessed through response.content
    """
    try:
        response = requests.get(main_url)
        if response.status_code == 200:
            return response
    except requests.ConnectionError:
        pass

    raise FileNotFoundError("Could not download from url: {}".format(main_url))


def write_file(content, path):
    """
    Write content to a file.
    """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as f:
        f.write(content)


def download_zip(main_url, download_location, filter=None):
    """
    Download the contents of a zipfile to a local directory.
    download_location is the directory where the zip should be extracted.
    """
    # do not try/except as we want to propagate the exception
    zip_response = download_file(main_url)

    with BytesIO(zip_response.content) as in_memory:
        with zipfile.ZipFile(in_memory, "r") as z:
            if filter is None:
                z.extractall(path=download_location)
            else:
                for f in filter:
                    z.extract(f, path=download_location)
