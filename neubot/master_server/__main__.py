""" Main function """

import logging

from .rendezvous import RendezvousHandler

from tornado.web import Application
from tornado.ioloop import IOLoop

def main():
    """ Main function """
    logging.basicConfig(level=logging.DEBUG)
    application = Application((
        (r"/rendezvous", RendezvousHandler, {
            "conf": {
                "rendezvous.server.update_version": "0.4.16.9",
                "rendezvous.server.default": "master.neubot.org",
            }
        }),
    ))
    for port in 9773, 8080:
        application.listen(port)
    IOLoop.current().start()

if __name__ == "__main__":
    main()
