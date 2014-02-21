# timelapse_flow.py -l debug -f debug.log -x 1920

import logging
import optparse
import os
import time
import sys

#timestamp
from PIL import Image, ImageDraw, ImageFont  
from PIL.ExifTags import TAGS  

# CRITICAL < ERROR < WARNING < INFO < DEBUG < NOTSET
LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

PREFIX = "flow_"
TIMELAPSE_FILENAME = "timelapse.mp4"
global FPS_IN
global TIMESTAMP_IMAGE_DIR
FPS_IN = 10
FPS_OUT = 24
TIMEBETWEEN = 15 # 4 pictures per minute
global FILMLENGTH

def main():
  global FRAMES
  global DEMO_MODE
  global OVERRIDE
  global SCP
  global CLEANING

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

  # Your program goes here.
  # You can access command-line arguments using the args variable.
  logging.info("end main()")
  
def takingPhotos():
  FILMLENGTH = float(FRAMES / FPS_IN)
  logging.info("begin takingPhotos()")
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
        os.system("raspistill -o image%s.jpg" % (imageNumber))
      except Exception, e:
        logging.error(e)

    frameCount += 1
    time.sleep(TIMEBETWEEN - 7) #Takes roughly 6 seconds to take a picture, 7 seconds on a USB drive
  
  logging.info("end takingPhotos()")

def creatingTimelapse(image_dir):
  logging.debug("begin creatingTimelapse(%s)"%(image_dir))

  logging.info("Prefix: %s" % (PREFIX))
  logging.info("Timelapse filename: %s" % (TIMELAPSE_FILENAME))
  # Actual image is 2592x1944
  #os.system("nice -n 19 avconv -r %s -i %s/%simage%s.jpg -r %s -vcodec libx264 -crf 20 -g 15 -vf crop=2592:1458,scale=1280:720 %s"%(FPS_IN, image_dir, PREFIX, '%07d',FPS_OUT,TIMELAPSE_FILENAME))
  # added -y to override latest timelapse if exists
  os.system("nice -n 19 avconv -y -r %s -i %s/%simage%s.jpg -r %s -vcodec libx264 -crf 20 -g 15 -vf scale=1280:720 %s"%(FPS_IN, image_dir, PREFIX, '%07d',FPS_OUT,TIMELAPSE_FILENAME))

  logging.debug("end creatingTimelapse(%s)"%(image_dir))

def scp():
  logging.debug("begin scp()")
 
  logging.info("Transfering timelapse...")
  os.system("scp -i %s %s %s"%("/home/pi/.ssh/ida_dsa", TIMELAPSE_FILENAME, "user@ip:~/"))
  
  logging.debug("end scp()")

def cleaning():
  logging.debug("begin cleaning()")

  logging.info("Cleaning up...")
  
  if OVERRIDE is False:
    os.system("nice -n 19 rm -Rf %s"%(TIMESTAMP_IMAGE_DIR))

  os.system("nice -n 19 rm -Rf *image*.jpg")
  
  logging.debug("end cleaning()")

#timestamp stuff
def get_exif(fn):  
  '''returns all EXIF data as dictionary'''
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

  logging.debug("end get_exif(%s) -> %s"%(fn,ret))
  return ret

def get_datetime(fn):  
  '''returns string of year, month, day, hour, minute and second'''  
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
  global TIMESTAMP_IMAGE_DIR

  logging.info("begin timestampPhotos()")

  maindir = os.getcwd() # current working dir  
  fileList = os.listdir( maindir )    # list of files in current dir  
  fileList = [os.path.normcase(f) for f in fileList]   # normal case  
  # keep only files ending with .jpg  
  fileList = [ f for f in fileList if '.jpg' in os.path.splitext(f)[1]]  
  try:  
    i = Image.open(fileList[0])  
    imgwidth = i.size[0]  # get width of first image  
    imgheight = i.size[1]  
  except:  
    pass  
  fontPath = "/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-R.ttf" # font file path  
  myfont = ImageFont.truetype ( fontPath, imgwidth/40 ) # load font and size  
  (textw, texth) = myfont.getsize('00-00-0000 00:00')  # get size of timestamp  
  x = imgwidth - textw - 50  # position of text  
  y = imgheight - texth - 50

  if OVERRIDE is False:
    print 'Now creating',str(len(fileList)),'frames in folder', \
      time.strftime('"Frames_%Y%m%d_%H%M%S".', time.localtime())  
    # make new dir  
    newdir = os.path.join(maindir, time.strftime("Frames_%Y%m%d_%H%M%S", time.localtime()))
    TIMESTAMP_IMAGE_DIR = newdir
    os.mkdir(newdir)
  else:
    TIMESTAMP_IMAGE_DIR = maindir
    logging.debug("Now creating %s timestamp images in current folder"%(str(len(fileList))))
  
  # sorting file list alphabetical
  fileList.sort()

  for n in range(0,len(fileList)):  
    # open image from list
    i = Image.open(fileList[n])  
    draw = ImageDraw.Draw ( i )  
    # thin border  
    draw.text((x-1, y-1), get_datetime(fileList[n]), font=myfont, fill='black')  
    draw.text((x+1, y-1), get_datetime(fileList[n]), font=myfont, fill='black')  
    draw.text((x-1, y+1), get_datetime(fileList[n]), font=myfont, fill='black')  
    draw.text((x+1, y+1), get_datetime(fileList[n]), font=myfont, fill='black')  
    # text  
    draw.text ( (x, y), get_datetime(fileList[n]), font=myfont, fill="white" )

    if OVERRIDE is False:
      os.chdir(newdir)
    
    # save in new dir 
    #i.save ( 'Frame_'+str(n+1)+'.jpg', quality=95 ) 
    i.save(fileList[n], quality=95 ) 

    if OVERRIDE is False:
      os.chdir(maindir)  
    
    #print str(n+1)+',',  
    logging.debug("Processing image %s"%(fileList[n]))

  logging.info("end timestampPhotos()")

if __name__ == '__main__':
  main()
  takingPhotos()
  timestampPhotos()
  creatingTimelapse(TIMESTAMP_IMAGE_DIR)
  if SCP is True:
    scp()

  if CLEANING is True:
    cleaning()