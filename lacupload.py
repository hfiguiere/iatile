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


def upload_video(url, params):

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = params['source']
        title = "LAC {} - {}".format(params["year"], params["title"])
        description = "{}\n{}\n{}\n\n{}\n\nOriginal URL: {}\n{}".format(
            params["conf"], params["title"], params["presenter"],
            params["abstract"],
            source,
            params["license_text"])

        md = dict(title=title,
                  mediatype="movie",
                  collection="opensource_movies",
                  creator="linuxaudio.org",
                  subject=[
                      "linux", "audio", "software", "kde", "gnome",
                      "conference", "free software", "linux audio conference",
                      params['year']
                  ],
                  date = params['year'],
                  language = 'eng',
                  license = params['license'],
                  description=description,
                  source=params['source']
        )

        # slides + paper
        # "texts", "opensource"

        print("video url = {}".format(url))
        print("description {}".format(description))
        print("params {}".format(params))

        u = urlparse(url)
        local_item_file = os.path.basename(u.path)
        (item_id, ext) = os.path.splitext(local_item_file)
        (item_file, headers) = urlretrieve(url, filename=os.path.join(tmpdirname, local_item_file))
        # print("item_file {}".format(item_file))
        r = upload(item_id, item_file, metadata=md)

        for asset in ["paper_url", "slides_url"]:
            if params[asset] is None:
                continue

            if "bookreader-defaults" in md:
                del md["bookreader-defaults"]
            if "license" in md:
                del md["license"]

            if asset == "paper_url":
                subtitle = "Paper"
            elif asset == "slides_url":
                subtitle = "Slides"
                md["bookreader-defaults"] = "mode/1up"

            description = "{}\n{}: {}\n{}\n\n{}\n\nOriginal URL: {}".format(
                params["conf"], subtitle, params["title"], params["presenter"],
                params["abstract"],
                source)

            md["mediatype"] = "texts"
            md["collection"] = "opensource"
            md["description"] = description

            print("asset {} description {}".format(asset, description))
            print("asset {} md {}".format(asset, md))

            u = urlparse(params[asset])
            local_item_file = os.path.basename(u.path)
            asset_item_id = "{}_{}".format(item_id, subtitle)
            print("item_id {}".format(asset_item_id))

            (item_file, headers) = urlretrieve(
                params[asset],
                filename=os.path.join(tmpdirname, local_item_file)
            )
            print("item_file {}".format(item_file))
            upload(asset_item_id, item_file, metadata=md)


parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
parser.add_argument("url", help="URL")
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")

args = parser.parse_args()

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
        abstract = None
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

