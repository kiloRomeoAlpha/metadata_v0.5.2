#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                     metaData.utils.runUtils.py
#                                                      Kenneth Anderson, 2011-08
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "K.R. Anderson, <k.r.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

import sys, types
import getopt
import time

from   os.path import basename, normpath
from   numpy   import ndarray
from   math    import degrees

from metaData.incl.imageInclusion import velocityType
from metaData.convert.polarizationConversions import casaStokesTypes
# ------------------------------------------------------------------------------

def usage(mod):

    useBurp = '\n\tUsage: '+ mod + ' [--help] [--verbose] '\
              '<FITSfile or ms_dir>\n\n\twhere <FITSfile or ms_dir> is the name '\
	      'of a FITS file,\n\ta Casa Image or Visibility Measurement Set, \n\t'\
              'either as a tar archive or gzip tar archive.\n\n'
    return useBurp


def handleCLargs(args):
    mod = basename(sys.argv[0])
    long_options = ['help', 'verbose']
    try:
	opts, arg = getopt.getopt(sys.argv[1:],'',long_options)
    except getopt.GetoptError:
	sys.exit(usage(mod))

    if not arg:
	sys.exit(usage(mod))

    # Only ONE observation (argument) can be specified
    if len(arg) != 1:
       	sys.exit(usage(mod))

    msFile      = normpath(arg[0])
    verbose     = False
    cl_switches = []

    # cl_switches is left as a hook for handling possible future options,
    # options that do not exist at the moment. -kra, 10.08.2011.

    if opts:
	for o, a in opts:
	    if a:
		cl_switches.append(o+"="+a)
	    else:
		cl_switches.append(o)

            if o in ("--verbose"):
                verbose = True
                continue
	    if o in ("--help",):
		sys.exit(usage(mod))
	    else:
		sys.exit(usage(mod))
    return msFile, verbose


def redirectStdOut(logger=None):
    """Redirect stdout to a logger object, if passed. If a logger object is not
    passed, redirection is to /dev/null. A logger object must be a file like
    object with a write method. Preferably, logger is a configured logging
    instance.
    """
    saveStdOut = sys.stdout
    if logger:
        fsock = logger
        sys.stdout = fsock
    else:
        fsock = open('/dev/null','w')
        sys.stdout = fsock
    return fsock, saveStdOut


def resetStdOut(fsock,saveStdOut):
    """Resets sys.stdout to the passed file object, saveStdOut. This object
    should be the original sys.stdout file object. fsock is an opened file
    object that is acting as stdout.
    """
    sys.stdout = saveStdOut
    fsock.close()
    del fsock, saveStdOut
    return


def decdeg2dms(dd):
    """Caller passes decimal degrees of type <float>.

    Returns a 3-tuple, all type <float>:

    (degrees, minutes, seconds) 

    Parameters: <float> -- decimal degrees
    Return:     <tuple> -- (<float>,<float>,<float>)
    """
    mnt,sec = divmod(dd*3600,60)
    deg,mnt = divmod(mnt,60)
    return deg,mnt,sec

def decdeg2hms(dd):
    """Caller passes decimal degrees of type <float>.
    
    Returns a 3-tuple,  all type <float>:

    (hours, minutes, seconds).
    """
    mnt,sec = divmod(dd*3600,60)
    deg,mnt = divmod(mnt,60)
    return deg,mnt,sec

def decdeg2dmsString(ddegrees):
    """Caller passes decimal degree of type <float>.

    Returns a <string> of the form

    'd[dd].mm.ss.sss...'

    Note: A kludge is introduced here in order to deal with imprecision in stored
    coordinate conversion values.  Seconds are set to zero when a seconds value
    is less than 1 milli-arcsecond, (0.001).  Such small fractions of a second
    appear to result from original pointing directions (so far seen only in
    simulated data) specified as an exact number of degrees, eg. 28.0, which is then 
    converted and stored in the resulting Measurement Set as radians.  The precision of
    this converted value as stored in the MS is insufficient to re-render the original
    float value of 28.0 degrees.

    Eg.,  simulated VLA beam data, VLA_sim_beam5.MS,

    >>> FIELD:REFERENCE_DIR[0]
    array([[7.27220522e-05, 4.88692191e-01]])

    where dec is second item of the array, i.e. 

    >>> FIELD:REFERENCE_DIR[0][0][1]
    0.4886921905584124
    
    This converts to 
        
        dec = +28 degrees, 0 minutes, 2.910383304567e-11 seconds
    
    It appears highly unlikely that this was the original requested pointing.

    This function will return the <string>
        '+28.0.0.0'
    """
    ensign = ''
    if ddegrees < 0:
        ensign = '-'
        dd   = abs(ddegrees)
    else: dd = ddegrees
    mnt,sec  = divmod(dd*3600,60)
    deg,mnt  = divmod(mnt,60)
    if sec < 0.001:
        sec = 0.0
    if ensign:
        dmsString = ensign+str(int(deg))+"."+str(int(mnt))+"."+str(sec)
    else:
        dmsString = "+"+ str(int(deg))+"."+str(int(mnt))+"."+str(sec)
    return dmsString

