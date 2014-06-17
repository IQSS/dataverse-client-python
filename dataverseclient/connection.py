"""
Wrapper around the sword2.Connection class.
"""

# python base lib modules

#downloaded modules
import sword2

#local modules
from dataverse import Dataverse


class DvnConnection(object):

    def __init__(self, username, password, host, cert=None, disable_ssl=False):
        # Connection Properties
        self.username = username
        self.password = password
        self.host = host
        self.cert = cert
        self.disable_ssl = disable_ssl
        self.sd_uri = "https://{host}/dvn/api/data-deposit/v1/swordv2/service-document".format(host=self.host)
        
        # Connection Status and SWORD Properties
        self.sword = None
        self.status = None
        self.connected = False
        
        self.connect()

    def connect(self):
        self.sword = sword2.Connection(
            service_document_iri=self.sd_uri,
            user_name=self.username,
            user_pass=self.password,
            ca_certs=self.cert,
            disable_ssl_certificate_validation=self.disable_ssl,
        )

        # Update history with data retrieval attempt
        self.sword.get_service_document()
        self.status = self.sword.history[1]['payload']['response']['status']
        self.connected = True if self.status == 200 else False
        
    def get_dataverses(self):
        # Get latest dataverse information
        self.connect()

        # Note: All SWORD collections are stored in the 0th workspace
        _, collections = self.sword.workspaces[0]

        # Cast SWORD collections to Dataverses
        return [Dataverse(self, col) for col in collections]

    def get_dataverse(self, alias):
        return next((dataverse for dataverse in self.get_dataverses()
                     if dataverse.alias == alias), None)
