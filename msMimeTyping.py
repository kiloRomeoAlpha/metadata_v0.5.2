#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                       metaData.msMimeTyping.py
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

from os.path        import basename, join
from pyrap.tables   import table as pyraptable

from metaData.utils.runUtils import redirectStdOut,resetStdOut


class MSMimeTypeError(TypeError):
    """Raise this if the Mime Typing returns something off.
    This shouldn't happen, of course, but just in case of 
    cosmic ray hit or something.
    """
    pass

        
class MSMimeTyping(object):
    def __init__(self, fileName, verbosity):
        """Class definition for some mime typing of CASA Images and
        Visibility Measurement Sets.

        This constructor does some fiddling with stdout to suppress
        pyrap.tables.table print output, which is not desired as part of
        stdout output string from this module.

                       *******************
        Right now, just prints, but will return something, or spit out
        a header file ... 
                       *******************
        """

        fsock, saveStdOut = redirectStdOut()
        self.msFileName   = fileName
        self.verbosity    = verbosity
        self.msObj        = pyraptable(fileName) # nulling stdout from this call
        resetStdOut(fsock,saveStdOut)


    def buildType(self,msVersion=None):
        """Build the type objects, call for printing."""
        msType   = self.__getType()
        mimeType = self.__buildMimeType(msType)
        if self.verbosity: self.__printHeader(msType,mimeType,msVersion)
        self.msObj.close()
        return mimeType

    #################################### prive #################################

    def __getType(self):
        """Return the 'type' from of the MS table object.
        
        return <string>

        type will be either,
        
        'Measurement Set' or
        'Image'

        If 'Measurement Set', a further type test is conducted on
        the expected 'UVW' column under the column's keyword,
        'MEASINFO'.

        eg., 

        >>> getcolkeywords('UVW')['MEASINFO']['type']
        
        'uvw'

        If a value other than 'uvw' is returned, a TypeError is raised as
        an unknown Measurement Set type has been detected.  This may also
        function as a test of Measurement Set typing consistency, but let's
        hope not.
        """

        msType = self.msObj.info()['type']
        if msType == "Measurement Set":
            msExtraTypeCheck = self.msObj.getcolkeywords('UVW')['MEASINFO']['type']
            if msExtraTypeCheck == 'uvw':
                msType = join(msType,msExtraTypeCheck)
            else: 
                err == "Unknown Measurement Set type:"+msExtraTypeCheck
                raise MSMimeTypeError, err
        return msType


    def __buildMimeType(self, mstype):
        """Return a somewhat valid MIME Type for the passed type, as extracted
        by self.gettype()

        returns <string>
        """
        if mstype   == "Measurement Set/uvw":
            mimeType = "image/ms-uvw"
        elif mstype == "Image":
            mimeType = "image/ms-image"
        else:
            err = "Invalid type passed: "+mstype
            raise MSMimeTypeError, err
        return mimeType


    def __printHeader(self,msType,mimeType,msVersion):
        """ Print out a little header at the start of processing."""
        print "\n#################################################"
        print "##########  MS MimeType Notification  ###########"
        print "#################################################\n"
        print "Received file:", self.msFileName
        print "Data Type Confirmed: ",msType
        print "_"*20,"\n"
        print "MIME-Version: 1.0"
        print "Content-Type:",mimeType
        if msVersion:
            print "Content-Version: MS_VERSION=" + str(msVersion[1])
        print "Content-Disposition: filename=" + basename(self.msObj.name()) + ";\n\t" \
            "parse-date=\""+self.__ptime()+"\";"
        print "_"*20,"\n"


    def __ptime(self):
        """returns the current date/time in ISO 8601 standard format."""

        return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(time.time()))
