settile.py
==========

A Python script to change the tile page of an Internet Archive text item.

The tile page is the page that show up in the list. Usually we want
the cover, tbut the automation on Internet Archive doesn't always
think so.

So I wrote a tool to do it.

Installation
------------

You need the `internetarchive` Python module. See:

https://github.com/jjjake/internetarchive
https://archive.org/services/docs/api/internetarchive/quickstart.html

Then you need to configure it:

$ ia configure

Will ask for your Internet Archive credentials. These are the one
settile will use.


Usage
-----


$ settile.py ID

This will set the tile to page 0 for the item ID.

* ID is either the item ID or the Internet Archive URL.
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