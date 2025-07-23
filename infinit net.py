import curses
import requests
import os
import re
import textwrap
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, quote_plus

BOOKMARK_FILE = "infinit_bookmarks.txt"
FAVORITE_FILE = "infinit_favorites.txt"





print ("InfinitNet 0.1 Terminal Internet Browser")
print ("")

print ("________________________________________________________________________________________________")
CATEGORIES = {
    "News": [
        "https://legiblenews.com",
        "http://68k.news",
        "https://text.npr.org",
        "https://lite.cnn.com",                                                            #delete cnn
        "https://news.ycombinator.com",
    ],
    "Sports": [
        "https://plaintextsports.com/",
        "https://www.espn.com/espn/print?id=",                                       #rss is usless atm
    ],
    "FOSS": [
        "https://fosstorrents.com",
        "https://distrowatch.com",
        "https://opensource.com"                                               #only text sites work
    ],
    "Chat": [
        "https://www.irccloud.com",
        "https://app.element.io",
        "https://kiwiirc.com",                                         
        "https://web.libera.chat"
    ],
    "Games": [ 
        "https://textadventures.co.uk/games",
        "https://www.choiceofgames.com/",
        "https://www.ifdb.org/",       
        "https://play.aidungeon.io/",  
        "https://twitchplayspokemon.org/",
    ]
}

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import re
import html

class LinkTextParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.lines = []
        self.links = []
        self.current_line = ""
        self.skip = False
        self.in_title = False
        self.page_title = "Untitled"
        self.current_link = None
        self.link_counter = 1

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "head"):
            self.skip = True
            return
        if tag == "title":
            self.in_title = True
            return
        if tag == "a":
            href = next((v for k, v in attrs if k == "href"), None)
            if href:
                self.current_link = urljoin(self.base_url, href)
                self.current_line += f"[{self.link_counter}] "
        elif tag in ("p", "br", "div", "h1", "h2", "h3"):
            self._newline()
        elif tag == "li":
            self.current_line += "- "

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "head"):
            self.skip = False
            return
        if tag == "title":
            self.in_title = False
            return
        if tag == "a" and self.current_link:
            link_text = self.current_line.strip()
            if link_text:
                self.links.append((link_text, self.current_link))
                self.link_counter += 1
            self.current_link = None
        if tag in ("p", "br", "div", "h1", "h2", "h3", "li"):
            self._newline()

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_title:
            self.page_title = html.unescape(data.strip())
            return
        cleaned = html.unescape(data)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        self.current_line += cleaned

    def _newline(self):
        if self.current_line.strip():
            self.lines.append(self.current_line.strip())
        self.current_line = ""

    def get_content(self):
        self._newline()
        return self.lines, self.links, self.page_title


def save_bookmark(url):
    with open(BOOKMARK_FILE, 'a') as f:
        f.write(url + '\n')

def save_favorite(url):
    with open(FAVORITE_FILE, 'a') as f:
        f.write(url + '\n')

def view_file_list(stdscr, file, label):
    if not os.path.exists(file):
        stdscr.clear()
        stdscr.addstr(0, 0, f"No {label} found. Press any key...")
        stdscr.getch()
        return
    with open(file) as f:
        items = [line.strip() for line in f.readlines()]
    menu(stdscr, label, items, open_url)

def view_bookmarks(stdscr):
    view_file_list(stdscr, BOOKMARK_FILE, "Bookmarks")

def view_favorites(stdscr):
    view_file_list(stdscr, FAVORITE_FILE, "Favorites")

def view_categories(stdscr):
    cats = list(CATEGORIES.keys())
    def open_cat(stdscr, cat_name):
        browse_links(stdscr, CATEGORIES[cat_name])
    menu(stdscr, "Categories", cats, open_cat)

def browse_links(stdscr, urls):
    menu(stdscr, "Sites", urls, open_url)

