#!/usr/bin/env python

#
# Licensed under GPL-3.0 or later
#

import sys
import argparse
import re
import os
import tempfile

from lxml import html
import requests
import urllib
from urllib.parse import urlparse
from urllib.request import urlretrieve

from lac import idify_title, linkify, ensure_item_id
from internetarchive import upload, get_item

def upload_video(url, params, dry_run=False, verbose=False, download_flags=None):
    if download_flags is None:
        download_video = True
        download_slides = True
        download_paper = True
    else:
        download_video = download_flags.download_video
        download_slides = download_flags.download_slides
        download_paper = download_flags.download_paper

    if verbose is True:
        reporter = lambda count, size, total: print(".", end="", flush=True)
    else:
        reporter = None

    tmpdirname = "./downloads"
    source = params["source"]
    year = params["year"]
    title = "LAC {} - {}".format(params["year"], params["title"])

    description = "{}\n<b>{}</b>\n".format(params["conf"], params["title"])
    if params["presenter"] is not None:
        description += "<em>{}</em>\n\n".format(params["presenter"])
    description += "{}\n\n".format(params["abstract"])
    if source is not None:
        description += "Original URL: {}\n".format(linkify(source))
    description += "{}".format(params["license_text"])

    md = dict(title=title,
              mediatype="movies",
              collection="opensource_movies",
              creator="linuxaudio.org",
              subject=[
                  "linux audio conference",
                  "linux", "audio", "software", "kde", "gnome",
                  "conference", "free software",
                  year
              ],
              date = year,
              year = year,
              language = 'eng',
              licenseurl = params['license'],
              description=description,
              source=source
    )

    # slides + paper
    # "texts", "opensource"

    print("description {}".format(description))
    print("params {}".format(params))

    if url is not None:
        u = urlparse(url)
        local_item_file = os.path.basename(u.path)
        # (item_id, ext) = os.path.splitext(local_item_file)
        dest_file = os.path.join(tmpdirname, local_item_file)

    if url is not None:
        if download_video and os.path.exists(dest_file) is False:
            print("Downloading video {}".format(url))
            (item_file, headers) = urlretrieve(
                url,
                filename=dest_file,
                reporthook=reporter)
            if verbose is True:
                print("Done")
        else:
            if download_video:
                item_file = dest_file
                print("File {} already downloaded".format(dest_file))

    item_id = idify_title(params["title"])

    # The item id will be prefixed by LAC + year
    # As to avoid duplicates
    item_id = "LAC{}{}".format(year, item_id)
    item_id = ensure_item_id(item_id)
    if item_id is None:
        print("Can't get item_id")
        sys.exit(1)

    if url is not None:
        if download_video and dry_run is False:
            print("Updloading {} for {}".format(item_file, item_id))
            r = upload(item_id, item_file, metadata=md)
            print("Status {}".format(r[0].status_code))
            if r[0].status_code != 200:
                sys.exit(1)
        else:
            print("Dry run, not uploading video for item {}".format(item_id))

    for asset in ["paper_url", "slides_url", "audio_url"]: #, "misc_url"]:
        if params[asset] is None:
            continue

        if "bookreader-defaults" in md:
            del md["bookreader-defaults"]
        if "licenseurl" in md:
            del md["licenseurl"]

        if asset == "paper_url":
            if not download_paper:
                continue
            subtitle = "Paper"
        elif asset == "slides_url":
            if not download_slides:
                continue
            subtitle = "Slides"
            md["bookreader-defaults"] = "mode/1up"
        elif asset == "audio_url":
            subtitle = "Audio"
        elif asset == "misc_url":
            subtitle = "Misc."

        description = "{}\n{}: <b>{}</b>\n<em>{}</em>\n\n{}".format(
            params["conf"], subtitle, params["title"], params["presenter"],
            params["abstract"])
        if source is not None:
            description += "\n\nOriginal URL: {}".format(linkify(source))

        md["title"] = "LAC {} - {}: {}".format(params["year"],
                                               subtitle,
                                               params["title"])
        md["creator"] = params["presenter"]
        if asset == "audio_url":
            md["mediatype"] = "audio"
        else:
            md["mediatype"] = "texts"
        md["collection"] = "opensource"
        md["description"] = description

        print("asset {} description {}".format(asset, description))
        print("asset {} md {}".format(asset, md))

        u = urlparse(params[asset])
        if not re.match(r"lac\.linuxaudio\.org", u.netloc):
            print("URL is off LAC")
            continue

        local_item_file = os.path.basename(u.path)
        asset_item_id = "{}_{}".format(item_id, subtitle)
        print("item_id {}".format(asset_item_id))

        # if this is empty we end up trying to upload the whole
        # download directory.
        # Let's just move on
        # Test case: http://lac.linuxaudio.org/2012/video.php?id=13
        if len(local_item_file) == 0:
            print("Can't determine the local file name for '{}'".format(subtitle))
            continue

        dest_file = os.path.join(tmpdirname, local_item_file)
        if os.path.exists(dest_file) is False:
            asset_url = urllib.parse.quote(params[asset], safe=":/", encoding="UTF-8")
            (item_file, headers) = urlretrieve(
                asset_url,
                filename=dest_file,
                reporthook=reporter
            )
            if verbose is True:
                print("Done")
        else:
            item_file = dest_file
            print("File {} already downloaded".format(dest_file))

        if dry_run is False:
            if verbose is True:
                print("Uploading {}...".format(item_file))
            r = upload(asset_item_id, item_file, metadata=md)
            print("Status {}".format(r[0].status_code))
            if verbose is True:
                print("Done")
            if r[0].status_code != 200:
                sys.exit(1)
        else:
            print("Dry run, not uploading {}".format(item_file))

