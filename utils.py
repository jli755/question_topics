"""
Functions that will be used for all scripts
"""

from itertools import chain, combinations
import re


def rm_text_please(original_text, ignore_ls):
    """
    remove a sentence (from ignore_ls) from a string (original_text)

    orginal_text:
        original string

    ignore_ls:
        a list

    output: new_text
    """
    
    # Removes the brackets and everything inside them
    #rm_curling_brackets = re.sub(r'\{.*?\}', '', original_text)
    #result = re.sub(r'\[.*?\]', '', rm_curling_brackets)
    
    # Replace "^" with an empty string
    clean_text = original_text.replace("^", "")

    # Regex Approach: For better performance with many replacements, join the list into a regular expression pattern.
    pattern = "|".join(ignore_ls)
    new_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE)
    return new_text


def powerset(s):
    """
    items contains 2 items all then way to all items
    return all combination of a list, range(1, len(s_list) + 1)
    note that range(0, len(s_list) + 1) will include an empty set
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    return list(chain.from_iterable(combinations(s_list, r) for r in range(2, len(s_list) + 1)))


def powerset_4_5(s):
    """
    return n elements from combination of a list
    contains 2 and 3 items
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    # this returns n words combination
    out_list = list(chain.from_iterable(combinations(s_list, r) for r in (range(4, 6))))

    return sorted(out_list)


def powerset_n(s, n):
    """
    return n elements from combination of a list, (range(n,n+1))
    """
    s_list = list(s) # Sets must be converted to lists for indexing
    # this returns n words combination
    out_list = list(chain.from_iterable(combinations(s_list, r) for r in (range(n, n+1))))

    return sorted(out_list)
