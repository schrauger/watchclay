# Watches Claymore mining status
# Copyright 2017 Larry Lang
# Wemo support added by Stephen Schrauger
# If rig becomes unresponsive, wPower power cycle
# If rig overheats, wPower power off

import sys, os, io, ConfigParser # configuration file input and parsing
from random import randint # random cookie generation
from email.mime.text import MIMEText # email body format
from subprocess import Popen, PIPE # pipe to sendmail
import requests, json # API requests and JSON parsing
import re # regular expressions to extract JSON string and to strip ANSI codes
import time

# load configuration
if ( len(sys.argv) > 1 ) and ( os.path.isfile(sys.argv[1]) ): # argument given, file exists
    config_file=sys.argv[1] # use that file as config
else:
    config_file=os.path.splitext(sys.argv[0])[0]+".conf" # default config file <program>.conf
print "Loading configuration from", config_file
with open(config_file) as f:
    config_file = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(config_file))
version = config.get('version', 'ver')
if  version != '1.0':
    print "Unknown configuration version"
    quit()
IFTTT_WEBHOOKS_KEY = config.get('ifttt', 'webhooks_key')            # In your IFTTT account, this private key for webhooks
IFTTT_WEBHOOKS_POWER_OFF = config.get('ifttt', 'webhooks_power_off_string') 
IFTTT_WEBHOOKS_POWER_ON = config.get('ifttt', 'webhooks_power_on_string') 
CLAYMORE_IP    = config.get('claymore', 'claymore_ip')
CLAYMORE_PORT  = config.getint('claymore', 'claymore_port')

HASH_FLOOR     = config.getint('limits', 'hash_floor')     # Mh/s, rig total
REJECT_CEILING = config.getint('limits', 'reject_ceiling') # maximum number of mining pool rejects
TEMP_CEILING   = config.getint('limits', 'temp_ceiling')   # degrees Celsius, hottest GPU

CHECK_TIME     = config.getint('timers', 'check_time')     # seconds between status checks
MAX_RECHECK    = config.getint('timers', 'max_recheck')    # maximum recheck attempts before rig reset
# CHECK_TIME * MAX_RECHECK must be greater than Claymore reboot time to avoid endless power cycles
CYCLE_TIME     = config.getint('timers', 'cycle_time')     # seconds for power cycle pause
WAIT_TIME      = config.getint('timers', 'wait_time')      # seconds for api response
UPDATE_TIME    = config.getint('timers', 'update_time')    # seconds between email updates

SENDER     = config.get('email','sender')
RECIPIENTS = config.get('email','recipients')
REFERENCE  = config.get('email','reference')

print "Watching Claymore at", CLAYMORE_IP, "every", CHECK_TIME, "seconds"
print "Power cycle reset (after", MAX_RECHECK, "rechecks) if:"
print "\tRig becomes unresponsive or returns errors"
print "\tHash rate falls below", HASH_FLOOR, "Mh/s"
print "\tMining pool rejects more than", REJECT_CEILING, "shares"
print "Power shut down if:"
print "\tAny GPU runs hotter than", TEMP_CEILING, "Celsius"

class pstyle: # print with ANSI style and color codes
    END   = '\033[0m'
    BOLD  = '\033[1m'
    RED   = '\033[31m'
    BLINK = '\033[5m'
    GREEN = '\033[32m'
    GRAY  = '\033[97m'

def sendupdate ( subject, body ):
    # email updates via sendmail
    body = re.sub('\x1b.*?m', '', body) #strip ANSI style and color codes
    msg = MIMEText(body+"\n"+REFERENCE)
    msg["From"] = SENDER
    msg["To"]   = RECIPIENTS
    msg["Subject"] = subject
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(msg.as_string())
    return(True)

def wpower ( operation, cycletime=0 ):
    if operation.lower() == 'cycle':
        print "Power cycling power outlet"
        #@TODO power off
        r = requests.get('https://maker.ifttt.com/trigger/'+str(IFTTT_WEBHOOKS_POWER_OFF)+'/with/key/'+IFTTT_WEBHOOKS_KEY)
        print "Power off, pausing", cycletime, "seconds... "
        time.sleep(cycletime)
        #@TODO power on
        r = requests.get('https://maker.ifttt.com/trigger/'+str(IFTTT_WEBHOOKS_POWER_ON)+'/with/key/'+IFTTT_WEBHOOKS_KEY)
        print "Power on"
        print "Power cycle complete"
    elif operation.lower() == 'off':
        print "Powering off power outlet"
        #@TODO power off
        r = requests.get('https://maker.ifttt.com/trigger/'+str(IFTTT_WEBHOOKS_POWER_OFF)+'/with/key/'+IFTTT_WEBHOOKS_KEY)
        print "Power off complete"
    elif operation.lower() == 'on':
        print "Powering on power outlet"
        #@TODO power on
        r = requests.get('https://maker.ifttt.com/trigger/'+str(IFTTT_WEBHOOKS_POWER_ON)+'/with/key/'+IFTTT_WEBHOOKS_KEY)
        print "Power on complete"
        
