""" Geolocation routines """

def lookup_country(address):
    """ Lookup country from user's address """
    return "IT"

def lookup_servers(country):
    """ Lookup best servers for country """
    return [
        "neubot.mlab.mlab1.trn01.measurement-lab.org",
        "neubot.mlab.mlab2.trn01.measurement-lab.org",
    ]
