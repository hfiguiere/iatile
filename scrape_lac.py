#!/usr/bin/env python

#
# Licensed under GPL-3.0 or later
#

import sys
import re
import argparse
import lxml
from lxml import html
import requests
from urllib.parse import urlparse, urljoin

import lac
import lacupload

parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
parser.add_argument("url", help="URL")
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
parser.add_argument("--orphans", action="store_true", help="Only get orphan items")

args = parser.parse_args()
dry_run = args.dry_run
verbose = args.verbose

def parse_program(url, verbose = False):
    page = requests.get(url)
    tree = html.fromstring(page.content)

    program = []

    result = tree.xpath("//div[@id=\"maintitle\"]/text()");
    if result == 0:
        print("Error: can't guess conference")
        sys.exit(1)

    conf = result[0]
    if verbose:
        print("Conference {}".format(conf))

    m = re.search(r"Linux Audio Conference ([0-9]{4})", conf)
    if m is None:
        print("Can't guess year, bailing out")
        sys.exit(1)

    year = m.group(1)
    if verbose:
        print("Year: {}".format(year))

    timeslots = tree.xpath("//div[@id=\"content\"]/span[@class=\"tme\"]")
    for tm in timeslots:
        # print("Found timeslot {}".format(tm.text_content()))
        if verbose:
            print("BEGIN ========")
        nodes = tm.xpath("following-sibling::node()[local-name() != \"\"]")
        # print("Found {} node".format(len(nodes)))

        title = None
        presenter = None
        abstract = None
        video_link = None
        paper_link = None
        audio_link = None
        slides_link = None
        misc_link = None

        for node in nodes:
            # print("Node: {}".format(lxml.etree.tostring(node)))
            if node.tag == "hr" and node.get("class") == "psep":
                # print("Found separator")
                break
            elif node.tag == "span":
                # print("Node: {}".format(lxml.etree.tostring(node)))
                if title is None:
                    result = node.xpath("b/text()");
                    if len(result) > 0:
                        title = result[0]
            elif node.tag == "em":
                p = node.xpath("a/text()")
                if len(p) > 0:
                    presenter = p[0]
                else:
                    presenter = node.text
            elif node.tag == "div":
                klass = node.get("class")
                if klass == "abstract":
                    abstract = node.text_content()
                elif klass == "flright":
                    link = node.xpath("a[contains(text(), \"Video\")]/@href")
                    if len(link) > 0:
                        video_link = urljoin(url, link[0])
                        if not re.match(r"lac\.linuxaudio\.org",
                                        urlparse(video_link).netloc):
                            print("URL is off LAC")
                            video_link = None
                    link = node.xpath("a[contains(text(), \"Paper\")]/@href")
                    if len(link) > 0:
                        paper_link = link[0]
                    link = node.xpath("a[contains(text(), \"Slides\")]/@href")
                    if len(link) > 0:
                        slides_link = link[0]
                    link = node.xpath("a[contains(text(), \"Audio\")]/@href")
                    if len(link) > 0:
                        audio_link = link[0]
                    link = node.xpath("a[contains(text(), \"Misc.\")]/@href")
                    if len(link) > 0:
                        misc_link = link[0]


        if len(title) == 0:
            print("No title found")
            sys.exit(1)

        if verbose:
            print("Title: {}".format(title))
            print("Found abstract: {}".format(abstract))
            print("Presenter: {}".format(presenter))
            if video_link is not None:
                print("video link: {}".format(video_link))
            if audio_link is not None:
                print("audio link: {}".format(audio_link))
            if slides_link is not None:
                print("slides link: {}".format(slides_link))
            if paper_link is not None:
                print("paper link: {}".format(paper_link))
            if misc_link is not None:
                print("misc {}".format(misc_link))

        params = dict(
            conf = conf,
            title = title,
            presenter = presenter,
            source = None,
            abstract = abstract,
            video_url = video_link,
            paper_url = paper_link,
            slides_url = slides_link,
            audio_url = audio_link,
            misc_url = misc_link,
            license_text = "",
            license = None,
            year = year,
            date = year
        )
        program.append(params)

    return program



program = parse_program(args.url, verbose = args.verbose)
print("found {} item of conference program".format(len(program)))
if args.orphans:
    print("checking orphans")
    orphans = []
    for item in program:
        if not lac.is_video_page(item["video_url"]):
            orphans.append(item)
    print("found {} orphan item of conference program".format(len(orphans)))
    program = orphans

for item in program:
    if item["video_url"] is not None or item["paper_url"] is not None or item["slides_url"] is not None or item["audio_url"] is not None:
        # or item["misc_url"] is not None:
        lacupload.upload_video(item["video_url"], item, dry_run=dry_run, verbose=verbose)
    else:
        print("Nothing to download for {}".format(item["title"]))