def claystatus ( ip, port ):
    # return Claymore mining status
    clayreturn = { 'errortype' : 'None' , 'rebooting' : False, 'clayJSON' : {"result": [],} } # initialize return dictionary
    url = "http://"+ip+":"+str(port)
    try:
        r = requests.get(url, timeout=WAIT_TIME)
        t = re.search('\{[^\}]+\}', r.content) # find JSON string in response contents
        j = json.loads(t.group(0)) # convert string to JSON
        clayreturn['clayJSON'] = j
        if "Rebooting" in r.content:
            clayreturn['rebooting'] = True
    except requests.exceptions.Timeout as err:
        # print err
        clayreturn['errortype'] = "Timeout error"
    except requests.exceptions.ConnectionError as err:
        # print err
        clayreturn['errortype'] = "Connection error"
    except requests.exceptions.RequestException as err:
        # print err
        clayreturn['errortype'] = "Request Exception error"
    return clayreturn

# initialize state
csstring = ""   # no clay status string yet
maxtemp = 0     # no hot GPUs yet
recheck = 0     # no rig rechecks yet
prevupdate = 0  # no email updates sent yet
worried = False # no emails about problems sent yet

while True:
    # main loop
    cs = claystatus ( ip=CLAYMORE_IP, port=CLAYMORE_PORT )
    # print pstyle.GRAY+str(cs)+pstyle.END # verbose
    if cs['errortype'] == "None":
        hashrate     = cs['clayJSON']['result'][2].split(';')[0] # select hashrate from JSON structure
        hashrate     = round(int(hashrate)/1000.0, 1) # convert from kh/s to Mh/s, round to nearest tenth
        gpuhash      = cs['clayJSON']['result'][3].split(';') # list of hashrate for every GPU
        minhash      = min(gpuhash) # minimum hashrate for all GPUs
        mingpu       = gpuhash.index(minhash) # GPU with minimum hashrate
        minhash      = round(int(minhash )/1000.0, 1) # convert from kh/s to Mh/s, round to nearest tenth
        gpuhashcount = len(gpuhash) # GPUs reporting hash rate
        totalshares  = int(cs['clayJSON']['result'][2].split(';')[1]) # select total shares from JSON structure
        rejectshares = int(cs['clayJSON']['result'][2].split(';')[2]) # select rejected shares from JSON structure
        try:
            gputemps = cs['clayJSON']['result'][6].split(';') # list of temperatures and fanspeeds for every GPU
        except: # JSON parsing error
            gputemps = [0,0]
        if ( gputemps == [u''] ): # empty list of GPU temps
            gputemps = [0,0]
        maxtemp = max(gputemps[::2])          # maximum temperature for all GPUs
        maxgpu  = gputemps.index(maxtemp)/2   # GPU with maximum temperature
        gputempcount = int(round(len(gputemps)/2.0)) # GPUs reporting temperature
        if gpuhashcount > gputempcount: # more GPUs reporting hashrate than temperature
            cs['errortype'] = "GPU hash/temp mismatch error"
            print cs['errortype']
        csstring = pstyle.BOLD+"Hashrate:"+str(hashrate)+"Mh/s"+pstyle.END+" (GPU"+str(mingpu)+" "+str(minhash)+" slowest)" \
                    +"\t"+pstyle.GREEN+"Total shares:"+str(totalshares)+pstyle.END+" (Rejected:"+str(rejectshares)+")" \
                    +"\t"+"Max temp:"+str(maxtemp)+" (GPU"+str(maxgpu)+")"
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "\t", csstring
    else:
        print cs['errortype']
    # notify of Claymore rebooting itself
    if cs['rebooting'] == True:
        print pstyle.RED+"Reboot ordered by Claymore"+pstyle.END
        # send email for reboot
        if sendupdate( subject="Mining rig reboot (ordered by Claymore)", body=csstring ):
            prevupdate = time.time() # record email update time
            worried = True # email about problem sent
            print "Email sent about reboot"
    # check for errors or problems that could prompt power cycle reset
    if ( cs['errortype'] != 'None' ) or ( hashrate < HASH_FLOOR ) or ( rejectshares > REJECT_CEILING ):
        print "Rig response error, hash too slow, or too many share rejects.",
        if ( recheck < MAX_RECHECK ):
            recheck = recheck+1 # count recheck attempt
            print "Recheck ",recheck,"of",MAX_RECHECK
        else:
            print pstyle.RED+pstyle.BOLD+pstyle.BLINK+"Resetting via power cycle..."+pstyle.END
            recheck = 1    # reset clears recheck, except 1 for probation (no normal status yet)
            wpower ( operation = 'cycle', cycletime=CYCLE_TIME )
            # send email for reset
            if sendupdate( subject="Mining rig reset (via wPower cycle)", body=csstring+"\n"+cs['errortype'] ):
                prevupdate = time.time() # record email update time
                worried = True # email about problem sent
                print "Email sent about reset"
            print "Resuming watch"
    else:
	    recheck = 0     # valid response clears recheck
    # send email for normal status, at least once per UPDATE_TIME
    if ( recheck == 0 ) and ( worried or ( time.time()-prevupdate >= UPDATE_TIME )):
        if sendupdate( subject="Mining rig operating normally", body=csstring ):
            prevupdate = time.time() # record email update time
            print "Email sent about normal status"
            worried = False # email resolving problem sent
    # shut down if any GPU exceeds maximum temperature
    if ( int(maxtemp) >= TEMP_CEILING ):
        print "Rig running too hot. Shutting down..."
        wpower ( operation = 'off' )
        # send email for shut down
        if sendupdate( subject="Mining rig shut down (excess GPU temp)", body=csstring) :
            prevupdate = time.time() # record email update time
            worried = True # emabil about problem sent
            print "Email sent about shutdown"
        break
    time.sleep(CHECK_TIME)
print "Rig shut down"
quit()
