#!/bin/python3

from gmail import GMail,GMailWorker,GMailHandler,Message
import configparser
import sys
from requests import get
import logging
import logging.handlers

# debug(), info(), warning(), error() and critical()
def setupLogging():
    logging.basicConfig(filename='ip.log',level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # File handler for /var/log/some.log
    #serverlog = logging.FileHandler('/var/log/some.log')
    #serverlog.setLevel(logging.DEBUG)
    #serverlog.setFormatter(logging.Formatter(
    #    '%(asctime)s %(pathname)s [%(process)d]: %(levelname)s %(message)s'))

    # Syslog handler
    #syslog = logging.handlers.SysLogHandler(address='/dev/log')
    #syslog.setLevel(logging.WARNING)
    #syslog.setFormatter(logging.Formatter(
    #    '%(pathname)s [%(process)d]: %(levelname)s %(message)s'))

    # Combined logger used elsewhere in the script
    #logger = logging.getLogger('wbs-server-log')
    #logger.setLevel(logging.DEBUG)
    #logger.addHandler(serverlog)
    #logger.addHandler(syslog)

    return logger

try:
    logger = setupLogging()
    ip = get('https://api.ipify.org').text
    logger.info('My public IP address is %s', ip)

    config = configparser.ConfigParser()
    #settings._interpolation = configparser.ExtendedInterpolation()
    config.read('ip.cfg')

    if (config['General']['IP'] != ip):
        logger.info('IP address change from %s to %s', ['General']['IP'], ip)
        config['General']['IP'] = ip
        
        logger.info('Sending mail')
        gmail = GMail(config['GMail']['username'],config['GMail']['password'])
        mail = Message(subject='New IP @ KA',
                       to='florian.wallburg@web.de',
                       sender='Automatic IP updater',
                       text='Reported from: %s\nIP: %s' % (config['General']['hostname'],ip) )
        gmail.send(mail)
        gmail.close()
        with open('ip.cfg', 'w') as configfile:    # save
            config.write(configfile)
    else:
        logger.info('No IP address change')
except:
    logger.warning('Oh oh %s', sys.exc_info()[0])
