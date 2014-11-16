#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                               metaData.incl.tablesInclusion.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

""" Support for msHandlers class.  Provides explicit inclusion
specifications for Measurement Set tables and embedded metadata.
"""


orderedTableNamesAsKeys = [
    'OBSERVATION',
    'DATA_DESCRIPTION',
    'POLARIZATION',
    'SPECTRAL_WINDOW',
    'FIELD',
    'ANTENNA'
    ]


tableIncludes = {
'ANTENNA':
    ['NAME',
     'STATION',
     'DISH_DIAMETER',
     'POSITION',
     'TYPE',
     ],

'DATA_DESCRIPTION': 
    ['SPECTRAL_WINDOW_ID',
     'POLARIZATION_ID',
     ],

'FIELD':
    ['NAME',
     'TIME',
     'SOURCE_ID',
     'REFERENCE_DIR',
     #'CODE',
     'PHASE_DIR',
     #'DELAY_DIR',
     ],

'OBSERVATION':
    ['PROJECT',
     'OBSERVER',
     'TELESCOPE_NAME',
     'TIME_RANGE'
     ],

'POLARIZATION':
    ['CORR_TYPE'],

'SPECTRAL_WINDOW':
    ['NUM_CHAN',
     'NAME',
     'REF_FREQUENCY',
     'TOTAL_BANDWIDTH',
     'MEAS_FREQ_REF',
     'CHAN_FREQ',
     'CHAN_WIDTH',
     'EFFECTIVE_BW',
     'RESOLUTION'
     ]
}

     
     
