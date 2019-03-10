#!env python2.7

# Not Python 3????

import string
import sys
import argparse
from xml.dom import minidom
from internetarchive import get_item

URL_BASE = "https://archive.org/details/"

parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
parser.add_argument("item_id", help="Item ID or URL")
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")
parser.add_argument("-p", type=int, help="The page to set as tile (default=0)", default=0)

args = parser.parse_args()

item_id = args.item_id
if string.find(item_id, URL_BASE) == 0:
    item_id = string.replace(item_id, URL_BASE, "")

item = get_item(item_id)
if item is None:
    print("Item not found.")
    sys.exit(1)

fnames = [f.name for f in item.get_files(glob_pattern='*_scandata.xml')]
if len(fnames) > 1:
    print("Too many scandata, abort.")
    sys.exit(1)
elif len(fnames) < 1:
    print("Scandata not found.")
    sys.exit(1)

scandata_file = fnames[0]

if item.download(scandata_file, no_directory=True) is False:
    print("Download failed")
    sys.exit(1)

modified = False
xmldoc = minidom.parse(scandata_file)
if xmldoc is None:
    print("Couldn't parse scandata file")
    sys.exit(1)

pages = xmldoc.getElementsByTagName("page")
if len(pages) == 0:
    print("No pages found")
    sys.exit(1)

for page in pages:
    pageNum = int(page.attributes["leafNum"].value)
    pageType = page.getElementsByTagName("pageType")

    if len(pageType) == 0:
        print("Can't find page type")
        sys.exit(1)

    f = pageType[0].firstChild
    if pageNum == args.p:
        if f.data != u"Title":
            modified = True
            t = xmldoc.createTextNode(u"Title")
            pageType[0].replaceChild(t, f)
    elif f.data == u"Title":
        modified = True
        t = xmldoc.createTextNode(u"Normal")
        pageType[0].replaceChild(t, f)

if modified:
    out_xml = xmldoc.toprettyxml(indent="", newl="", encoding="utf-8")
    if args.dry_run:
        print(out_xml)
    else:
        new_file = scandata_file + "_new"
        f = open(new_file, "w")
        f.write(out_xml)
        f.close()
        item.upload({scandata_file: new_file})
else:
    print("Not modified")

