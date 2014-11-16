#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                       metaData.fitsHandlers.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

import pyfits

from os.path import basename
from types   import BooleanType as boolean

from metaData.metaDataVersion import version, pkg_name
from metaData.utils.runUtils  import ptime

class FitsHandlers(object):
    """Though much simpler than either the CasaImageHandlers or MSHandlers
    classes, the FitsHandlers class as been implemented as below to parallel
    the method calls of those classes.

    i.e. 

    // constructor
    fho = FitsHandlers(fitsFile)
    fho.parseFits(<mimeType>)
    fho.writeHdr()
    
    The writeHdr method will write a file equal to the input filename with
    an appended '.hdr' extension.
    """

    def __init__(self,fitsFile):
        """Constructor receives a fitsfile name <string>. Does not support
        tarred or gzipped files.
        """
        self.fitsFileName = fitsFile
        self.fitsObj      = pyfits.open(fitsFile)
        self.hduList      = []
        self.fitsHdrFile  = self.fitsFileName+'.hdr'

    def parseFits(self, mimeType):
        """Caller passes the predetermined mime-type <string> of the file.
        In the case of FITS, this will either be,
        
        'image/fits-image'  or,
        'image/fits-uvw'
        """
        self.mimeType = mimeType
        for i in range(len(self.fitsObj)):
            self.hduList.append(self.fitsObj[i].header)
        return

    def writeHdr(self):
        """write out the header data as pretty print to a header file.

        parameters: <void>
        return:     <bool> or <string>, None or the file name written.
        """

        fitsCmnt = "Flexible Image Transport System"
        format1  = "%-8s= %21s\n"
        format2  = "%-8s= %21s /%s\n"
        formatc  = "%-8s %21s\n"
        fhdrFile = open(self.fitsHdrFile,'w')
        fileWrite= None
        # The following header data have been requested removed by
        # A. Grimstrup, 04-10-11
        
        # fhdrFile.write(format1 % ("FILENAME",basename(self.fitsFileName)))
        fhdrFile.write(format2 % ("FILETYPE","FITS",fitsCmnt))
        # fhdrFile.write(format1 % ("MIME-TYPE",self.mimeType))
        # fhdrFile.write("\nFITS Header Actual Begin:\n\n")
        
        for hdu in self.hduList:
            for card in hdu.ascardlist():
                key     = card.key
                value   = card.value
                comment = card.comment
                if key== 'HISTORY': continue
                if key[:2] == 'PC': continue
                #if key == 'COMMENT': continue       # request COMMENT cards -- R. Taylor.
                if key == 'COMMENT':
                    hline = formatc %(key,str(value))
                    fhdrFile.write(hline)
                    continue
                if value and type(value) == boolean:
                    value = "T"
                if len(key) < 8:
                    if not key.strip(): continue
                    if not comment.strip():
                        hline   = format1 %(key,str(value))
                    else: hline = format2 %(key,str(value),comment)
                    fhdrFile.write(hline)
                    continue
                else: 
                    if not key.strip(): continue
                    if not comment.strip():
                        hline   = format1 % (key,str(value))
                    else: hline = format2 % (key,str(value),comment)
                    fhdrFile.write(hline)
        fhdrFile.write(format1 % ("PARSER",pkg_name+" v"+version))
        fhdrFile.write(format1 % ("PARSE-DATE",ptime().split("T")[0]))
        fhdrFile.close()
        fileWrite = self.fitsHdrFile
        return fileWrite

    def render(self):
        """To stdout."""
        format1 = "%-8s= %24s"
        format2 = "%-8s= %24s /%s"
        for hdu in self.hduList:
            for card in hdu.ascardlist():
                key     = card.key
                value   = card.value
                comment = card.comment
                if key == 'HISTORY': continue
                if key == 'COMMENT': continue
                if value and type(value) == boolean:
                    value = "T"                
                if len(key) < 8:
                    if not key.strip(): continue
                    if not comment.strip():
                        hline   = format1 %(key,str(value))
                    else: hline = format2 %(key,str(value),comment)
                    print hline
                    continue
                else: 
                    if not key.strip(): continue
                    if not comment.strip():
                        hline   = format1 %(key,str(value))
                    else: hline = format2 %(key,str(value),comment)
                    print hline
        return
