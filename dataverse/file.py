__author__="peterbull"
__date__ ="$Aug 16, 2013 12:32:24 PM$"

# python base lib modules
from datetime import datetime
import urlparse

#downloaded modules
import sword2

#local modules
import utils


class DataverseFile(object):
    def __init__(self, name, study, edit_media_uri=None, download_url=None):
        self.name = utils.sanitize(name)
        self.study = study

        if edit_media_uri:
            self.is_released = False
            self.edit_media_uri = edit_media_uri
            self.id = edit_media_uri.split('/')[-2]
            host = urlparse.urlparse(edit_media_uri).netloc
            self.download_url = 'http://{0}/dvn/FileDownload/?fileId={1}'.format(host, self.id)
        elif download_url:
            self.is_released = True
            self.download_url = download_url
            self.id = download_url.split('=')[-1]
        else:
            raise utils.DataverseException(
                'Files must have an edit media uri or download url.'
            )

    def __repr__(self):
        return """
    DATAVERSE FILE:
    Name: {0}
    Id: {1}
    Download URL: {2}
    Status: {3}
    """.format(
            self.name,
            self.id,
            self.download_url,
            self.edit_media_uri,
            'RELEASED' if self.is_released else 'DRAFT',
        )

    @classmethod
    def from_statement(cls, resource, study):
        edit_media_uri = resource.cont_iri
        name = edit_media_uri.rsplit("/")[-1]
        return cls(name, study, edit_media_uri)

    @classmethod
    def from_metadata(cls, element, study):
        name = element[0].text
        download_url = element.attrib.get('URI')
        return cls(name, study, download_url)