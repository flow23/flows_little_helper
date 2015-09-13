#!/usr/bin/python3

from gmail import GMail,GMailWorker,GMailHandler,Message
import configparser
import sys,os
from requests import get
import logging
import logging.handlers

CWD = os.path.dirname(os.path.abspath(__file__))

# debug(), info(), warning(), error() and critical()
def setupLogging():
    logging.basicConfig(format='%(levelname)s %(asctime)s %(module)s.%(funcName)s()[%(lineno)d] %(message)s',
        filename='%s/ip.log' % CWD,
        level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    return logger

def sendMail():
    logger.info('Sending mail to %s', config['GMail']['to'])

    gmail = GMail(config['GMail']['username'],config['GMail']['password'])
    mail = Message(subject='New IP @ KA',
        to=config['GMail']['to'],
        sender='Automatic IP updater',
        text='Reported from: %s\nIP: %s' % (config['General']['hostname'],ip) )
    gmail.send(mail)
    gmail.close()

try:
    logger = setupLogging()

    ip = get('https://api.ipify.org').text
    logger.info('Public IP address %s', ip)

    config = configparser.ConfigParser()
    config.read('ip.cfg')

    if (config['General']['IP'] != ip):
        logger.info('IP address change from %s to %s', config['General']['IP'], ip)
        config['General']['IP'] = ip
        
        sendMail()

        with open('ip.cfg', 'w') as configfile:
            config.write(configfile)
    else:
        logger.info('No IP address change')
except:
    logger.warning('Oh oh %s', sys.exc_info()[0])
