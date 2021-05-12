import re


def get_range(group_adress_range: str):
    pattern = r"\[.*\]"
    first, last = re.search(pattern, group_adress_range).span()
    first += 1
    last -= 1
    start, end = group_adress_range[first:last].split("-")
    start = int(start)
    end = int(end)
    assert start <= end, f"Eroare in compliarea grup adresei {group_adress_range}, formatul este numar/numar/[minim-maxim] , minim , maxim inclusiv"
    return range(start, end + 1)
