#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                  metaData.casaImageHandlers.py
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
import string

from os.path import basename
from math    import degrees, radians

from pyrap.images   import image as pyrapimage
from pyrap.images   import coordinates

from metaData.utils.runUtils import redirectStdOut,resetStdOut
from metaData.utils.runUtils import decdeg2hmsString, decdeg2dmsString
from metaData.utils.runUtils import stringify, delist, vtranslate, ptime
from metaData.utils.genUtils import convertHz

from metaData.convert import mjdConversions
from metaData.metaDataVersion import pkg_name, version
from metaData.incl.imageInclusion import statInclusions

""" Initial open and step through keyword values in a CASA Image, which is a 
subtype of a CASA Measuremet Set. This module and class will slurp CASA Image
metadata. 

ToDo: Markup these as xml, perhaps using xmlUtils.
"""


class CasaImageValueError(AttributeError):
    """ A casaImageValueError will be raised when a CASA Image contains an
    unknown element as presented by a call to keywordnames().  At the top
    level, CASA Image metadata are presented as a list of string values, 
    whose underlying values may be one of several types, either a table, or
    some other data structure, such as a nested dictionary, or a simple string.
    To date, only the string values of 

    'logtable', 'coords', 'imageinfo', 'units'

    are known.

    Image list inclusions for image metadata, incl.imageInclusions.listInclusions,
    will only examine the expected keyword lists and strings,

    'coords', 'imageinfo', 'units'
    """
    pass


class CasaImageTypeError(TypeError):
    """Use this error for type assertions on coordinate types."""
    pass


