#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                         metaData.msHandlers.py
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
import sys

from os.path        import basename
from pyrap.tables   import table as pyraptable

from metaData.utils.runUtils import redirectStdOut,resetStdOut
from metaData.utils.runUtils import delist, isoDateTime, raDecConvert
from metaData.utils.runUtils import decdeg2dmsString, decdeg2hmsString
from metaData.utils.runUtils import stringify, polarizationConvert, ptime

from metaData.utils.genUtils import convertHz

from metaData.metaDataVersion import pkg_name,version

from metaData.incl.tablesInclusion import orderedTableNamesAsKeys, tableIncludes

from metaData.convert.timeConversions         import timeKeys
from metaData.convert.directionConversions    import directionKeys
from metaData.convert.polarizationConversions import polarizationKeys
from metaData.convert.frequencyConversions    import frequencyReference
from metaData.convert.frequencyConversions    import frequencyFields, referenceFields

""" Initial open and step through all keyword tables in a CASA 
Measuremet Set, slurping each table's metadata -- keyword-value pairs.
This module and class will provide methods to create a FITS-like "flat"
keyword/value header file, and an hierarchical xml markup of the Measurement
Set metadata.
"""


class MSTableValueError(AttributeError):
    """ An MSTableValueError will be raised when a Measurement Set contains
    an unknown element as presented by a call to keywordnames().  Only
    values of type,

    <float>
    <string>
    <list>
    
    are so far understood.

    eg., top level keywords, values of some Measurement Set

    key                       val
    ----------------------------------------
    'MS_VERSION'       2.0
    'ANTENNA'          'Table: /... .MS/ANTENNA'
    'DATA_DESCRIPTION' 'Table: /... .MS/DATA_DESCRIPTION'
    'FEED'             'Table: /... .MS/FEED'
    [...snip...]
    'STATE'            'Table: /... .MS/STATE'
    'SOURCE'           'Table: /... .MS/SOURCE'
    'SORTED_TABLE'     'Table: /... .MS/SORTED_TABLE'
    ['ARRAY_ID', 'FIELD_ID', 'DATA_DESC_ID', 'TIME']
    
    where,
    
    type(key)       type(val)
    -----------------------------
    (<type 'str'>, <type 'float'>)
    (<type 'str'>, <type 'str'>)
    (<type 'str'>, <type 'str'>)
    [...snip...]
    (<type 'str'>, <type 'str'>)
    (<type 'str'>, <type 'str'>)
    (<type 'str'>, <type 'str'>)
    (<type 'str'>, <type 'list'>)
    
    """
    pass


