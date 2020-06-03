#
# Licensed under GPL-3.0 or later
#

from urllib.parse import urljoin

def parse_program(tree, url=None, verbose=False):
    program = []

    results = tree.xpath("//main/div[@class=\"container\"]/div/div/h2[@id=\"program\"]/following-sibling::table/tbody/tr")
    print("found {} table items".format(len(results)))
    for result in results:

        title = None
        presenter = None
        video_url = None
        video2_url = None
        paper_url = None

        t = result.get("class")
        cols = result.xpath("td")
        if len(cols) == 0:
            continue

        if len(cols) >= 5:
            n = cols[1].xpath("a/@href")
            if len(n) > 0:
                paper_url = urljoin(url, n[0])
            n = cols[1].xpath("text()")
            if len(n) >= 1:
                title = n[0].strip()
            presenter = cols[2].text
            n = cols[4].xpath("a/@href")
            if len(n) > 0:
                video_url = urljoin(url, n[0])
            if len(n) > 1:
                video2_url = urljoin(url, n[1])
        else:
            ocols = cols[0].xpath("preceding-sibling::th")
            if len(ocols) != 2:
                continue

            colspan = ocols[1].get("colspan")
            title = ocols[1].text
            # depending on the colspan of the title
            video_index = 3 - int(colspan)
            n = cols[video_index].xpath("a/@href")
            if len(n) > 0:
                video_url = urljoin(url, n[0])
            if len(n) > 1:
                video2_url = urljoin(url, n[1])

        params = dict(
            conf = "Linux Audio Conference 2019",
            title = title,
            presenter = presenter,
            source = None,
            abstract = title,
            video_url = video_url,
            video2_url = video2_url,
            paper_url = paper_url,
            slides_url = None,
            audio_url = None,
            misc_url = None,
            license_text = "",
            license = None,
            year = "2019",
            date = "2019-03"
        )
        program.append(params)

    return program

