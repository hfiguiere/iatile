#!env python2.7

# Not Python 3????

import sys
import argparse
from xml.dom import minidom
from internetarchive import download, get_item, get_files

URL_BASE = "https://archive.org/details/"

parser = argparse.ArgumentParser(description="Set tile for Internet Archive item")
parser.add_argument("item_id", help="Item ID")
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run")
parser.add_argument("-p", type=int, help="The page to set as tile (default=0)", default=0)

args = parser.parse_args()

item = get_item(args.item_id)

fnames = [f.name for f in get_files(args.item_id, glob_pattern='*_scandata.xml')]
print(fnames)
if len(fnames) != 1:
    print("Too many scandata, abort.")
    sys.exit(1)

scandata_file = fnames[0]

if download(args.item_id, scandata_file, no_directory=True) is False:
    print("Download failed")
    sys.exit(1)

modified = False
xmldoc = minidom.parse(scandata_file)
pages = xmldoc.getElementsByTagName("page")

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

