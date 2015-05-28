""" Handles /rendezvous API """

import json
import logging
import random

from tornado.web import RequestHandler
from tornado.web import stream_request_body

from .import geoloc
from .import privacy

from ..utils import utils_version

LOGGER = logging.getLogger("rendezvous")

@stream_request_body
class RendezvousHandler(RequestHandler):
    """ Handles /rendezvous API """

    def initialize(self, conf):
        self._conf = conf

    def prepare(self):
        self._body = []
        self._total = 0

    def data_received(self, data):
        self._body.append(data)
        self._total += len(data)
        # TODO: Add limit on maximum body length

    def get(self):
        self.post()

    def post(self):

        mimetype = self.request.headers.get("Content-Type", "")
        if mimetype == "application/json":
            body = b"".join(self._body).decode("utf-8")
            request = json.loads(body)
        else:
            request = {}

        reply = {
            "available": {},
            "update": {},
        }

        #
        # If we don't say anything the rendezvous server is not
        # going to prompt for updates.  We need to specify the
        # updated version number explicitly when we start it up.
        # This should guarantee that we do not advertise -rc
        # releases and other weird things.
        #
        version = self._conf["rendezvous.server.update_version"]
        if version and "version" in request:
            diff = utils_version.compare(version, request["version"])
            LOGGER.debug('version=%s req["version"]=%s diff=%f',
                         version, request["version"], diff)
            if diff > 0:
                reply["update"] = {
                    "uri": "http://neubot.org/",
                    "version": version,
                }

        #
        # Select test server address.
        # The default test server is the master server itself.
        # If we know the country, lookup the list of servers for
        # that country in the database.
        # We only redirect to other servers clients that have
        # agreed to give us the permission to publish, in order
        # to be compliant with M-Lab policy.
        # If there are no servers for that country, register
        # the master server for the country so that we can notice
        # we have new users and can take the proper steps to
        # deploy nearby servers.
        #
        server = self._conf["rendezvous.server.default"]
        LOGGER.debug("default test server: %s", server)

        #
        # Backward compatibility: the variable name changed from
        # can_share to can_publish after Neubot 0.4.5
        #
        if 'privacy_can_share' in request:
            request['privacy_can_publish'] = request['privacy_can_share']
            del request['privacy_can_share']

        # Redirect IFF have ALL privacy permissions
        if privacy.count_valid(request, 'privacy_') == 3:
            address = self.request.remote_ip
            country = geoloc.lookup_country(address)
            if country:
                servers = geoloc.lookup_servers(country)
                if servers:
                    server = random.choice(servers)
                LOGGER.info("%s[%s] -> %s", address, country, server)
        else:
            LOGGER.warning('cannot redirect: %s', request)

        #
        # We require at least informed and can_collect since 0.4.4
        # (released 25 October 2011), so stop clients with empty
        # privacy settings, who were still using master.
        #
        if privacy.collect_allowed(request):
            #
            # Note: Here we will have problems if we store unquoted
            # IPv6 addresses into the database.  Because the resulting
            # URI won't be valid.
            #
            if "speedtest" in request["accept"]:
                reply["available"]["speedtest"] = [
                    "http://%s/speedtest" % server
                ]
            if "bittorrent" in request["accept"]:
                reply["available"]["bittorrent"] = [
                    "http://%s/" % server
                ]

        #
        # Neubot <=0.3.7 expects to receive an XML document; as of Neubot
        # 0.4 (20 July 2011) JSON is used. As of 28 May 2015 we have removed
        # support for receiving and sending XML documents.
        #
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(reply))
