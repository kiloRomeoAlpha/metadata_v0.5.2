#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                This is the executable with cli
#                                                            metaData.extract.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

import sys, logging
from   os.path  import dirname, basename

from metaData import msMimeTyping, fitsMimeTyping
from metaData import msHandlers, casaImageHandlers, fitsHandlers
from metaData.utils import runUtils
from metaData import metaDataVersion

class MimetypeError(TypeError):
    """Raise this if the Mime Typing returns something off.
    This shouldn't happen, of course, but just in case of 
    cosmic ray hit or something.
    """
    pass

def getFitsMimeType(fitsFileName,verbosity):
    fmtype = fitsMimeTyping.FITSMimeTyping(fitsFileName,verbosity)
    mimeType = fmtype.buildType()
    return mimeType

def getMSMimeType(msFileName,verbosity):
    try: 
        msTypingObj = msMimeTyping.MSMimeTyping(msFileName,verbosity)
        mimeType = msTypingObj.buildType()
    except RuntimeError: mimeType = ''
    return mimeType

def run(inFileName, mimeType, untarredName=""):
    """Extract metadata of the appropriate mime type passed.

    Parameters: inFileName   <string>, dataset name
                mimeType     <string>, the mime type of dataset
                untarredName <string>, optional name for untarred file name.

    Return: <bool> or <string>, None or the header file name written.
    """
    fileWrite= None
    if mimeType == "image/ms-uvw":
        if untarredName:
            handler   = msHandlers.MSHandlers(untarredName)
        else: handler = msHandlers.MSHandlers(inFileName)
        handler.parseMS(mimeType)
        handler.buildFlatMeta()
        fileWrite = handler.writeHdr(inFileName)
    elif mimeType == "image/ms-image":
        if untarredName:
            handler   = casaImageHandlers.CasaImageHandlers(untarredName)
        else: handler = casaImageHandlers.CasaImageHandlers(inFileName)
        handler.parseImage(mimeType)
        fileWrite = handler.writeHdr(inFileName)
    elif mimeType == "image/fits" or mimeType == "image/fits-uvw":
        handler = fitsHandlers.FitsHandlers(inFileName)
        handler.parseFits(mimeType)
        fileWrite = handler.writeHdr()
    else:
        err = "Unknown File MIME Type on: "+inFileName
        raise MimetypeError, err
    return fileWrite


