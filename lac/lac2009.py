#
# Licensed under GPL-3.0 or later
#

import re
import requests
from lxml import html
from urllib.parse import urljoin

import lac

def parse_program(tree, url=None, verbose=False):
    program = []

    items = tree.xpath("//div[@id=\"content\"]/ul/li/a")
    for item in items:
        title = item.text_content()
        page = item.get("href")
        entry = parse_page(urljoin(url, page), verbose=verbose)
        program.append(entry)

    return program


def parse_page(url, verbose=False):
    page = requests.get(url)
    tree = html.fromstring(page.content)

    video_url = None
    paper_url = None
    slides_url = None
    misc_url = None
    source = url
    result = tree.xpath("//h2/text()")
    if len(result) > 0:
        full_title = result[0]
        m = re.search(r"([^:])*: (.*)", full_title)
        if m:
            presenter = m.group(1)
            title = m.group(2).strip()
        else:
            return None
    else:
        return None

    result = tree.xpath("//div[@id=\"content\"]/p[1]/text()")
    abstract = ""
    for t in result:
        abstract += t
    if False and verbose:
        print(abstract)

    result = tree.xpath("//div[@id=\"content\"]/p[2]/child::node()")
    print(result)
    for i in range(len(result)):
        n = result[i]
        if isinstance(n, str):
            n = n.strip()
            if re.match(r"Paper:", n):
                i += 1
                if result[i].tag == "a":
                    paper_url = urljoin(url, result[i].get("href"))
            elif re.match(r"Slides:", n):
                i += 1
                if result[i].tag == "a":
                    slides_url = urljoin(url, result[i].get("href"))
            elif re.match(r"Homepage:", n):
                i += 1
                if result[i].tag == "a":
                    homepage_url = result[i].get("href")
                    abstract += n
                    abstract += lac.linkify(homepage_url)
            elif re.match(r"Video Recording:", n):
                if result[i + 1].tag == "a":
                    i += 1
                    list_url = result[i].get("href")
                else:
                    # still look up in the default list
                    list_url = "http://lac.linuxaudio.org/2009/cdm/videos/"
                video_url = parse_video_list(list_url, title, verbose=verbose)
                if video_url is None:
                    print("Couldn't find video for {}".format(title))
                else:
                    video_url = urljoin(list_url, video_url)

            elif i + 1 < len(result):
                if result[i + 1].tag == "a":
                    i += 1
                    misc_url = urljoin(url, result[i].get("href"))
                    if verbose:
                        print("Misc link {}".format(n))

    # video_file = re.sub(r": ", " - ", full_title)
    # video_file = re.sub(r" ", "_", video_file)

    return dict(
        conf="Linux Audio Conference 2009",
        presenter=presenter,
        title=title,
        abstract=abstract,
        video_url=video_url,
        paper_url=paper_url,
        slides_url=slides_url,
        misc_url=misc_url,
        source=source,
        license_text = "",
        license = None,
        date="2009",
        year="2009"
    )

def parse_video_list(url, title, verbose=False):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    result = tree.xpath("//table/tr/td/a")

    idx = title.find(":")
    if idx != -1:
        title = title[idx + 1:].strip()
    title = title[:23]
    title = re.sub(r" ", "_", title)
    title = re.sub(r"\?", "", title)
    title = title.lower()
    if verbose:
        print("Searching for {}".format(title))

    for item in result:
        text = item.text.lower()
        # Hacks, the video titles have typos
        text = re.sub(r"progamming", "programming", text)
        text = re.sub(r"constant_q", "constant-q", text)
        text = re.sub(r"transient effect", "transient effects", text)
        if text.find(title) != -1:
            print("Found {}".format(item.text))
            return item.get("href")
    return None
