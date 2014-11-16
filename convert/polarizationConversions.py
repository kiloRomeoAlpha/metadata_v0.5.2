#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                    metaData.convert.polarizationConversions.py
#                                                      Kenneth Anderson, 2011-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""metaDict keys subject to polarization conversions.  The CORR_TYPE 
string literals are supplied by casaStokesTypes.

This module provides the casaStokesTypes mapping list as a list of
polarization correlation type values. Array values found in the 
POLARIZATION table column, CORR_TYPE are index mapped against
casaStokesTypes.
eg., 

ngc4826.ms/POLARIZATION: CORR_TYPE = [[5 8]]

The index mapping list is 

casaStokesTypes = [ '' 'I', 'Q', 'U', 'V', 'RR', 'RL', 'LR', 'LL',
                    'XX', 'XY', 'YX', 'YY', 'RX', 'RY', 'LX', 'LY',
                    'XR', 'XL', 'YR', 'YL', 'PP', 'PQ', 'QP', 'QQ',
                    'RCircular', 'LCircular', 'Linear', 'Ptotal',
                    'Plinear', 'PFtotal', 'PFlinear', 'Pangle' ]

When mapped agains the casaStokesTypes list, the above indicated 
CORR_TYPE table values produce literal values for CORR_TYPE: 

CORR_TYPE    RR LL

polarizationConversions for casaStokesTypes actual.
"""

casaStokesTypes = [ '' 'I', 'Q', 'U', 'V', 'RR', 'RL', 'LR', 'LL',
                    'XX', 'XY', 'YX', 'YY', 'RX', 'RY', 'LX', 'LY',
                    'XR', 'XL', 'YR', 'YL', 'PP', 'PQ', 'QP', 'QQ',
                    'RCircular', 'LCircular', 'Linear', 'Ptotal',
                    'Plinear', 'PFtotal', 'PFlinear', 'Pangle' ]


polarizationKeys = [ 'POLARIZATION:CORR_TYPE']
