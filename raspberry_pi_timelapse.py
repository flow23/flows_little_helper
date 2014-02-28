#!/usr/bin/env python

import logging
import optparse
import os
import time
import sys

from PIL import Image, ImageDraw, ImageFont  
from PIL.ExifTags import TAGS  

# CRITICAL < ERROR < WARNING < INFO < DEBUG < NOTSET
LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

PREFIX = "flow_"
global FPS_IN
global TIMESTAMP_IMAGE_DIR
FPS_IN = 10
FPS_OUT = 24
TIMEBETWEEN = 15 # 4 pictures per minute
global FILMLENGTH
global SCP_USER
global SCP_HOST
global SCP_DIRECTORY
SCP_USER = "user"
SCP_HOST = "0.0.0.0"
SCP_DIRECTORY = "/volume1/public/"

def main():
  '''Main class'''
  global FRAMES
  global DEMO_MODE
  global OVERRIDE
  global SCP
  global CLEANING
  global TIMELAPSE_FILENAME
  global DATE

  # optparse is deprecated since 2.7, use argparse
  parser = optparse.OptionParser()
  parser.add_option('-l', '--logging-level', help='Logging level')
  parser.add_option('-f', '--logging-file', help='Logging file name')
  parser.add_option('-x', '--frames', help='Frames to catch')
  parser.add_option('-d', '--demo', help='Demo mode', action='store_true', default=False)
  parser.add_option('-o', '--override', help='Overrides taken image with timestamp image', action='store_true', default=False)
  parser.add_option('-s', '--scp', help='Transfer timelapse to another machine', action='store_true', default=False)
  parser.add_option('-c', '--clean', help='Cleaning images and timestamp images alike', action='store_true', default=False)
  (options, args) = parser.parse_args()
  logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
  logging.basicConfig(level=logging_level, filename=options.logging_file,
                      format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

  logging.info("begin main()")
  
  logging.debug("Options: %s"%(options))

  if options.frames is None:
    FRAMES = 1920 # 4/m * 60m *8h 
  else:
    FRAMES = int(options.frames)

  DEMO_MODE = options.demo
  OVERRIDE = options.override
  SCP = options.scp
  CLEANING = options.clean   
  TIMELAPSE_FILENAME = time.strftime("timelapse_%Y%m%d_%H%M%S", time.localtime())  + ".mp4"
  DATE = time.strftime("%Y%m%d", time.localtime())

  logging.info("end main()")
  
def takingPhotos():
  '''Takes image via raspistill'''
  FILMLENGTH = float(FRAMES / FPS_IN)

  logging.info("begin takingPhotos()")
  logging.debug("Prefix: %s" % (PREFIX))
  logging.debug("Date: %s" % (DATE))
  logging.debug("Frames: %s" % (FRAMES))
  logging.debug("FPS in: %s" % (FPS_IN))
  logging.debug("FPS out: %s" % (FPS_OUT))
  logging.debug("Time between pictures: %s" % (TIMEBETWEEN))
  logging.debug("Length of film: %s" % (FILMLENGTH))

  frameCount = 1
  while frameCount < FRAMES+1:
    imageNumber = str(frameCount).zfill(7)
    logging.debug("Image number: %s" % imageNumber)
    if DEMO_MODE is False:
      try:
        os.system("raspistill -o %simage_%s_%s.jpg" % (PREFIX,DATE,imageNumber))
      except Exception, e:
        logging.error(e)

    frameCount += 1
    time.sleep(TIMEBETWEEN - 7) #Takes roughly 6 seconds to take a picture, 7 seconds on a USB drive
  
  logging.info("end takingPhotos()")

def creatingTimelapse(image_dir):
  '''Creates timelapse using avconv'''
  logging.debug("begin creatingTimelapse(%s)"%(image_dir))

  logging.info("Timelapse filename: %s" % (TIMELAPSE_FILENAME))
  # Actual image is 2592x1944
  #os.system("nice -n 19 avconv -r %s -i %s/%simage%s.jpg -r %s -vcodec libx264 -crf 20 -g 15 -vf crop=2592:1458,scale=1280:720 %s"%(FPS_IN, image_dir, PREFIX, '%07d',FPS_OUT,TIMELAPSE_FILENAME))
  # Added -y to override latest timelapse if exists
  os.system("nice -n 19 avconv -y -v quiet -r %s -i %s/%simage_%s_%s.jpg -r %s -vcodec libx264 -crf 20 -g 15 -vf scale=1280:720 %s"%(FPS_IN, image_dir, PREFIX, DATE, '%07d', FPS_OUT, TIMELAPSE_FILENAME))

  logging.debug("end creatingTimelapse(%s)"%(image_dir))

def scp(user,host,directory):
  '''Transfers timelapse via scp to another machine, ssh-keygen and ssh-copy-id needed'''
  logging.debug("begin scp(%s, %s, %s)"%(user, host, directory))
 
  logging.info("Transfering %s"%(TIMELAPSE_FILENAME))
  os.system("scp -q -i %s %s %s@%s:%s"%("/home/pi/.ssh/id_dsa", TIMELAPSE_FILENAME, user, host, directory))
  
  logging.debug("end scp(%s, %s, %s)"%(user, host, directory))

def cleaning():
  '''Cleans all images and timelapse'''
  logging.debug("begin cleaning()")

  logging.info("Cleaning up...")
  
  if OVERRIDE is False:
    os.system("nice -n 19 rm -Rf %s"%(TIMESTAMP_IMAGE_DIR))

  os.system("nice -n 19 rm -Rf %simage_%s_*.jpg" % (PREFIX,DATE))
  os.system("nice -n 19 rm -Rf %s" % (TIMELAPSE_FILENAME))
  
  logging.debug("end cleaning()")

def get_exif(fn):  
  '''Returns all EXIF data as dictionary'''
  logging.debug("begin get_exif(%s)"%(fn))

  ret = {}  
  i = Image.open(fn)  
  info = i._getexif()  
  try:  
    for tag, value in info.items():  
      decoded = TAGS.get(tag, tag)  
      ret[decoded] = value  
  except:  
    pass

  logging.debug("end get_exif()")
  
  return ret

def get_datetime(fn):  
  '''Returns string of year, month, day, hour, minute and second'''  
  logging.info("begin get_datetime(%s)"%(fn))

  try:  
    raw = get_exif(fn)['DateTime']  
  except:  
    raw='??????????????????????'  
  date = {'year': raw[0:4], 'month':raw[5:7], 'day':raw[8:10],\
         'hour':raw[11:13], 'minute':raw[14:16], 'second':raw[17:19]}  
  datetime = str(date['day']) + '-' + str(date['month']) + '-' + \
        str(date['year']) + ' ' + str(date['hour']) + ':' + \
        str(date['minute']) # format timestamp 

  logging.info("end get_datetime(%s) -> %s"%(fn,datetime)) 
  
  return datetime

def timestampPhotos():
  '''Adds timestamp to immage'''
  global TIMESTAMP_IMAGE_DIR

  logging.info("begin timestampPhotos()")

  mainDir = os.getcwd() # current working dir  
  fileList = os.listdir(mainDir)    # list of files in current dir  
  fileList = [os.path.normcase(f) for f in fileList]   # normal case  
  # keep only files ending with .jpg  
  fileList = [ f for f in fileList if '.jpg' in os.path.splitext(f)[1]]  
  try:
    logging.debug("Getting image informatiom from file: %s"%(fileList[0]))
    i = Image.open(fileList[0])  
    imageWidth = i.size[0]  # get width of first image  
    imageHeight = i.size[1]  
  except Exception, e:
    logging.error(e)
  fontPath = "/usr/share/fonts/truetype/freefont/FreeSans.ttf" # font file path  
  myFont = ImageFont.truetype ( fontPath, imageWidth/40 ) # load font and size  
  (textWidth, textHeight) = myFont.getsize('00-00-0000 00:00')  # get size of timestamp  
  x = imageWidth - textWidth - 50  # position of text  
  y = imageHeight - textHeight - 50

  if OVERRIDE is False:
    print 'Now creating',str(len(fileList)),'frames in folder', \
      time.strftime('"Frames_%Y%m%d_%H%M%S".', time.localtime())  
    # make new dir  
    newDir = os.path.join(mainDir, time.strftime("Frames_%Y%m%d_%H%M%S", time.localtime()))
    TIMESTAMP_IMAGE_DIR = newDir
    os.mkdir(newDir)
  else:
    TIMESTAMP_IMAGE_DIR = mainDir
    logging.debug("Now creating %s timestamp images in current folder"%(str(len(fileList))))
  
  # sorting file list alphabetical
  fileList.sort()

  for n in range(0,len(fileList)):  
    logging.debug("Timestamping image %s"%(fileList[n]))

    # open image from list
    i = Image.open(fileList[n])  
    draw = ImageDraw.Draw ( i )  
    # thin border
    imageDatetimeFromEXIF = get_datetime(fileList[n])
    draw.text((x-1, y-1), imageDatetimeFromEXIF, font=myFont, fill='black')  
    draw.text((x+1, y-1), imageDatetimeFromEXIF, font=myFont, fill='black')  
    draw.text((x-1, y+1), imageDatetimeFromEXIF, font=myFont, fill='black')  
    draw.text((x+1, y+1), imageDatetimeFromEXIF, font=myFont, fill='black')  
    # text  
    draw.text((x, y), imageDatetimeFromEXIF, font=myFont, fill="white" )

    # change directory
    if OVERRIDE is False:
      os.chdir(newDir)
    
    # save image
    i.save(fileList[n], quality=95 ) 

    # change directory back
    if OVERRIDE is False:
      os.chdir(mainDir)

  logging.info("end timestampPhotos()")

if __name__ == '__main__':
  main()
  takingPhotos()
  timestampPhotos()
  creatingTimelapse(TIMESTAMP_IMAGE_DIR)
  if SCP is True:
    scp(SCP_USER, SCP_HOST, SCP_DIRECTORY)

  if CLEANING is True:
    cleaning()