def menu(stdscr, title, options, action_func):
    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"{title} (arrow keys to navigate, Enter to select, q to quit)")
        h, w = stdscr.getmaxyx()
        for i, opt in enumerate(options):
            y = i + 2
            if y >= h - 1:
                break
            if i == idx:
                stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, 2, opt[:w-4])
            if i == idx:
                stdscr.attroff(curses.A_REVERSE)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            idx = (idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            idx = (idx + 1) % len(options)
        elif key in (10, 13):
            action_func(stdscr, options[idx])
        elif key in (ord('q'), 27):
            break
        elif key == curses.KEY_F1:
            return

def open_url(stdscr, url):
    while True:
        try:
            if not url.startswith("http"):
                url = "http://" + url
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            html = response.text
            parser = LinkTextParser(url)
            parser.feed(html)
            lines, links, title = parser.get_content()

            idx = 0
            link_idx = -1

            while True:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                display_height = height - 4
                line_counter = 0
                for i in range(display_height):
                    line_no = idx + i
                    if line_no >= len(lines):
                        break
                    for wrap_line in textwrap.wrap(lines[line_no], width):
                        if line_counter < display_height:
                            stdscr.addstr(line_counter, 0, wrap_line[:width])
                            line_counter += 1

                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(height-3, 0, f"URL: {url}"[:width])
                stdscr.addstr(height-2, 0, "↑️\ ↓️ scroll | TAB links | ⏎ open | b bookmark | f fav | d save | F1 home | q quit")
                stdscr.attroff(curses.A_REVERSE)

                if links:
                    pos = 0
                    for i, (text, _) in enumerate(links):
                        part = f"{i+1}:{text}  "
                        if pos + len(part) > width:
                            break
                        if i == link_idx:
                            stdscr.attron(curses.A_REVERSE)
                            stdscr.addstr(height-1, pos, part)
                            stdscr.attroff(curses.A_REVERSE)
                        else:
                            stdscr.addstr(height-1, pos, part)
                        pos += len(part)
                else:
                    stdscr.addstr(height-1, 0, "No links found."[:width])

                stdscr.refresh()
                key = stdscr.getch()

                if key == curses.KEY_DOWN:
                    idx = min(len(lines) - display_height, idx + 1)
                elif key == curses.KEY_UP:
                    idx = max(0, idx - 1)
                elif key == 9 and links:
                    link_idx = (link_idx + 1) % len(links)
                elif key in (10, 13) and 0 <= link_idx < len(links):
                    url = links[link_idx][1]
                    break
                elif key == ord('b'):
                    save_bookmark(url)
                elif key == ord('f'):
                    save_favorite(url)
                elif key == ord('d'):
                    filename = re.sub(r'[\\/:*?"<>|]', '_', urlparse(url).netloc + ".txt")
                    filepath = os.path.join(os.getcwd(), filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                elif key in (ord('q'), 27):
                    return
                elif key == curses.KEY_F1:
                    return
        except Exception as e:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Error: {str(e)}")
            stdscr.getch()
            return

def prompt(stdscr, label):
    curses.echo()
    stdscr.addstr(0, 0, label)
    stdscr.clrtoeol()
    stdscr.refresh()
    s = stdscr.getstr(1, 0, 200)
    curses.noecho()
    return s.decode()

def main_menu(stdscr):
    options = ["Categories", "Bookmarks", "Favorites", "URL/Search", "Quit"]
    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "InfinitNet 0.1 Internet Browser")
        stdscr.addstr(2, 0, "Use arrow keys, Enter, or F1 to return home:")
        for i, opt in enumerate(options):
            y = i + 4
            if i == idx:
                stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, 2, opt)
            if i == idx:
                stdscr.attroff(curses.A_REVERSE)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            idx = (idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            idx = (idx + 1) % len(options)
        elif key in (10, 13):
            return options[idx]
        elif key == curses.KEY_F1:
            return "Categories"
        elif key in (ord('q'), 27):
            return "Quit"

def main(stdscr):
    curses.curs_set(0)
    while True:
        choice = main_menu(stdscr)
        if choice == "Quit":
            break
        elif choice == "Categories":
            view_categories(stdscr)
        elif choice == "Bookmarks":
            view_bookmarks(stdscr)
        elif choice == "Favorites":
            view_favorites(stdscr)
        elif choice == "URL/Search":
            query = prompt(stdscr, "Enter search or URL: ")
            if "." in query and " " not in query:
                if not query.startswith("http"):
                    query = "http://" + query
                open_url(stdscr, query)
            else:
                search_url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
                open_url(stdscr, search_url)

if __name__ == "__main__":
    curses.wrapper(main)