def decdeg2hmsString(ddegrees):
    """Caller passes decimal degrees of type <float>.

    Returns a <string> of the form

    'HH:mm:ss.ssss...'

    Note: See previous note for the function, decdeg2dmsString().
    """
    ensign = ''
    if ddegrees < 0:
        ensign = '-'
        dd     = abs(ddegrees)
    else: dd   = ddegrees
    hours,hrem = divmod(dd,15)
    fracmnt   = hrem/15*60
    mnt       = int(fracmnt)
    secs      = (fracmnt - mnt)*60
    if secs < 0.001:
        secs = 0.00
    if hours < 10:
        hmsString = ensign+"0"+str(int(hours))+":"+str(mnt)+":"+str(secs)
    else:
        hmsString = ensign+str(int(hours))+":"+str(mnt)+":"+str(secs)
    return hmsString


def delist(sentList):
    """Caller passes an iterable, comprising elements of any type,
    Returns a concantentated csv string of all iterated elements.
    """
    return ", ".join(["%s" % el for el in sentList])


def stringify(thing):
    """Caller passes an object. Passed object handled
    here can be one of

    <string>
    <integer>
    <float>
    <list>
    <ndarray>

    Return a string build from  a passed data type. Iterables
    are concatentated via the delist() function.
    """
    if isinstance(thing,str):
        stringThing = thing
    elif isinstance(thing,int):
        stringThing = str(thing)
    elif isinstance(thing, float):
        stringThing = str(thing)
    elif isinstance(thing,list):
        stringThing = delist(thing)
    elif isinstance(thing,ndarray):
        stringThing = delist(thing)
    else:
        raise TypeError, "Unknown type passed"
    return stringThing.strip()
               

def vtranslate(velocityIndex):
    """Caller passes a 'velType' index of type <int>,
    
    Returns a <string> of the Velocity Type.  
    """
    return velocityType[int(velocityIndex)]


def isoDateTime(mjdSecs):
    """Caller passes MJD in seconds. Passed object can be of type
    <float> or <string>.

    Returns an ISO 8601 Date-Time string.

    return <string>

    MJD of Unix epoch 1970-01-01T00:00:00.0 = 40587.0

    In seconds,

    40587*86400 = 3506716800s

    The ValueError exception trapped here will likely be due
    to times of zero being passed to this function.  Indeed,
    anytime < epochDelta will throw that exception on the 
    strftime() call.
    """
    epochDelta = 3506716800.
    secondsMJD = float(mjdSecs)
    try: isoTime= time.strftime("%Y-%m-%dT%H:%M:%SZ",\
                                    time.gmtime(secondsMJD - epochDelta))
    except ValueError:
        isoTime = "No Times"
        pass
    return isoTime


def raDecConvert(directionPair):
    """Caller passes a Casa Image buried array RA-Dec pair.

    eg., metaDict['FIELD:REFERENCE_DIR']
    ...
    array([[ 1.40134576,  0.29041328]])
    array([[ 1.49066296, -0.09943254]])
    array([[ 1.46225308, -0.09471353]])
    ...
    
    Returns tuple-like <string>.
    """
    radecs = ''
    ra     = decdeg2hmsString(degrees(directionPair[0][0]))
    dec    = decdeg2dmsString(degrees(directionPair[0][1]))
    return '('+ra+' '+ dec+'), '


def polarizationConvert(corrTypeArray):
    return ", ".join([casaStokesTypes[corr] for corr in corrTypeArray[0]])

def ptime():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(time.time()))
    