if __name__ == '__main__':

    import shutil, tarfile

    # Initalise a default logger
    logging.basicConfig(format="%(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    #-----------------------------------------------------------------#
    #                         Handle Cl Options
    ##----------------------------------------------------------------#

    inFileName,verbosity = runUtils.handleCLargs(sys.argv)

    #-----------------------------------------------------------------#
    #                       End Handle Cl Options
    ##----------------------------------------------------------------#

    # Get the MIME Type. This will take considerably longer if a tarfile
    # is passed. Input can be 
    # 
    # -- FITS
    # -- UVFITS
    # -- UV Measurement Set, ) straight, tar, or gzip tar
    # -- Casa Image,         ) straight, tar, or gzip tar
    #
    # Extracts all data in order to make pyrap work, which is why it
    # takes so long. Dump in '.', then remove it.

    # Testing first for a FITS file ...
    # Verbosity clause eliminates 15 truth tests in previous version.
    # See commented section below.
    # New in v0.5.2, added 2012-12-12 kra.

    if verbosity:
        notice = "Wrote header to file: "
        fileWrite = None
        print "\n\n\tThis is metaData, v"+metaDataVersion.version
        print "\t"+("-")*24+"\n"
        print "Operating on", inFileName
        try:
            print "\nTesting for tar ..."
            if not tarfile.is_tarfile(inFileName):     # must be a FITS file
                print "\ntarfile test is False"
                print "\nCheck for FITS type."
                mimeType = getFitsMimeType(inFileName,verbosity)
                print "\nGot a FITS mimetype:", mimeType
                print "\ncalling run functional on",inFileName,",",mimeType
                fileWrite = run(inFileName,mimeType)
                print notice,fileWrite
            else:
                print "\ntarfile detected. Opening ..."
                msTarObj     = tarfile.open(inFileName)
                untarredName = msTarObj.getnames()[0]
                print "Tarfile name is,",basename(inFileName),"is really",untarredName
                msTarObj.extractall()             # dumps into '.' Watch out.
                mimeType     = getMSMimeType(untarredName,verbosity)
                print "\nGot an MS mimetype:",mimeType
                del msTarObj
                print "\ncalling run functional on",inFileName,",",mimeType
                fileWrite = run(inFileName,mimeType,untarredName=untarredName)
                print notice,fileWrite
                print "\ndeleting untarred",mimeType,"dataset..."
                shutil.rmtree(untarredName)
        except IOError, err:
            if "Is a directory:" in str(err):
                print "Not tar ..."
                mimeType = getMSMimeType(inFileName,verbosity)
                print "\nGot an MS mimetype:",mimeType
                if mimeType: 
                    if verbosity: print "\ncalling run functional on",inFileName,",",mimeType
                    fileWrite = run(inFileName,mimeType)
                    print notice,fileWrite
                else: 
                    print "Indeterminate MIME-TYPE on file:",inFileName
            else: 
                print "\n*** Hit an IOError. Probable fail on run() ***"
                raise IOError,err
    # not verbose clause
    else:
        try:
            if not tarfile.is_tarfile(inFileName):     # must be a FITS file
                mimeType  = getFitsMimeType(inFileName,verbosity)
                fileWrite = run(inFileName,mimeType)
            else:
                msTarObj     = tarfile.open(inFileName)
                untarredName = msTarObj.getnames()[0]
                msTarObj.extractall()             # dumps into '.' Watch out.
                mimeType     = getMSMimeType(untarredName,verbosity)
                del msTarObj
                fileWrite = run(inFileName,mimeType,untarredName=untarredName)
                shutil.rmtree(untarredName)
        except IOError, err:
            if "Is a directory:" in str(err):
                mimeType = getMSMimeType(inFileName,verbosity)
                if mimeType: 
                    fileWrite = run(inFileName,mimeType)
            else: 
                raise IOError,err
    sys.exit()


    # if verbosity:
    #     print "\n\n\tThis is metaData, v"+metaDataVersion.version
    #     print "\t"+("-")*24+"\n"
    #     print "Operating on", inFileName

    # try:
    #     if verbosity: print "\nTesting for tar ..."
    #     if not tarfile.is_tarfile(inFileName):     # must be a FITS file
    #         if verbosity: print "\ntarfile test is False"
    #         if verbosity: print "\nCheck for FITS type."
    #         mimeType = getFitsMimeType(inFileName,verbosity)
    #         if verbosity: print "\nGot a FITS mimetype:", mimeType
    #         if verbosity: print "\ncalling run functional on",inFileName,",",mimeType
    #         run(inFileName,mimeType)
    #     else:
    #         if verbosity: print "\ntarfile detected. Opening ..."
    #         msTarObj     = tarfile.open(inFileName)
    #         untarredName = msTarObj.getnames()[0]
    #         if verbosity: print "Tarfile name is,",basename(inFileName),"is really",untarredName
    #         msTarObj.extractall()             # dumps into '.' Watch out.
    #         mimeType     = getMSMimeType(untarredName,verbosity)
    #         if verbosity: print "\nGot an MS mimetype:",mimeType
    #         del msTarObj
    #         if verbosity: print "\ncalling run functional on",inFileName,",",mimeType
    #         run(inFileName,mimeType,untarredName=untarredName)
    #         if verbosity: print "\ndeleting untarred",mimeType,"dataset..."
    #         shutil.rmtree(untarredName)
    # except IOError, err:
    #     if "Is a directory:" in str(err):
    #         if verbosity: print "Not tar ..."
    #         mimeType = getMSMimeType(inFileName,verbosity)
    #         if verbosity: print "\nGot an MS mimetype:",mimeType
    #         if mimeType: 
    #             if verbosity: print "\ncalling run functional on",inFileName,",",mimeType
    #             run(inFileName,mimeType)
    #         else: 
    #             if verbosity: print "Indeterminate MIME-TYPE on file:",inFileName
    #     else: 
    #         if verbosity: print "\n*** Hit an IOError. Probable fail on run() ***"
    #         raise IOError,err
    # sys.exit()
