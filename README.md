Python webscrapper for the website [AsuraScans.](https://asuratoon.com)https://asuratoon.com

This only works on this website and will not work anywhere else without modifing the main data pulling methods.

Libraries:
-json
-requests
-os
-re
-bs4
-PIL
-io

The info for each book is stored in 3 classes, Page/Chapter/Manga.
Each class has functions meant for debugging perposes, for sorting the info, and for managing if this specific info is downloaded or not(check).

The info from those classes are stored in a json file and saved in the "Data-Folder" that is later opened in the code to get the links so that the webscrapper knows where to go to look for the info to scrape.

The info that is saved for 
Manga:
-title
-url
-check

Chapter:
-title
-url
-check

Page:
-number
-url
-check

The use of check is so that if it ever is false then the code will use the url to download the info that it needs be it the page, chapter, or book.
Reason was that without this meathod it was really slow when checking to see if something is missing but now it use has to see in the json which is faster then loading it one by one in the scrape because of the lag in the response from the website.

The most used functions in the code are:
-get_page_soup(url): returns an html element
-get_soup(html)
-convert(url)
-load_manga(title)

That is it for now, there is still alot more to explain, this code is way more complex then I remeber it being when I wrote it but for now this should explain the basics of the info gathering storing and loading.
