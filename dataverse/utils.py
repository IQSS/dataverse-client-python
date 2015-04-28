import os

from lxml import etree
import bleach

from settings import SWORD_NAMESPACE, REPLACEMENT_DICT, UNIQUE_FIELDS


# factor out xpath operations so we don't have to look at its ugliness
def get_element(root, tag='*', namespace=None, attribute=None, attribute_value=None):
    elements = get_elements(root, tag, namespace, attribute, attribute_value)
    return elements[0] if elements else None


def get_elements(root, tag='*', namespace=None, attribute=None, attribute_value=None):

    # If string, convert to etree element
    if isinstance(root, str):
        root = etree.XML(root)

    namespace = root.nsmap.get(namespace, namespace)

    if namespace is None:
        xpath = tag
    else:
        xpath = '{{{ns}}}{tag}'.format(ns=namespace, tag=tag)

    if attribute and not attribute_value:
        xpath += '[@{att}]'.format(att=attribute)
    elif not attribute and attribute_value:
        raise Exception('You must pass an attribute with attribute_value')
    elif attribute and attribute_value:
        xpath += "[@{att}='{val}']".format(att=attribute, val=attribute_value)

    return root.findall(xpath)


def format_term(term, namespace):

    if term in REPLACEMENT_DICT:
        term = REPLACEMENT_DICT[term]

    return '{{{0}}}{1}'.format(SWORD_NAMESPACE[namespace], term)


def add_field(entry, key, value, namespace='dcterms'):

    formatted_key = format_term(key, namespace)
    element = entry.find(formatted_key) if key in UNIQUE_FIELDS else None

    if element is None:
        element = etree.SubElement(entry, formatted_key, nsmap=SWORD_NAMESPACE)

    element.text = value


# def add_author(entry, formatted_key, author, namespace):
#
#     # TODO Accept base strings?
#
#     author_element = etree.SubElement(entry, formatted_key, nsmap=SWORD_NAMESPACE)
#
#     name_element = etree.SubElement(
#         author_element,
#         format_term('name', namespace),
#         nsmap=SWORD_NAMESPACE,
#     )
#     name_element.text = author.get('name')
#
#     if author.get('uri'):
#         uri_element = etree.SubElement(
#             author_element,
#             format_term('uri', namespace),
#             nsmap=SWORD_NAMESPACE,
#         )
#         uri_element.text = author.get('uri')
#
#     if author.get('email'):
#         email_element = etree.SubElement(
#             author_element,
#             format_term('email', namespace),
#             nsmap=SWORD_NAMESPACE,
#         )
#         email_element.text = author.get('email')


def get_files_in_path(path):
    path = os.path.normpath(path) + os.sep
    filepaths = []
    for filename in os.listdir(path):
        filepath = path + filename
        if os.path.isdir(filepath):
            filepaths += get_files_in_path(filepath)
        else:
            filepaths.append(filepath)
    return filepaths


def sanitize(value):
    return bleach.clean(value, strip=True, tags=[], attributes=[], styles=[])
