#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                metaData.incl.imageInclusion.py
#                                                      Kenneth Anderson, 2011-08
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

""" Support for casaImageHandlers class.  Provides ... some kind of data structure
as an explicit inclusion specification for CASA Image data structures and embedded 
metadata.

Unlike a nominal Visibility Measurement Set (MIME Type: Image/ms-uvw), the top level
of a CASA Image expresses a list of data structures,

['logtable', 'coords', 'imageinfo', 'units']

only one of which is a Table, 'logtable', which is ignorable in this context.
N.B. Other keywords may be present, though the above set contains a reasonably 
complete metadata description.
"""

listInclusions=['imageinfo',
                'units',
                'coords',
                ]

coordKeyInclusions = ['telescope',
                      'observer',
                      'obsdate',
                      'pointingenter',
                      'telescopeposition',
                      'direction0', 
                      'stokes1',
                      'spectral2',
                      ]

imageinfoKeyInclusions = ['objectname',
                          'imagetype',
                          'restoringbeam',
                          ]

statInclusions = ['median',
                  'sigma',
                  'mean',
                  'rms',
                  'sum',
                  'min',
                  'max',
                  'minpos',
                  'maxpos'
                  ]
                  
velocityType = [ 'RADIO',
                 'OPTICAL',
                 'RATIO',
                 'TRUE',
                 'GAMMA'
                 ]



