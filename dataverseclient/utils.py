__author__="peterbull"
__date__ ="$Aug 16, 2013 12:07:48 PM$"

from lxml import etree
import bleach

REPLACEMENT_DICT = {'id': 'identifier', 'author': 'creator', 'producer': 'publisher', 'restriction': 'rights',
                    'keyword': 'subject', 'publication': 'isReferencedBy'}


class DataverseException(Exception):
    pass


# factor out xpath operations so we don't have to look at its ugliness
def get_element(root, tag=None, namespace=None, attribute=None, attribute_value=None):
    elements = get_elements(root, tag, namespace, attribute, attribute_value)
    return elements[0] if elements else None


def get_elements(root, tag=None, namespace=None, attribute=None, attribute_value=None):
    # accept either an lxml.Element or a string of xml
    # if a string, convert to etree element
    if isinstance(root, str):
        root = etree.XML(root)

    try:
        namespace = root.nsmap[namespace]
    except KeyError:
        # namespace not expressed in map; use literal
        pass

    if not tag:
        xpath = "*"
    elif namespace is None:
        xpath = tag
    else:
        xpath = "{{{ns}}}{tag}".format(ns=namespace, tag=tag)

    if attribute and not attribute_value:
        xpath += "[@{att}]".format(att=attribute)
    elif not attribute and attribute_value:
        raise Exception("You must pass an attribute with attribute_value")
    elif attribute and attribute_value:
        xpath += "[@{att}='{val}']".format(att=attribute, val=attribute_value)

    return root.findall(xpath)


def format_term(term):
    if term in REPLACEMENT_DICT.keys():
        return 'dcterms_{0}'.format(REPLACEMENT_DICT[term])
    else:
        return 'dcterms_{0}'.format(term)


def sanitize(value):
    return bleach.clean(value, strip=True, tags=[], attributes=[], styles=[])