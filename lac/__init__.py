
import re
from internetarchive import get_item

#
# Turn a title to an id
#
def idify_title(title):
    return re.sub(r"[^0-9a-zA-Z]", "", title.title())

#
# Turn an url to HTML markup link
#
# Doesn't validate the url
def linkify(url):
    if url is None:
        return ""
    return '<a href="{}">{}</a>'.format(url, url)


#
# Ensure the item_id is unused.
# retry = retry mode: don't try to find a new ID
#
# Return the unused item_id or None
#
def ensure_item_id(item_id, retry=False):
    # Shrink to 70 chars. IA has a hard limit to 100.
    item_id = item_id[:70]
    while len(get_item(item_id).item_metadata) != 0:
        if retry:
            return None
        l = len(item_id)
        if l <= 12:
            return None
        item_id = item_id[:l - 1]

    return item_id


#
# Return true if the video_url is a video page.
#
def is_video_page(url):
    if url is None:
        return False
    return re.match(r".*/video\.php\?id=[\d]*$", url)
