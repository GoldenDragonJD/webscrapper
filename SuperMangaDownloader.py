import json
import requests
import os
import re

from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO


class Page:
    def __init__(self, number, url, check):
        self.url = url
        self.check = check
        self.number = number


class Chapter:
    def __init__(self, title, url, check):
        self.title = title
        self.pages = []
        self.check = check
        self.url = url

    def add_page(self, number, page_url, check):
        page = Page(number, page_url, check)
        self.pages.append(page)

    def list_pages(self):
        page_str = ", ".join(page.content for page in self.pages)
        print(page_str)

    def update_check_status(self):
        self.check = all(page.check for page in self.pages)


class Manga:
    def __init__(self, title, url, check):
        self.title = title
        self.chapters = {}
        self.check = check
        self.url = url

    def add_chapter(self, chapter_title, url, check):
        chapter = Chapter(chapter_title, url, check)
        self.chapters[chapter_title] = chapter

    def list_chapters(self):
        chapter_str = ", ".join(chapter.title for chapter in self.chapters.values())
        print(chapter_str)

    def update_check_status(self):
        self.check = all(chapter.check for chapter in self.chapters.values())

    def sort_chapters(self):
        def extract_numeric_part(chapter_title):
            match = re.search(r'\d+', chapter_title)
            return int(match.group()) if match else 0

        sorted_chapters = sorted(self.chapters.values(), key=lambda x: extract_numeric_part(x.title))

        self.chapters = {}

        for chapter in sorted_chapters:
            self.chapters[chapter.title] = chapter


def remove_invalid_file_characters(input_string):
    pattern = r'[\\/:*?"<>|]'

    cleaned_string = re.sub(pattern, '', input_string)

    return cleaned_string


def save_manga(book, title):
    with open(f"Data-Folder/{title}.json", "w") as file:
        json.dump(book, file, default=lambda obj: obj.__dict__, indent=4)


def load_manga(title):
    with open(f"Data-Folder/{title}.json", "r") as file:
        data = json.load(file)
        manga_name = data["title"]
        manga_url = data["url"]
        manga_check = data["check"]

        manga = Manga(manga_name, manga_url, manga_check)

        for chapter_data in data["chapters"].values():
            chapter_name = chapter_data["title"]
            chapter_url = chapter_data["url"]
            chapter_check = chapter_data["check"]

            manga.add_chapter(chapter_name, chapter_url, chapter_check)

            for page_data in chapter_data["pages"]:
                page_number = page_data["number"]
                page_url = page_data["url"]
                page_check = page_data["check"]

                manga.chapters[chapter_data["title"]].add_page(page_number, page_url, page_check)

        return manga


def get_page_soup(url):
    page_response = requests.get(url)

    if not page_response.status_code == 200:
        return print("Unable to connect to webpage")

    page_soup = BeautifulSoup(page_response.text, "html.parser")
    return page_soup


def get_soup(html):
    return BeautifulSoup(str(html), "html.parser")


def convert(url):
    return get_page_soup(url)


def get_manga_title(page_soup):
    manga_html = page_soup.find("div", class_="infox")

    manga_name = get_soup(manga_html).find(class_="entry-title").get_text()

    manga_name = remove_invalid_file_characters(manga_name)

    return manga_name


def get_chapter_urls(page_soup, reverse):
    chapter_html = page_soup.find_all(class_="clstyle")

    chapter_urls = []

    chapter_list = get_soup(chapter_html)

    for chapter_stuff in chapter_list.find_all("a"):
        chapter_url = chapter_stuff.get("href")
        chapter_urls.append(chapter_url)

    if reverse:
        chapter_urls.reverse()

    return chapter_urls


def get_chapter_names(page_soup, reverse):
    chapter_html = page_soup.find_all(class_="clstyle")

    chapter_names = []

    chapter_list = get_soup(chapter_html)

    for chapter_name in chapter_list.find_all(class_="chapternum"):

        clean_name = remove_invalid_file_characters(chapter_name.get_text())

        chapter_names.append(clean_name)

    if reverse:
        chapter_names.reverse()

    return chapter_names


def get_pages(page_soup):
    page_html = page_soup.find_all("img", class_="ts-main-image")

    page_urls = []

    for page in page_html:
        page_url = page.get("src")

        if requests.get(page_url).status_code == 200:
            page_urls.append(page_url)

    return page_urls


def get_alternate_pages(page_soup):
    page_html = page_soup.find_all("p")

    page_urls = []

    page_list = get_soup(page_html)

    for page in page_list.find_all("img"):
        page_url = page.get("src")

        if requests.get(page_url).status_code == 200:
            page_urls.append(page_url)

    return page_urls


def get_page_ext(page_url):
    page_ext = f".{page_url.split('/')[-1].split('.')[-1]}"
    return page_ext


def add_to_class(url):
    manga_url = convert(url)
    manga = Manga(get_manga_title(manga_url), url, False)
    manga.title = get_manga_title(manga_url)

    data_folder_name = "Data-Folder"

    if not os.path.exists(data_folder_name):
        os.makedirs(data_folder_name)

    print("Starting Recording Process")

    for chapter_url, chapter_title in zip(get_chapter_urls(manga_url, True), get_chapter_names(manga_url, True)):
        manga.add_chapter(chapter_title, chapter_url, False)
        print(f"{manga.title} {chapter_title} added to the tree.")

        pages = get_pages(convert(chapter_url))

        if len(pages) == 0:
            pages = get_alternate_pages(convert(chapter_url))

        for page_url, page_number in zip(pages, range(0, (len(pages)))):
            manga.chapters[chapter_title].add_page(f"{page_number}{get_page_ext(page_url)}", page_url, False)
            print(f"{page_number}{get_page_ext(page_url)} added to the {chapter_title} tree in {manga.title}")

        save_manga(manga, manga.title)
    save_manga(manga, manga.title)