class MSHandlers(object):
    """Class defines CASA Measurement Set (MS) metadata handlers.
    Constructor opens a passed Measurement Set name.
    """

    def __init__(self, msFile):
        """ Open the Measurement Set file. Caller receives an MSHandler 
        object with four (4) attributes: the passed filename, a casacore table
        tool for the passed CASA measurement set, and unpopulated data
        structures,  "meta" of type <list> and "metaDict" of type <dict>

        *** This constructor fiddles with stdout to suppress
        pyrap.tables.table stdout output, which is not desired as part of
        stdout output from this module. ***

        self.meta will be a list of tuples, wherein ordered keys and values
        are maintained.

        eg., 
        
        [
        ('OBSERVER','Some Blasted Astronomer'),
        ('TELESCOPE', 'WSRT'),
        ('PROJECT', '' )
        ('RELEASE_DATE', 'Jan 01, 2011'),
         ...
        ]
        """

        fsock,saveStdOut = redirectStdOut()
        self.msFileName = msFile
        self.msObj      = pyraptable(msFile)
        self.metaDict   = {}
        self.meta       = []                 # ordered meta tuples 
        resetStdOut(fsock,saveStdOut)

        
    def parseMS(self, mimeType):
        """Parse and extract all meta info from a Measurement Set.
        A FloatType value will be the MS_VERSION, likely 2.0.
        Only one FloatType keyword value has been observed to date,
        04/08/2011.
        
        Passed mimeType is type <string>. Should be derived from
        the MSMimeTyping class (msMimeTyping.py), and will have the
        form,
        
          'image/ms-uvw'

        to indicate a Visibility (UV) Measurement Set.
        """

        self.mimeType  = mimeType
        self.msVersion = None
        topLevelNames  = self.msTopLevelKeywords()
        orderedKeyVals = []
        topLevelTables = []

        for name in topLevelNames:
            val = self.msObj.getkeyword(name)
            orderedKeyVals.append((name,val))

        for key,val in orderedKeyVals:
            if type(val) == types.FloatType:
                if key == "MS_VERSION":
                    self.msVersion =(key, val)
                    continue
                else: pass
            elif type(val) == types.ListType:
                continue
            elif type(val) == types.StringType:
                if "Table:" in val:
                    topLevelTables.append(val.split(':')[1].strip())
                else:
                    err = "Unknown Measurement Set keyword value:"+val
                    raise MSTableValueError,err
        
        self.openTopLevelTables(topLevelTables)
        self.msObj.close()
        return


    def openTopLevelTables(self,tableNames):
        """
        Open the MS tables iteratively, calling the .__extract method to
        parse, sift, and extract equired metadata. 

        """
        for subTableName in tableNames:
            trimmedSubTableName = basename(subTableName)
            if trimmedSubTableName in orderedTableNamesAsKeys:
                subTableTool = self.__openSubTable(subTableName)
                #print "\nExtracting from Table:", trimmedSubTableName,"..."
                self.__extract(trimmedSubTableName,subTableTool)
            else:continue
        return
            

    def msTopLevelKeywords(self):
        """ Return a list of top level keyword names as returned by a 
        table tool's keywordnames() method.  At the top level, keywords
        will be a mix of plain keywords, and table names.
        """
        keyWordNames = self.msObj.keywordnames()
        return keyWordNames


    def msTableKeywords(tableObj):
        keyWordNames = tableObj.keywordnames()
        return keyWordNames


    def buildFlatMeta(self):
        """Build an ordered list of tuples, the "meta" data structure,
        for key-val flat files from the extracted metadata in self.metaDict
        """

        # The following header data have been requested removed by
        # A. Grimstrup, 04-10-11
        #
        # self.meta.append(("FILENAME",    basename(self.msFileName))
        # self.meta.append(("MIME-TYPE",   self.mimeType))
        #
        # -------------------------------------------------------------------- #

        self.meta.append(("FILETYPE",    "Visibility Measurement Set"))
        if self.msVersion: self.meta.append(("MS-VERSION",  self.msVersion[1]))

        # The "OBSERVATION" key is special as primary information

        for tabKey in orderedTableNamesAsKeys:
            if tabKey == "OBSERVATION": self.__buildObsKey(tabKey)
            else: self.__buildGenericKey(tabKey)
        self.meta.append(("PARSER",pkg_name+", v"+version))
        self.meta.append(("PARSE-DATE",  ptime().split("T")[0]))
        return


    def render(self):
        """Write the meta data structure to stdout."""
        for key,val in self.meta:
            if len(key) >= 15:
                print key,"\t",val
            elif len(key) <= 4:
                print key,"\t\t\t",val
            else:
                print key,"\t\t",val
        return

    def writeHdr(self, inFileName):
        """write out the header data in self.meta as pretty print to 
        a header file.

        The inFileName <string> is passed to handle the use case wherein
        an input tarfile name is not equal to the archived root path name
        for a Measurement Set or Casa Image.

        CyberSKA management determined that the output header file should
        be named as the input filename, and not the archived root name of
        the tar archive. 
        -- 28.09.2011
        """
        frequency_truncs = ['CHAN_FREQ','CHAN_WIDTH','EFFECTIVE_BW','RESOLUTION']
        hdrFile = inFileName+".hdr"
        fob     = open(hdrFile,"w")

        for key,val in self.meta:
            sval = str(val)
            if "_DIR" in key:
                self.__writeSetValues(key,sval,fob)
                continue
            elif ":POSITION" in key:
                self.__writeSetValues(key,sval,fob)
                continue
            elif key == "WINDOW_NAME":
                self.__writeWinNames(key,sval,fob)
                continue
            # elif key in frequency_truncs and len(sval) > 55:
            #     self.__writeTruncValues(key,sval,fob)
            #     continue
            elif len(sval) > 55:
                self.__writeLongValue(key,sval,fob)
                continue
            self.__writeNominalValue(key,sval,fob)
        fob.write("\n")
        fob.close()
        return hdrFile
                

    #################################### prive #################################

    def __openSubTable(self,tableName):
        """ Open a passed table name from Measurement Set top level.
        The table name is a POSIX like string.
        tableName, <string>

        eg., The OBSERVATION table of the Measurement Set
        N6251_36M_1950.MS is simply

        /data/testing/msdata/N6251_36M_1950.MS/OBSERVATION

        As in the contructor, this method fiddles with stdout to suppress
        pyrap.tables.table print output when opening all subTables.
        """
        fsock,saveStdOut = redirectStdOut()
        pyrapttool = pyraptable(tableName)
        resetStdOut(fsock,saveStdOut)
        return pyrapttool

    def __extract(self, tableName,tableTool):
        """
        Slurp the metadata from the passed table tool object.
        These data are placed in the instance's meta tuple list.
        An undefined column will raise a RuntimeError exception,
        and will be marked at 'Undefined.'

        """

        for keyName in tableIncludes[tableName]:
            try: keyval = tableTool.getcol(keyName)
            except RuntimeError: keyval = "Undefined"; pass
            self.metaDict[tableName+':'+keyName]= keyval
        tableTool.close()
        return

    def __buildObsKey(self,obsKey):
        for subKey in tableIncludes[obsKey]:
            metaDictKey = obsKey+":"+subKey
            if subKey == "TIME_RANGE":
                self.meta.append(("DATE-OBS",      self.__startObs()))
                self.meta.append(("DATE-OBS-MJD",  self.__mjdDate()/86400))
                self.meta.append(("START-OBS",     self.__startObs()))
                self.meta.append(("END-OBS",       self.__endObs()))
                self.meta.append(("EXPOSURE",      self.__expTime()))
                self.meta.append(("EXPOSURE-UNIT", 'seconds'))
            else: 
                self.meta.append((subKey, 
                                  delist(list(set(self.metaDict[metaDictKey])))))
        return

    def __buildGenericKey(self,tabKey):
        tossKeys = ["DATA_DESCRIPTION", "POLARIZATION", "SPECTRAL_WINDOW"]
        for subKey in tableIncludes[tabKey]:
            if tabKey in tossKeys: metaKey=subKey
            else: metaKey = tabKey+":"+subKey
            if tabKey == tossKeys[-1] and subKey == "NAME":
                metaKey = "WINDOW_"+subKey
            metaDictKey = tabKey+":"+subKey
            if metaDictKey in timeKeys:
                timeList = self.__convertTimeValues(metaDictKey)
                self.meta.append((metaKey, delist(timeList)))
            elif metaDictKey in directionKeys:
                dirList = self.__convertDirValues(metaDictKey)
                self.meta.append((metaKey, dirList))
            elif metaDictKey in polarizationKeys:
                polList = self.__convertPolValues(metaDictKey)
                self.meta.append((metaKey, polList))
            elif metaDictKey in frequencyFields:
                freqVals = self.__convertFreqValues(metaDictKey)
                self.meta.append((metaKey, freqVals))
            elif metaDictKey in referenceFields:
                refs = self.__convertReferences(metaDictKey)
                self.meta.append((metaKey, refs))
            else: self.meta.append((metaKey, delist(self.metaDict[metaDictKey])))
        return

    def __startObs(self):
        timeStr = delist(self.metaDict['OBSERVATION:TIME_RANGE'][0]).split(',')[0]
        return isoDateTime(timeStr)

    def __endObs(self):
        timeStr = delist(self.metaDict['OBSERVATION:TIME_RANGE'][0]).split(',')[1]
        return isoDateTime(timeStr)

    def __mjdDate(self):
        return float(delist(self.metaDict['OBSERVATION:TIME_RANGE'][0]).split(',')[0])

    def __expTime(self):
        return (self.metaDict['OBSERVATION:TIME_RANGE'][0][1] -
                self.metaDict['OBSERVATION:TIME_RANGE'][0][0])

    def __expUnits(self):
        """Not implemented."""
        return delist(self.msObj.getcolkeywords('EXPOSURE')['QuantumUnits'])

    ########################## Conversions ################################

    def __convertTimeValues(self,dictKey):
        """Caller passes a known TIME type key, converts values
        in metaDict to the proper TIME type (see timeConversions), 
        i.e. ISO8601 Date-Time format, as returned by the runUtils
        function, isoDateTime().
        """
        return [isoDateTime(val) for val in self.metaDict[dictKey]]
        
    def __convertDirValues(self,dictKey):
        """Caller passes a known direction type key, converts values
        in metaDict to RA,Dec in HMS,decdegrees (see directionConversions).
        """
        radecString = ''
        for dpair in self.metaDict[dictKey]:
            radecString += raDecConvert(dpair)
        return radecString

    def __convertPolValues(self,dictKey):
        """Caller passes a known polarization type key, converts values
        in metaDict to the appropriate string literal (see directionConversions).
        Only one use case present thus far:

        POLARIZATION:CORR_TYPE 

        The try-except clause is now present to handle cases where the POLARIZATION
        CORR-TYPE is not defined.  This would throw an TypeError exception from 
        runUtils.polarizationConvert(), which expects an nested array of integers.
        As discovered in dataset uid___X02_X56142_X1.MS provided by the CASA regression
        test site: 

        casa-data - Revision 5175:/trunk/regression/exportasdm/input
        @ https://svn.cv.nrao.edu/svn/

        -- 23-11-2011.kra
        """
        try: corrType = polarizationConvert(self.metaDict[dictKey])
        except TypeError: corrType = "Undefined"
        return corrType

    def __convertFreqValues(self,dictKey):
        """Callers pass a dictKey that pertains to 'SPECTRAL_WINDOW'
        table values. Most 'SPECTRAL_WINDOW' values specified in
        tableIncludes will be found in units of Hz. These values are
        required to be reported in 'human readable' form, i.e. kHz, 
        MHz, GHz.
        
        Non-iterables will throw a TypeError exception in the list
        comprehension, which is then handled.
        """
        nestedArrs = [ 'SPECTRAL_WINDOW:CHAN_FREQ',
                       'SPECTRAL_WINDOW:CHAN_WIDTH',
                       'SPECTRAL_WINDOW:EFFECTIVE_BW',
                       'SPECTRAL_WINDOW:RESOLUTION'
                       ]
        singleArrs = [ 'SPECTRAL_WINDOW:REF_FREQUENCY',
                       'SPECTRAL_WINDOW:TOTAL_BANDWIDTH'
                       ]
                       
        if dictKey in nestedArrs: freqString = self.__handleNest(dictKey)
        elif dictKey in singleArrs: freqString = self.__handleSingle(dictKey)
        else: raise MSTableValueError, "unknown dictKey: "+dictKey
        return freqString
        
    def __convertReferences(self,dictKey):
        """Callers pass a dictKey that pertains to the specific
        'SPECTRAL_WINDOW:MEAS_FREQ_REF' parameter.  This is converted from
        a set of <int> values, like

        >>> self.metaDict['SPECTRAL_WINDOW:MEAS_FREQ_REF']
        array([5, 5], dtype=int32)

        by index mapping against the frequencyConversions.frequencyReference
        list.  Such a mapping should result in a string value that looks like
        
        'TOPO, TOPO'
        """
        refVals = self.metaDict[dictKey]
        return ", ".join(["%s" % frequencyReference[val] for val in refVals])

    ############################ channel handlers ###########################

    def __handleNest(self,dictKey):
        fbegin = fend = ' '
        freqValues = self.metaDict[dictKey]
        if type(freqValues) != types.StringType:
            freqString = ''
            for i in range(len(freqValues)):
                lenf = len(freqValues[i])
                fbegin = "%s %s" % convertHz(list(freqValues[i])[0])
                if lenf > 1:
                    fend = " [..] %s %s" % convertHz(list(freqValues[i])[-1])
                    fend += " ("+str(lenf)+" chan), "
                freqString += fbegin + fend
        elif type(freqValues) == types.StringType:
            freqString   = freqValues
        else: freqString = "Unknown frequency field datatype"
        return freqString

    def __handleSingle(self, dictKey):
        freqString = ''
        freqValues = self.metaDict[dictKey]
        if type(freqValues) != types.StringType:
            freqString = ", ".join("%s %s" % convertHz(freq) for freq in (list(freqValues)))
        elif type(freqValues) == types.StringType:
            freqString   = freqValues
        else: freqString = "Unknown frequency datatype"
        return freqString

    ###################### file output support methods ######################

    def __writeWinNames(self,key,val,fob):
        """Write the channel names for SPECTRAL_WINDOW:NAME key. These will 
        very often be null strings, which should then not be written as blank lines.
        """
        vals = val.split(',')
        if not vals[0].strip():
            if   len(key) >= 16: fob.write("\n"+key+"\tNone")
            elif len(key) <= 7:  fob.write("\n"+key+"\t\t\tNone")
            else: fob.write("\n"+key+"\t\tNone")
        else: self.__writeNominalValue(key,vals[0],fob)
        if len(vals) > 1:
            for nextval in vals[1:]:
                if not nextval.strip(): continue
                else: fob.write("\n\t\t"+nextval)
        fob.flush()
        return

    def __writeSetValues(self, key,val,fob):
        """Write a set of direction values, one pair per line."""
        vals = val.split(',')
        self.__writeNominalValue(key,vals[0],fob)
        if len(vals) > 1:
            fob.write("\n\t\t\t")
            fob.write("\n\t\t\t".join([val for val in vals[1:]]))
        fob.flush()
        return

    def __writeTruncValues(self,key,val,fob):
        """Write the first value of a long string set of channel frequency
        information for those values in the frequency_truncs list.
        Key length checks are not needed, as the lengths of these keys
        are known to be > 7 & < 16.
        """
        fvals = val.split(',')
        fob.write("\n"+key+"\t\t"+fvals[0]+" ... "+fvals[-1])
        fob.flush()
        return

    def __writeLongValue(self,key,val,fob):
        """Write lines for a val considered to be 'long.'
        Method splits the val string, write the pieces
        properly to the passed file object.
        """
        line    = ''
        values  = val.split(',')
        lineset = []

        for item in values:
            if not item.strip(): continue
            if len(line) <= 55:
                line += item+", "
                continue
            else:
                lineset.append(line)
                line = item+", "
        lineset.append(line)

        # lineset list will have a set of lines.
        # First one gets the key.

        self.__writeNominalValue(key,lineset[0],fob)

        if len(lineset) > 1:
            fob.write("\n\t\t\t")
            fob.write("\n\t\t\t".join([line for line in lineset[1:]]))
        fob.flush()
        return

    def __writeNominalValue(self,key,val,fob):
        """Write a header line where the passed val is 
        written to one line. The passed value, 'val' must
        be of type <string>.
        """
        if len(key) >= 16:
            fob.write("\n"+key+"\t"+val)
        elif len(key) <= 7:
            fob.write("\n"+key+"\t\t\t"+val)
        else:
            fob.write("\n"+key+"\t\t"+val)
        fob.flush()
        return
