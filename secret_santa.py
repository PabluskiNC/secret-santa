import datetime
import getopt
import random
import re
import smtplib
import socket
import sys
import time

import pytz
import yaml

# sudo pip install pyyaml

help_message = '''
To use, fill out config.yml with your own participants. You can also specify
DONT-PAIR so that people don't get assigned their significant other.

You'll also need to specify your mail server settings. An example is provided
for routing mail through gmail.

For more information, see README.
'''

REQUIRED_CONFIG = (
    'SMTP_SERVER',
    'SMTP_PORT',
    'USERNAME',
    'PASSWORD',
    'TIMEZONE',
    'PARTICIPANTS',
    'DONT-PAIR',
    'DONT-REPEAT',
    'FROM',
    'SUBJECT',
    'MESSAGE',
)

HEADER = """Date: {date}
Content-Type: text/plain; charset="utf-8"
Message-Id: {message_id}
From: {frm}
To: {to}
Subject: {subject}

"""


class Person:
    def __init__(self, name, email, invalid_matches):
        self.name = name
        self.email = email
        self.invalid_matches = invalid_matches

    def __str__(self):
        return "{} <{}> won't give to {}".format(self.name, self.email, self.invalid_matches)


class Pair:
    def __init__(self, giver, receiver):
        self.giver = giver
        self.receiver = receiver

    def __str__(self):
        return "\"{}\" -> \"{}\"".format(self.giver.name, self.receiver.name)


def choose_receiver(giver, receivers):
    choice = random.choice(receivers)
    if choice.name in giver.invalid_matches or giver.name == choice.name:
        if len(receivers) == 1:
            return None
        return choose_receiver(giver, receivers)
    else:
        return choice


def create_pairs(g):
    givers = g[:]
    receivers = g[:]
    pairs = []
    for giver in givers:
        receiver = choose_receiver(giver, receivers)
        if receiver is None:
            print("Oops, hit a dead end, trying again...")
            return create_pairs(g)
        receivers.remove(receiver)
        pairs.append(Pair(giver, receiver))

    return pairs


def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hsc:p:", ["help", "send", "config=", "pairings="])
    except getopt.error as msg:
        print("Error getting options: {}".format(msg))
        return 1

    send = False
    config_yaml = 'config.yml'
    pairings_yaml = 'pairings.yml'
    for option, value in opts:
        if option in ("-h", "--help"):
            print(help_message)
            return 0
        if option in ("-s", "--send"):
            send = True
        if option in ("-c", "--config"):
            config_yaml = value
        if option in ("-p", "--pairings"):
            pairings_yaml = value

    print("Using send={} config={} pairings={}".format(send, config_yaml, pairings_yaml))

    with open(config_yaml) as config_file:
        config = yaml.load(config_file, Loader=yaml.SafeLoader)

    for key in REQUIRED_CONFIG:
        if key not in config.keys():
            print("Required config {} was not found in {}.".format(key, config_yaml))
            return 1

    participants = config['PARTICIPANTS']
    if len(participants) < 2:
        print('Not enough participants specified ({}).'.format(len(participants)))
        raise Exception()

    dont_pair = config['DONT-PAIR']
    print("Don't pair:")
    print(dont_pair)
    dont_repeat = config['DONT-REPEAT']
    print("")
    print("Don't repeat:")
    print(dont_repeat)
    givers = []
    for person in participants:
        name, email = re.match(r'([^<]*)<([^>]*)>', person).groups()
        name = name.strip()
        invalid_matches = []
        for dp in dont_pair:
            names = [n.strip() for n in dp.split(',')]
            if name in names:
                names.remove(name)
                for other_name in names:
                    invalid_matches.append(other_name)
        for dr in dont_repeat:
            names = [n.strip() for n in dr.split(',')]
            if name == names[0]:
                names.remove(name)
                for other_name in names:
                    invalid_matches.append(other_name)

        person = Person(name, email, invalid_matches)
        givers.append(person)

    print()
    print("Loaded givers:")
    for giver in givers:
        print(giver)

    if not send:
        print()
        print("Generating fresh pairings.")
        pairings = create_pairs(givers)

        print()
        print("Pairings:")
        for pairing in pairings:
            print(pairing)

        print()
        print("Writing pairings to {}".format(pairings_yaml))
        pairing_names = {}
        for pairing in pairings:
            pairing_names[pairing.giver.name] = pairing.receiver.name

        with open(pairings_yaml, 'w') as pairings_file:
            yaml.dump(pairing_names, pairings_file)

        return 0

    print()
    print("Loading pairings from {}".format(pairings_yaml))
    with open(pairings_yaml) as pairings_file:
        pairing_names = yaml.load(pairings_file, Loader=yaml.SafeLoader)

    pairings = []
    for giver_name, receiver_name in pairing_names.items():
        giver = next(filter(lambda g: g.name == giver_name, givers), None)
        receiver = next(filter(lambda r: r.name == receiver_name, givers), None)
        pairings.append(Pair(giver, receiver))

    print()
    print("Pairings:")
    for pairing in pairings:
        print(pairing)

    print()
    print("Sending...")

    server = smtplib.SMTP(config['SMTP_SERVER'], config['SMTP_PORT'])
    server.starttls()
    server.login(config['USERNAME'], config['PASSWORD'])
    for pair in pairings:
        zone = pytz.timezone(config['TIMEZONE'])
        now = zone.localize(datetime.datetime.now())
        date = now.strftime('%a, %d %b %Y %T %Z')  # Sun, 21 Dec 2008 06:25:23 +0000
        message_id = '<%s@%s>' % (str(time.time()) + str(random.random()), socket.gethostname())
        frm = config['FROM']
        to = pair.giver.email
        subject = config['SUBJECT'].format(santa=pair.giver.name, santee=pair.receiver.name)
        body = (HEADER + config['MESSAGE']).format(
            date=date,
            message_id=message_id,
            frm=frm,
            to=to,
            subject=subject,
            santa=pair.giver.name,
            santee=pair.receiver.name,
        )
        result = server.sendmail(frm, [to], body)
        print("Emailed {} <{}> -- {}".format(pair.giver.name, to, result))

    server.quit()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
