__author__="peterbull"
__date__ ="$Aug 16, 2013 12:32:24 PM$"

# python base lib modules
from datetime import datetime
import urlparse

#downloaded modules
import sword2

#local modules
import utils


class DraftFile(object):
    def __init__(self, name, edit_media_uri, updated, study):
        self.name = utils.sanitize(name)
        self.edit_media_uri = edit_media_uri
        self.updated = updated
        self.study = study
        self.id = edit_media_uri.split('/')[-2]

        host = urlparse.urlparse(edit_media_uri).netloc
        self.download_url = 'http://{0}/dvn/FileDownload/?fileId={1}'.format(
            host, self.id
        )
        
    def __repr__(self):
        return """
    DATAVERSE FILE:
    Name: {0}
    Id: {1}
    Download URL: {2}
    Status: DRAFT
    """.format(self.name, self.id, self.download_url, self.edit_media_uri)

    @classmethod
    def from_statement(cls, statement, study):
        uri = statement.cont_iri
        name = uri.rsplit("/")[-1]
        # Note: Updated element is meaningless at the moment
        updated = datetime.strptime(statement.updated, "%Y-%m-%dT%H:%M:%S.%fZ")
        return cls(name, uri,  updated, study)


class ReleasedFile(object):
    def __init__(self, name, download_url, study):
        self.name = utils.sanitize(name)
        self.download_url = download_url
        self.study = study
        self.id = download_url.split('=')[-1]

    def __repr__(self):
        return """
    DATAVERSE FILE:
    Name: {0}
    Id: {1}
    Download URL: {2}
    Status: RELEASED
    """.format(self.name, self.id, self.download_url)