#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                     metaData.utils.genUtils.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "K.R. Anderson, <k.r.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

import math

"""General utility functions for Measurement Set and Casa Image metadata
scraping.
"""

def getAllColumnMetaData(msTab):
    """pass an MS top level table tool, print to stdout all column data found."""
    for mcol in msTab.colnames():
        print "\nColumn present:\t\t", mcol
        print "Current Column:\t\t", mcol
        print mcol,"keywords present:", msTab.colkeywordnames(mcol)
        print "__________________________"
        print mcol,"Keyword Values:"
        print msTab.getcolkeywords(mcol)
        print "__________________________"
    return

def convertHz(hz, kBase=1000):
    """Caller passes either a <string> or  <float> value
    representing a frequency.

    Returns a human-readable <string> displaying appropriate
    engineering units.

    i.e.
    
    >>> convertHz(8435100000.0)
    8.43 GHz

    >>> convertHz(8.43510000e+09)
    8.43 GHz
    """
    ensign = ''
    hz = float(hz)
    if hz < 0: ensign = '-'
    hz = abs(hz)
    hrUnits = ['Hz','kHz','MHz','GHz']
    hrindex = 0
    suffix  = hrUnits[hrindex]
    strn    = hz
    while hz >= 999.9:
        hz /= kBase
        hrindex += 1
        suffix = hrUnits[hrindex]
        # we only go to GHz ...
        if hrindex == 2: suffix = hrUnits[hrindex]
        if hz < 9.95 and hz != round(hz):
            strn = ensign+"%3.4f" % hz
        else: strn = ensign+"%d" % round(hz)
    return strn, suffix
    