#
# parse video_page
#
def parse_video_page(url, verbose=False, dry_run=False, download_flags=None):
    page = requests.get(args.url)
    tree = html.fromstring(page.content)

    result = tree.xpath('//div[@class="header"]/text()')
    if result == 0:
        print("Error: can't guess conference")
        sys.exit(1)

    conf = result[0]

    m = re.search(r"Linux Audio Conference ([0-9]{4})$", conf)
    if m is None:
        print("Can't guess year, bailing out")
        sys.exit(1)

    year = m.group(1)

    print(conf)

    if year == "2011" or year == "2012" or year == "2013" or year == "2014" or year == "2015":
        # print("Found conference I know")

        result = tree.xpath('//div[@class="title"]/b/text()')
        if len(result) >= 1:
            title = result[0]

        result = tree.xpath('//div[@class="title"]/em/text()')
        if len(result) >= 1:
            presenter = result[0]
        else:
            presenter = None

        result = tree.xpath('//div[@class="links"]/ul/li[contains(text(), "Video URL: ")]/a')
        if len(result) == 0:
            result = tree.xpath('//div[@class="links"]/ul/li[contains(text(), "Video: ")]/a')
        num_found = len(result)
        if num_found == 1:
            video_url = result[0].get("href", None)
        elif num_found > 1:
            r_found = 0
            for elem in result:
                m = re.search(r"^([\d]{3,4})p", elem.text_content())
                if m is not None:
                    resolution = int(m.group(1))
                    if resolution > r_found:
                        r_found = resolution
                        video_url = elem.get("href", None)
        else:
            video_url = None

        result = tree.xpath('//div[@class="links"]/ul/li[contains(text(), "Paper: ")]/a/@href')
        if len(result) >= 1:
            paper_url = result[0]
        else:
            paper_url = None

        result = tree.xpath('//div[@class="links"]/ul/li[contains(text(), "Slides: ")]/a/@href')
        if len(result) >= 1:
            slides_url = result[0]
        else:
            slides_url = None

        result = tree.xpath('//a[@rel="license"]/@href')
        if len(result) >= 1:
            license = result[0]
        result = tree.xpath('//div[@class="license"]')
        if len(result) >= 1:
            license_text = result[0].text_content()

        # print("title {}\npresenter {}\nvideo url {}\nlicense {}".format(title, presenter, video_url, license))
        # print("license text: {}".format(license_text))
        # print("paper url {}".format(paper_url))
        # print("slides url {}".format(slides_url))

        result = tree.xpath('//div[@class="abstract"]')
        if len(result) >= 1:
            abstract = result[0].text_content();
        else:
            abstract = ""
        # print("abstract:\n{}".format(abstract))

        params = dict(
            conf = conf,
            title = title,
            presenter = presenter,
            paper_url = paper_url,
            slides_url = slides_url,
            license = license,
            license_text = license_text,
            abstract = abstract,
            source = url,
            year = year,
            date = year
        )

        upload_video(video_url, params,
                     dry_run=dry_run, verbose=verbose,
                     download_flags=download_flags)
    else:
        print("Unknown conference {}".format(conf))
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
    parser.add_argument("url", help="URL")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    parser.add_argument("--slides-only", action="store_true", help="Only download the slides")
    parser.add_argument("--paper-only", action="store_true", help="Only download the paper")
    parser.add_argument("--video-only", action="store_true", help="Only download the video")

    args = parser.parse_args()

    download_slides = args.slides_only or not (args.paper_only or args.video_only)
    download_paper = args.paper_only or not (args.slides_only or args.video_only)
    download_video = args.video_only or not (args.paper_only or args.slides_only)

    download_flags = dict(
        download_slides = download_slides,
        download_paper = download_paper,
        download_video = download_video
    )
    parse_video_page(args.url,
                     verbose=args.verbose,
                     dry_run=args.dry_run,
                     download_flags=download_flags)