class CasaImageHandlers(pyrapimage):
    """The CasaImageHandlers class is subclassed off the pyrap.images.image class,
    which in turn is subclassed from the Casacore Image class. Constructor opens a
    passed CASA Image filename of type <string>.

    The Casacore Image class defines a number of methods to extract metadata
    from the passed image, and are not overridden here.

    Examples of such methods are 

    self.name() - filename passed
    self.ndim() - N dimensions of image
    self.shape()- shape of image cube, pixels
    self.size() - N_of pixels in image.
    self.unit() - units of image, eg. 'Jy/beam'
    
    Some calls will still return data structures that will have to be further
    parsed by this class. 

    eg.,

    self.imageinfo()

    {'restoringbeam': {
        'major': {'unit': 'arcsec', 'value': 1.3832687139511108},
        'positionangle': {'unit': 'deg', 'value': 33.8624153137207},
        'minor': {'unit': 'arcsec', 'value': 1.2961828708648682}
        },
    'objectname': '3C129', 
    'imagetype': 'Intensity'
    }

    which means 'objectname' is available as

    >>> self.imageinfo()['objectname']

    '3C129'

    Other methods will manifest in an call to the passed image's coordinate systems
    via
    
    self.coordinates().get_telescope()

    which is more efficiently extracted from an instance of image.coordinates,

    i.e.

    pimCoords = self.coordinates()
    pimCoords.get_telescope()

    For more documentation on available image methods see,

    <http://www.atnf.csiro.au/computing/software/casacore/pyrap/docs/pyrap_images.html>

    Still other metadata will need to be accessed directly from available data
    structures but which do not have methods provided. Methods for those data
    are provided as 'meta-methods', such as 'buildPointing()', which will call
    these methods on instances of this class, gather and package the data in an
    appropriate way.
    """

    def parseImage(self, mimeType):
        """Parse and extract required metadata from a CASA Image, as passed to the
        constructor.  Caller passes the MIME Type, which is determined prior to 
        instantiating this class.
        
        Parameters: <string>, the mimetype of the Casa Image, as determined (usually)
        by the MSMimeTyping class.

        Return: void
        """

        self.__setInstanceAttrs(mimeType)
        self.pimCoords = self.coordinates()
        self.pimageInfo= self.imageinfo()
        self.imAxes    = self.buildImAxes()
        self.axesNames = self.pimCoords._names
        self.extract()
        return


    def extract(self):
        """
        Slurp the metadata from the passed table tool object. These data are 
        placed in the instance's meta tuple list. An undefined column will raise
        a RuntimeError exception, and will be marked at 'Undefined.'

        N.B. : 'START-OBS' and 'END-OBS' are spoofed for database query
        =====   purposes.  There are no such parameters in Casa Images, nor any 
        way to determine the start and end times for these datasets within a
        Casa Image context.

        Parameters: none
        Return: void
        """
        vObsDates,timesys = self.isoObsDate()

        # The following header data have been requested removed by
        # A. Grimstrup, 04-10-11
        # - k.r.a.
        #
        # self.meta.append(("FILENAME",    self.imFileName))
        # self.meta.append(("MIME-TYPE",   self.mimeType))
        # self.meta.append(("PARSE-DATE",  ptime()))
        # -------------------------------------------------------------------- #

        self.meta.append(("FILETYPE",   "CASA Image"))
        self.meta.append(("OBSERVER",   self.pimCoords.get_observer()))
        self.meta.append(("DATE-OBS",   vObsDates))
        self.meta.append(("MJD-OBS",    self.mjdObsDate()[0]))
        self.meta.append(("START-OBS",  vObsDates))
        self.meta.append(("END-OBS",    vObsDates))
        self.meta.append(("TIMESYS",    timesys))
        self.meta.append(("TELESCOPE",  self.pimCoords.get_telescope()))
        self.telescopePosition()
        self.meta.append(("TARGET",     self.pimageInfo['objectname']))
        self.meta.append(("N_OF-AXES",  self.ndim()))
        self.meta.append(("IMAGE-AXES", self.imAxes))
        self.meta.append(("IMAGE-SHAPE",self.shape()))
        self.meta.append(("IMAGE-TYPE", self.pimageInfo['imagetype']))
        self.meta.append(("IMAGE-UNIT", self.unit()))
        self.meta.append(("IMAGE-SIZE", str(self.size())+" (pixels)"))
        self.buildBeamInfo()
        self.buildPointing()
        self.buildCoords()
        self.imStats()
        self.meta.append(("PARSER",pkg_name+", v"+version))
        self.meta.append(("PARSE-DATE",  ptime().split("T")[0]))
        return


    def obsDate(self):
        """ 
                   ********************** Deprecated *****************
        Use isoObsDate()

        Return an ISO 8601 compliant Observation Date. The function caldate
        accepts <int> or <float>

        eg.,
        
        >>> mjdConversions.caldate(49558.320659722245)
        '1994-07-25T07:41:45.0000019837'

        >>> mjdConversions.caldate(49558)
        '1994-07-25T00:00:00.0'

        Parameters: none
        Return: <string>, an ISO8601 Date-Time
        """
        return mjdConversions.caldate(self.mjdObsDate())


    def mjdObsDate(self):
        """Return a readable MJD date from the get_obsdate() call.
        Parameters: none
        Return: <string>, MJD date string
        """
        dateval = self.pimCoords.get_obsdate()['m0']['value']
        timesys = self.pimCoords.get_obsdate()['refer']
        return dateval,timesys
        

    def isoObsDate(self):
        """ MJD of Unix epoch 1970-01-01T00:00:00.0 = 40587.0

        In seconds,

        40587*86400 = 3506716800s

        This is the epoch delta between MJD base and Unix time.

        This method returns a tuple consisting of the ISO Date-time as a string,
        and associated time system (CASA Table parameter, 'refer'), eg, 'UTF', 
        also as a string.

        Parameters: none
        Return: tuple, (<string>, ISO8601 Date-Time, <string> time system)
        """
        epochDelta   = 3506716800.
        daySecs      = 86400
        date,timesys = self.mjdObsDate()
        secondsMJD   = date*daySecs

        try:
            isoTime = time.strftime("%Y-%m-%dT%H:%M:%SZ", \
                                        time.gmtime(secondsMJD - epochDelta))
        except ValueError:
            isoTime = "Invalid DATE-OBS"
        return isoTime, timesys


    def telescopePosition(self):
        """Method inserts the telescope position parameters as found in the
        image's coordinate system instance (here, self.pimCoords).  There is no
        direct method to extract these metadata, but the full 'telescopeposition'
        dict can be accessed via the self.pimCoords instance.
        (images.coordinates.coordinatesystem):

        self.pimCoords.dict()['telescopeposition']

        which returns a dictionary containing the relevent metadata.
        eg.,
        
          {
            'm0': {'value': 0.10309153883282665, 'unit': 'rad'}, 
            'm1': {'value': 0.7756481013100227, 'unit': 'rad'}, 
            'm2': {'unit': 'm', 'value': 6370242.61901}, 
            'type': 'position', 
            'refer': 'ITRF'
            }
         
         m0 = telescope longitude
         m1 = telescope latitude
         m2 = telescope height 
         
         ITRF is the reference frame here, with GRS80 the recommended geoid for
         transformation from ITRF standard X,Y,Z coordinate data. See the ITRF
         FAQ for further information. (http://itrf.ensg.ign.fr/faq.php)
         
         The above structure is then converted to keyword-value form and inserted
         into the self.meta data structure.

         Parameters: None
         Return:     void
        """
        try: 
            pos = self.pimCoords.dict()['telescopeposition']
            lon = pos['m0']
            lat = pos['m1']
            hgt = pos['m2']
            self.meta.append(('TELESCOP_LAT',     lat['value']))
            self.meta.append(('TELESCOP_LAT_UNIT',lat['unit']))
            self.meta.append(('TELESCOP_LON',     lon['value']))
            self.meta.append(('TELESCOP_LON_UNIT',lon['unit']))
            self.meta.append(('TELESCOP_HGT',     hgt['value']))
            self.meta.append(('TELESCOP_HGT_UNIT',hgt['unit']))
            self.meta.append(('TELESCOP_REFER',   pos['refer']))
        except KeyError: pass
        return


    def buildImAxes(self):
        """Return a reasonable string for the image axes set as returned by
        coordinatesystem.get_axes().

        Parameters: none
        Return: <string>, names of image axes
        """
        axesStr = ''
        axesList = self.pimCoords.get_axes()
        for axis in axesList:
            if type(axis) == types.StringType:
                axesStr += axis+", "
            elif type(axis) == types.ListType:
                for axel in axis:
                    if type(axel) == types.StringType:
                        axesStr += axel+", "
                    else:
                        err = "Coordinate ListType too deeply nested: "+ axel
                        raise CasaImageValueError, err
            else:
                err = "Unknown coordinate type in axis: "+axis
                raise CasaImageValueError, err
        return axesStr[:-2]


    def buildBeamInfo(self):
        """Populate self.meta with the imageinfo()['restoringbeam'] data,
        if present.  Pass if 'restoringbeam' information is not found.

        Parameters: none
        Return: void
        """
        beamKeys = [
            ('positionangle', 'BEAM-PA'),
            ('major'        , 'BEAM-MAJOR'),
            ('minor'        , 'BEAM-MINOR')
            ]
        unit = 'unit'
        val  = 'value'
        try:
            beam = self.pimageInfo['restoringbeam']
            for key, keyString in beamKeys:
                try:
                    bkey    = beam[key]
                    bkeyval = str(bkey[val])+" "
                    bunit   = bkey[unit]
                except KeyError: 
                    bkey= "Beam parameter: "+key+" not found."
                    continue
                self.meta.append((keyString, bkeyval+bunit))
        except KeyError:
            err = "Restoring Beam information not found."
            print err
            pass
        return


    def buildPointing(self):
        """Populate self.meta with pointing center information,

        POINTING,       RA    Dec

        where RA is in HMS format, Declination is in decimal degrees.
        
        The 'pointingcenter' value is returned as a array of floats,

        eg., 

        array([ 1.24585202,  0.78404044])

        RA, Dec order (assumed).

        Parameters: none
        Return: void
        """
        try:
            pc = self.pimCoords.dict()['pointingcenter']['value']
            ra = decdeg2hmsString(degrees(pc[0]))
            dec= decdeg2dmsString(degrees(pc[1]))
            self.meta.append(("POINTING", str(ra)+"\t"+str(dec)))
        except KeyError:
            print "Pointing Information not found."
            pass
        return


    def imStats(self):
        """Build the image statistics onto an instance meta structure.

        Parameters: none
        Return: void
        """
        stats = self.statistics()
        for stat in statInclusions:
            self.meta.append(("IMAGE-"+string.upper(stat),stringify(stats[stat])))
        return


    def buildCoords(self):
        """Build the Coordinates information onto an instance meta
        structure. Works from self.imAxes, which is type <string>.
        Listified here.

        Parameters: none
        Return: void
        """
        for i in range(len(self.axesNames)):
            coordinateType = self.axesNames[i]
            coordinateObj  = self.pimCoords.get_coordinate(coordinateType)
            self.__buildCoordData(coordinateObj,coordinateType,i)
        return

    ############################ output methods #################################

    def par(self, mimeType):
        """parse and render the meta structure to stdout.

        Parameters: <string>  mimetype of the passed data file.
        Return: void
        """
        self.parseImage(mimeType)
        self.render()
        return

    def render(self):
        """Pretty print to stdout.

        Parameters: none
        Return: void
        """
        for key,val in self.meta:
            if len(key) >= 15:
                print key,"\t",val
            elif len(key) < 8:
                print key+"  ","\t\t",val
            else: print key,"\t\t",val
        return

    def writeHdr(self, inFileName):
        """Write out the header data in self.meta as pretty print.

        The output filename is,

        <input name> + '.hdr'

        The inFileName <string> is passed here to handle the use case wherein
        an input tarfile name is not equal to the archived root path name for
        a Measurement Set or Casa Image.

        Parameters: <string>, a filename
        Return:     <string>, file name written.
        __________________
        Note: CyberSKA management determined that the output header file should
        be named as the input filename, and not the archived root name of the
        tar archive. 
        -- 28.09.2011
        """
        fileWrite = inFileName + ".hdr"
        fob = open(fileWrite,"w")
        for key,val in self.meta:
            sval = str(val)
            if len(key) >= 16:
                fob.write(key+"\t"+str(val)+"\n")
            elif len(key) < 8:
                fob.write(key+"  \t\t"+str(val)+"\n")
            else: fob.write(key+"\t\t"+str(val)+"\n")
        fob.close()
        return fileWrite

    #################################### prive #################################

    def __setInstanceAttrs(self, mimeType):
        """ Set some instance variables.

        Parameters: none
        Return: void
        """
        self.imFileName = basename(self.name())
        self.mimeType   = mimeType
        self.meta = []
        return

    def __buildCoordData(self, coordinateObj, coordinateType, i):
        """ Build a passed coordinate's metadata.

        Parameters: <instance>, <string>, <int>
        Return: void
        """
        self.meta.append(("COORDINATE"+str(i)+"-TYPE", coordinateType))
        try: 
            cname     = stringify(coordinateObj.get_axes())
            self.meta.append(("COORDINATE"+str(i)+"-NAME", cname))
        except AttributeError: pass
        try: 
            cunit    = stringify(coordinateObj.get_unit())
            self.meta.append(("COORDINATE"+str(i)+"-UNITS", str(cunit)))
        except AttributeError: pass
        try: 
            refpix   = stringify(coordinateObj.get_referencepixel())
            self.meta.append(("REFERENCE"+str(i)+"-PIXEL", refpix))
        except AttributeError: pass
        try:
            if coordinateType == 'direction':
                refval = coordinateObj.get_referencevalue()
                dec = decdeg2dmsString(degrees(refval[0]))
                ra  = decdeg2hmsString(degrees(refval[1]))
                raDecStr = dec+", "+ra
                self.meta.append(("REFERENCE"+str(i)+"-VALUE", raDecStr))
            elif coordinateType == 'spectral':
                reftup = convertHz(coordinateObj.get_referencevalue())
                refval = stringify(delist(reftup))
                self.meta.append(("REFERENCE"+str(i)+"-VALUE", refval))
            else: 
                refval = stringify(coordinateObj.get_referencevalue())
                self.meta.append(("REFERENCE"+str(i)+"-VALUE", refval))
        except AttributeError: pass
        try:
            reftype  = stringify(coordinateObj.__dict__['_coord']['system'])
            self.meta.append(("REFERENCE"+str(i)+"-TYPE", reftype))
        except KeyError: pass
        try:
            if coordinateType == 'direction':
                cincr   = coordinateObj.get_increment()
                cincdec = decdeg2dmsString(degrees(cincr[0]))
                cincra  = decdeg2dmsString(degrees(cincr[1]))
                cincstr = cincdec+", "+cincra
                self.meta.append(("INCREMENT"+str(i), cincstr))
                self.meta.append(("INCREMENT"+str(i)+"_UNITS","deg, deg"))
            elif coordinateType == 'spectral':
                cincr   = stringify(coordinateObj.get_increment())
                cinctup = convertHz(cincr)
                cincstr = cinctup[0]+" "+cinctup[1]
                self.meta.append(("INCREMENT"+str(i), cincstr))
            else:
                cincr = stringify(coordinateObj.get_increment())
                self.meta.append(("INCREMENT"+str(i), cincr))
        except AttributeError: pass
        try: 
            cframe = stringify(coordinateObj.get_frame())
            self.meta.append(("FRAME"+str(i), cframe))
        except AttributeError: pass
        try:
            cproj = stringify(coordinateObj.get_projection())
            self.meta.append(("PROJECTION"+str(i), cproj))
        except AttributeError: pass
        try: 
            rfreqtup = convertHz(stringify(coordinateObj.get_restfrequency()))
            restfreq = stringify(delist(rfreqtup))
            self.meta.append(("REST-FREQUENCY", restfreq))
        except AttributeError: pass
        try: 
            velunit  = stringify(coordinateObj.__dict__['_coord']['velUnit'])
            self.meta.append(("VELOCITY-UNIT", velunit))
        except KeyError: pass
        try: 
            veltype  = stringify(coordinateObj.__dict__['_coord']['velType'])
            self.meta.append(("VELOCITY-TYPE", vtranslate(veltype)))
        except KeyError: pass
        try: 
            latpole  = stringify(coordinateObj.__dict__['_coord']['latpole'])
            self.meta.append(("LATPOLE", latpole))
        except KeyError: pass
        try: 
            longpole  = stringify(coordinateObj.__dict__['_coord']['longpole'])
            self.meta.append(("LONGPOLE", longpole))
        except KeyError: pass

        return
