#!env python

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
from urllib.parse import urlparse
from urllib.request import urlretrieve

from internetarchive import upload

parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
parser.add_argument("url", help="URL")
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")

args = parser.parse_args()
dry_run = args.dry_run
verbose = args.verbose

if verbose is True:
    reporter = lambda count, size, total: print(".", end="", flush=True)
else:
    reporter = None

def linkify(url):
    return '<a href="{}">{}</a>'.format(url, url)

def upload_video(url, params):

#    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = "./downloads"
        source = params['source']
        title = "LAC {} - {}".format(params["year"], params["title"])
        description = "{}\n<b>{}</b>\n<em>{}</em>\n\n{}\n\nOriginal URL: {}\n{}".format(
            params["conf"], params["title"], params["presenter"],
            params["abstract"],
            linkify(source),
            params["license_text"])

        md = dict(title=title,
                  mediatype="movies",
                  collection="opensource_movies",
                  creator="linuxaudio.org",
                  subject=[
                      "linux audio conference",
                      "linux", "audio", "software", "kde", "gnome",
                      "conference", "free software",
                      params['year']
                  ],
                  date = params['year'],
                  year = params['year'],
                  language = 'eng',
                  licenseurl = params['license'],
                  description=description,
                  source=source
        )

        # slides + paper
        # "texts", "opensource"

        print("description {}".format(description))
        print("params {}".format(params))

        u = urlparse(url)
        local_item_file = os.path.basename(u.path)
        (item_id, ext) = os.path.splitext(local_item_file)
        print("Downloading video {}".format(url))
        dest_file = os.path.join(tmpdirname, local_item_file)
        if os.path.exists(dest_file) is False:
            (item_file, headers) = urlretrieve(
                url,
                filename=dest_file,
                reporthook=reporter)
            if verbose is True:
                print("Done")
        else:
            item_file = dest_file
            print("File {} already downloaded".format(dest_file))

        if dry_run is False:
            r = upload(item_id, item_file, metadata=md)
            print("Status {}".format(r[0].status_code))
        else:
            print("Dry run, not uploading video")

        for asset in ["paper_url", "slides_url"]:
            if params[asset] is None:
                continue

            if "bookreader-defaults" in md:
                del md["bookreader-defaults"]
            if "licenseurl" in md:
                del md["licenseurl"]

            if asset == "paper_url":
                subtitle = "Paper"
            elif asset == "slides_url":
                subtitle = "Slides"
                md["bookreader-defaults"] = "mode/1up"

            description = "{}\n{}: <b>{}</b>\n<em>{}</em>\n\n{}\n\nOriginal URL: {}".format(
                params["conf"], subtitle, params["title"], params["presenter"],
                params["abstract"],
                linkify(source))
            md["title"] = "LAC {} - {}: {}".format(params["year"],
                                                   subtitle,
                                                   params["title"])
            md["creator"] = params["presenter"]
            md["mediatype"] = "texts"
            md["collection"] = "opensource"
            md["description"] = description

            print("asset {} description {}".format(asset, description))
            print("asset {} md {}".format(asset, md))

            u = urlparse(params[asset])
            local_item_file = os.path.basename(u.path)
            asset_item_id = "{}_{}".format(item_id, subtitle)
            print("item_id {}".format(asset_item_id))

            dest_file = os.path.join(tmpdirname, local_item_file)
            if os.path.exists(dest_file) is False:
                (item_file, headers) = urlretrieve(
                    params[asset],
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
            else:
                print("Dry run, not uploading {}".format(item_file))


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

if year == "2011" or year == "2012" or year == "2013" or year == "2014":
    # print("Found conference I know")

    result = tree.xpath('//div[@class="title"]/b/text()')
    if len(result) >= 1:
        title = result[0]

    result = tree.xpath('//div[@class="title"]/em/text()')
    if len(result) >= 1:
        presenter = result[0]

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
        source = args.url,
        year = year,
        date = year
    )

    upload_video(video_url, params)
else:
    print("Unknown conference {}".format(conf))
    sys.exit(1)

