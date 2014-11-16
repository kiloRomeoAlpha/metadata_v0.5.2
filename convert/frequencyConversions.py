#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                       metaData.convert.frequencyConversions.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------


# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""metaDict keys subject to frequency unit conversions."""

frequencyFields = ['SPECTRAL_WINDOW:REF_FREQUENCY',
                   'SPECTRAL_WINDOW:EFFECTIVE_BW',
                   'SPECTRAL_WINDOW:TOTAL_BANDWIDTH',
                   'SPECTRAL_WINDOW:CHAN_WIDTH',
                   'SPECTRAL_WINDOW:CHAN_FREQ',
                   'SPECTRAL_WINDOW:RESOLUTION'
                   ]

referenceFields = [ 'SPECTRAL_WINDOW:MEAS_FREQ_REF'
                       ]

# This FREQUENCY REFERENCE DIRECTORY is plucked from casacore
# namespace casa, Measures.MFrequency

frequencyReference = ["REST",
                      "LSRK", 
                      "LSRD",
                      "BARY", 
                      "GEO", 
                      "TOPO", 
                      "GALACTO", 
                      "LGROUP", 
                      "CMB" 
                      ]
