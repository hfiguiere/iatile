lacupload.py
============

A Python script to upload the Linux Audio Conference videos to
Internet Archive. With metadata.

Currently supported are Linux Audio Conference from 2010 to 2015.

**If you are reading this, it is likely it doesn't need to be used
anymore as everything has been uploaded to the Internet Archive**

`scrape_lac.py` is designed to scrape the program page to fetch all
the conference program items.

`lacupload.py` will upload the items from a video page. It is used
either as is or from `scrape_lac.py`.

Both have command line arguments. `-n` or `--dry-run` will not upload
to the internet archive, but otherwise will download. So running with
`-n` and then without will download first all items, then upload them.

settile.py
==========

A Python script to change the tile page of an Internet Archive text item.

The tile page is the page that shows up in the list as a
thumbnail. Usually we want the cover, but the automation on Internet
Archive doesn't always think so, and there is no easy way to change
this.

So I wrote a tool to do it.

Installation
------------

You need the `internetarchive` Python module. See:

https://github.com/jjjake/internetarchive
https://archive.org/services/docs/api/internetarchive/quickstart.html

Ideally you'd use a venv.
```
 $ python3 -m venv venv
 $ source ./venv/bin/activate
 $ pip install internetarchive
```
Then you need to configure it:
```
 $ ia configure
```
Will ask for your Internet Archive credentials. These are the one
`settile` will use.

Usage
-----
```
$ settile.py ID
```
This will set the tile to page 0 for the item ID.

* `ID` is either the item ID or the Internet Archive URL.
* Use `-n` or `--dry-run` for trying without saving
* Pass `-p N` to set the tile to page N

Author
------

Hubert Figuiere <hub@figuiere.net>

Contributing
------------

This tool is currently hosted on github.

https://github.com/hfiguiere/iatile

License
-------

This script is GPL-3+. See `COPYING` for the standard GPL-3.0 license
text.