def download(title, path):
    manga = load_manga(f"{title}")
    chapters = manga.chapters

    if not os.path.exists(f"{path}/{title}"):
        os.makedirs(f"{path}/{title}")

    for chapter in chapters.values():
        pages = chapter.pages

        chapter.title = remove_invalid_file_characters(chapter.title)

        if not os.path.exists(f"{path}/{title}/{chapter.title}"):
            os.makedirs(f"{path}/{title}/{chapter.title}")

        for page in pages:
            if page.check is False:
                image_response = requests.get(page.url)

                if image_response.status_code != 200:
                    update_list(manga.title, manga.url, True)

                image_content = image_response.content
                image = Image.open(BytesIO(image_content))
                image.save(f"{path}/{title}/{chapter.title}/{page.number}")
                page.check = True
                print(f"{title} {chapter.title} {page.number} Downloaded!")
                save_manga(manga, f"{title}")

            chapter.update_check_status()

        manga.update_check_status()

    save_manga(manga, f"{title}")


def check_if_downloaded(title, path):
    manga = load_manga(title)
    chapters = manga.chapters

    if not os.path.exists(f"{path}/{title}"):

        for chapter in chapters.values():
            pages = chapter.pages
            for page in pages:
                if page.check is False:
                    continue
                page.check = False
                chapter.update_check_status()
                save_manga(manga, title)
            chapter.check = False
            save_manga(manga, title)
            manga.update_check_status()
        manga.check = False
        save_manga(manga, title)

    for chapter in chapters.values():
        if not os.path.exists(f"{path}/{title}/{chapter.title}"):
            pages = chapter.pages

            for page in pages:
                if page.check is False:
                    continue
                page.check = False
                chapter.update_check_status()
                save_manga(manga, title)
            chapter.check = False
            save_manga(manga, title)

        pages = chapter.pages

        for page in pages:
            if page.check is False:
                continue
            if not os.path.exists(f"{path}/{title}/{chapter.title}/{page.number}"):
                print("check!")
                page.check = False
                chapter.update_check_status()
                save_manga(manga, title)

    for chapter in chapters.values():
        pages = chapter.pages

        for page in pages:
            if page.check is True:
                continue
            if os.path.exists(f"{path}/{title}/{chapter.title}/{page.number}"):
                page.check = True
                chapter.update_check_status()
                save_manga(manga, title)


def update_list(title, url, hard):

    try:
        manga = load_manga(title)
    except Exception as e:
        print(e)
        return add_to_class(url)

    if hard:
        chapter_urls = get_chapter_urls(convert(url), False)

        saved_chapter_urls = []

        for saved_chapter in manga.chapters.values().__reversed__():
            saved_chapter_urls.append(saved_chapter.url)

        saved_file = set(saved_chapter_urls)
        online_file = set(chapter_urls)

        missing_chapters = online_file - saved_file

    if not hard:
        chapter_names = get_chapter_names(convert(url), False)

        saved_chapter_names = []

        for saved_chapter in manga.chapters.values():
            saved_chapter_names.append(saved_chapter.title)

        saved_file = set(saved_chapter_names)
        online_file = set(chapter_names)

        missing_chapters = online_file - saved_file

    if len(missing_chapters) != 0:
        print(f"Missing chapters for {manga.title} found: {len(missing_chapters)} chapters: {missing_chapters}")

    for missing_chapter in missing_chapters:
        for online_chapter_url, online_chapter_name in zip(get_chapter_urls(convert(url), False),
                                                           get_chapter_names(convert(url), False)):
            if missing_chapter == online_chapter_url or missing_chapter == online_chapter_name:
                print(f"{manga.title}'s Missing Chapter: {online_chapter_name} Found...")

                manga.add_chapter(online_chapter_name, online_chapter_url, False)
                manga.sort_chapters()

                print(f"Missing Chapter Loaded To System and List Has Been Sorted!")

                online_pages = get_pages(convert(online_chapter_url))

                print(online_pages)

                if len(online_pages) == 0:
                    online_pages = get_alternate_pages(convert(online_chapter_url))

                for online_page, page_name in zip(online_pages, range(0, len(online_pages))):
                    page_ext = get_page_ext(online_page)
                    manga.chapters[online_chapter_name].add_page(f"{page_name}{page_ext}", online_page, False)
                    print(f"Added Page {online_page} to the System.")

        save_manga(manga, title)
    save_manga(manga, title)


def get_mangas():
    mangas = []

    for x in range(1, 10):
        main_url = f"https://asuratoon.com/manga/?page={x}&order=update"
        main_web_html = get_page_soup(main_url).find_all("div", class_="listupd")

        mangas_links = get_soup(main_web_html)

        for manga in mangas_links.find_all("a"):
            manga_url = manga.get("href")
            mangas.append(manga_url)

    return mangas


def manage_mangas():
    manga_links = get_mangas()

    manga_folder = "Manga-Folder"
    data_folder = "Data-Folder"

    if not os.path.exists(manga_folder):
        os.makedirs(manga_folder)

    for manga_link in manga_links:
        manga_name = get_manga_title(convert(manga_link))

        if not os.path.exists(f"{data_folder}/{manga_name}.json"):
            add_to_class(manga_link)
        elif os.path.exists(f"{data_folder}/{manga_name}.json"):
            update_list(manga_name, manga_link, False)
        check_if_downloaded(manga_name, manga_folder)
        download(manga_name, manga_folder)
        print(f"{manga_name} has been checked.")


if __name__ == '__main__':
    input("[Press the Enter key to continue]")

    while 1 == 1:
        manage_mangas()
