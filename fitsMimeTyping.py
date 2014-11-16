#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                     metaData.fitsMimeTyping.py
#                                                      Kenneth Anderson, 2011-08
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

import time
import types
from   os.path import basename, join

import pyfits

class FITSMimeTypeError(TypeError):
    """Raise this if the Mime Typing returns something off.
    This shouldn't happen, of course, but just in case of 
    cosmic ray hit or something.
    """
    pass

class FITSMimeTyping(object):
    def __init__(self, fileName, verbosity):
        """Class definition for some mime typing of FITS Images and
        UVFITS datasets.

                       *******************
        """

        self.fitsFileName = fileName
        self.verbosity    = verbosity
        self.fitsObj      = pyfits.open(fileName) # nulling stdout from this call


    def buildType(self):
        """Build the type objects, call for printing."""
        fitsType   = self.__getType()
        mimeType = self.__buildMimeType(fitsType)
        if self.verbosity: self.__printHeader(fitsType,mimeType)
        self.fitsObj.close()
        return mimeType

    ################################ prive #################################

    def __getType(self):
        """Return the 'type' from of the fits object.
        
        return <string>

        type will be either,
        
        'Image' or
        'Visibility'
        """
        uvwKeywordSet = ['PTYPE1','PTYPE2','PTYPE3']
        try:
            uukey = self.fitsObj[0].header[uvwKeywordSet[0]]
            vvkey = self.fitsObj[0].header[uvwKeywordSet[1]]
            wwkey = self.fitsObj[0].header[uvwKeywordSet[2]]
            if 'UU' in uukey and 'VV' in vvkey and 'WW' in wwkey:
                fitsType = 'Visibility'
            else: raise KeyError
        except KeyError:
            fitsType = 'Image'
        return fitsType

    def __buildMimeType(self, fitsType):
        """Return a somewhat valid MIME Type for the passed type, as extracted
        by self.gettype()

        returns <string>
        """
        if fitsType   == "Visibility":
            mimeType   = "image/fits-uvw"
        elif fitsType == "Image":
            mimeType   = "image/fits"
        else:
            err = "Invalid type passed: "+fitsType
            raise FITSMimeTypeError, err
        return mimeType

    def __printHeader(self,fitsType,mimeType):
        """ Print out a little header at the start of processing."""
        print "\n#################################################"
        print "#########  FITS MimeType Notification  ##########"
        print "#################################################\n"
        print "Received file:", self.fitsFileName
        print "Data Type Confirmed: ",fitsType
        print "_"*20,"\n"
        print "MIME-Version: 1.0"
        print "Content-Type:",mimeType
        print "Content-Disposition: filename=" + basename(self.fitsFileName) + ";\n\t" \
            "parse-date=\""+self.__ptime()+"\";"
        print "_"*20,"\n"


    def __ptime(self):
        """returns the current date/time in ISO 8601 standard format."""

        return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(time.time()))
