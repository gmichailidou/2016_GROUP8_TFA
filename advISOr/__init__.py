# -*- coding: utf-8 -*-
"""
/***************************************************************************
 advISOr
                                 A QGIS plugin
 This plugin is intented to detect the isolated areas from the public transport network
                             -------------------
        begin                : 2016-12-23
        copyright            : (C) 2016 by 2016 Group8 TuDelft GEO1005
        email                : lydiakotoula@outlook.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load advISOr class from file advISOr.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .advISOr import advISOr
    return advISOr(iface)
