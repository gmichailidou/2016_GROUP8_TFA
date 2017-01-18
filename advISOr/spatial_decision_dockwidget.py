# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpatialDecisionDockWidget
                                 A QGIS plugin
 This is a SDSS template for the GEO1005 course
                             -------------------
        begin                : 2015-11-02
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Jorge Gil, TU Delft
        email                : j.a.lopesgil@tudelft.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtGui, QtCore, uic
from qgis.core import *
from qgis.networkanalysis import *
from qgis.gui import *
import processing
import webbrowser

# matplotlib for the charts
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Initialize Qt resources from file resources.py
import resources

import os
import os.path
import random
import csv
import time
#import matplotlib.pyplot as plt
#import plotly.plotly as py
#import plotly.plotly as py
#import plotly.graph_objs as go

from . import utility_functions as uf    # error


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'spatial_decision_dockwidget_base.ui'))


class SpatialDecisionDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = QtCore.pyqtSignal()
    #custom signals
    updateAttribute = QtCore.pyqtSignal(str)

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(SpatialDecisionDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # define globals
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.clickTool = QgsMapToolEmitPoint(self.canvas)
        self.panTool = QgsMapToolPan(self.canvas)

        # set up GUI operation signals


        # GUI
        self.iface.projectRead.connect(self.updateNodeCensusScenario)
        self.iface.newProjectCreated.connect(self.updateNodeCensusScenario)
        self.iface.legendInterface().itemRemoved.connect(self.updateNodeCensusScenario)
        self.iface.legendInterface().itemAdded.connect(self.updateNodeCensusScenario)


        # data
        self.loadRotterdamdataButton.clicked.connect(self.warningLoadData)
        self.createScenarioButton.clicked.connect(self.createScenario)
        self.scenarioPath = QgsProject.instance().homePath()
        self.scenarioAttributes = {}
        self.subScenario = {}

        # add button icons
        self.bigiconButton.setIcon(QtGui.QIcon(':icons/advisor.png'))
        self.bigiconButton.clicked.connect(self.openinBrowser)

        # indicators
        self.sliderValue_2.textChanged.connect(self.sliderTextChanged2)
        self.selecttimeCombo.activated.connect(self.setTimeSlot)
        self.selecttimeCombo.activated.connect(self.selectfreq)
        self.horizontalSlider.sliderMoved.connect(self.sliderMoved2)
        self.nodesFrequencyLayer.clicked.connect(self.warningFrequencyNodes)
        self.selecttimeCombo.activated.connect(self.MaxThresholdText)


        # initialize
        #self.sliderInit()

        # analysis
        self.sliderValue.textChanged.connect(self.sliderTextChanged)
        self.stationDistanceSlider.sliderMoved.connect(self.sliderMoved)
        self.bufferbutton.clicked.connect(self.warningbuffer)
        self.distanceVisiblecheckBox.stateChanged.connect(self.distanceVisible)
        self.initialareas.clicked.connect(self.layer_initial)
        self.criticalarea.clicked.connect(self.layerpopulation)
        self.initialareasVisiblecheckBox.stateChanged.connect(self.initialVisible)
        self.screenshotButton.clicked.connect(self.savemap)
        self.initialareas.clicked.connect(self.MaxThresholdCritical)

        # report
        self.getinfo.clicked.connect(self.getsummary)
        self.saveStatisticsButton.clicked.connect(self.saveTable)
        self.statistics.clicked.connect(self.extractAttributeSummary)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    # data functions

    def openinBrowser(self):
        webbrowser.open('https://github.com/gmichailidou/2016_GROUP8_advISOr/wiki', new=2)

    def createScenario(self):
        # select the node layer
        vl = self.getNodesLayer()
        # create a path and filename for the new file
        path = QtGui.QFileDialog(self).getSaveFileName()
        if path:
            list_path = path.split("/")[:-1]
            real_path = '/'.join(list_path)
            # make a directory for scenario
            if not os.path.exists(path):
                os.makedirs(path)
            # save the scenario path
            self.scenarioPath = real_path
            current_scenario = path.split("/")[-1]

            vlayer = uf.copyLayerToShapeFile(vl, path, filename)


    def updateNodeCensusScenario(self):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        nodes_text = self.selectNodesCombo.currentText()
        if nodes_text == '':
            nodes_text = 'Network_Nodes'
        census_text = self.selectCensusCombo.currentText()
        if census_text == '':
            census_text = 'Demographic_Data_Rotterdam_2014(GRID)'
        self.selectNodesCombo.clear()
        self.selectCensusCombo.clear()
        if layers:
            layer_names = uf.getLayersListNames(layers)
            self.selectNodesCombo.addItems(layer_names)
            self.selectCensusCombo.addItems(layer_names)
            if layer_names.__contains__(nodes_text):
                index = self.selectNodesCombo.findText(nodes_text)
                self.selectNodesCombo.setCurrentIndex(index);
            if layer_names.__contains__(census_text):
                index = self.selectCensusCombo.findText(census_text)
                self.selectCensusCombo.setCurrentIndex(index);


    def warningLoadData(self):
        msgBox = QtGui.QMessageBox()
        msgBox.setText("This will delete all current layers, continue?")
        msgBox.setStandardButtons(QtGui.QMessageBox.Yes)
        msgBox.addButton(QtGui.QMessageBox.No)
        msgBox.setDefaultButton(QtGui.QMessageBox.No)
        if msgBox.exec_() == QtGui.QMessageBox.Yes:
            self.loadRotterdamButton()

    def loadRotterdamButton(self):
        data_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'Final_Rotterdam_data.qgs')
        self.iface.addProject(data_path)

        #initialize
        self.sliderInit()

    def getNodesLayer(self):
        layer_name = self.selectNodesCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    def getBaseNodeLayer(self):
        layer_name = self.selectNodeCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

        #
        ####indicators functions
        #

        # not fctnl
    def selectfreq(self):
        sel_freq = self.run_mouse()

        # not fctnl
    def run_mouse(self):
        self.canvas.setMapTool(self.panTool)

        # OK - 6 fields (timeslots) from layer RT Network Nodes appear and user can choose, Buttons enable only if a timeslot is chosen
    def setTimeSlot(self):
        value = self.sliderValue_2.text()
        timeslot = self.selecttimeCombo.currentText()
        if timeslot == 'Select time-slot':
            self.horizontalSlider.setEnabled(False)
            self.sliderValue_2.setEnabled(False)
        else:
            self.horizontalSlider.setEnabled(True)
            self.sliderValue_2.setEnabled(True)

            nodeLayer = uf.getLegendLayerByName(self.iface, "PT Network Nodes")
            if timeslot == 'Weekdays - Morning Rush Hours':
                timeslot_field = 'Rh1_Wd/h'
                return timeslot_field
            elif timeslot == 'Weekdays - Afternoon Rush Hours':
                timeslot_field = 'Rh2_Wd/h'
                return timeslot_field
            elif timeslot == 'Weekdays - Non Rush Hours':
                timeslot_field = 'NRh_Wd/h'
                return timeslot_field
            elif timeslot == 'Weekends - Morning Rush Hours':
                timeslot_field = 'Rh1_We/h'
                return timeslot_field
            elif timeslot == 'Weekends - Afternoon Rush Hours':
                timeslot_field = 'Rh2_We/h'
                return timeslot_field
            elif timeslot == 'Weekends - Non Rush Hours':
                timeslot_field = 'NRh_We/h'
                return timeslot_field

        # Ok - maximum threshold value for the slider(threshold)
    def sliderInit(self):
        value = self.sliderValue_2.text()
        self.horizontalSlider.setValue(96)
        self.horizontalSlider.setValue(int(value))

        # ??. Check if threshold is empty
    def sliderTextChanged2(self):
        value = self.sliderValue_2.text()
        try:
            self.horizontalSlider.setValue(int(value))
        except:
            print 'Fill in a number.'

        # Ok
    def sliderMoved2(self, value):
        self.sliderValue_2.setText(str(value))


    def warningFrequencyNodes(self):
            # check if layer already exists
        #current_scenario = self.scenarioCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface,'_nodes_filtered')
        if layer:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(
                "The layer for the nodes filtering (by the frequency threshold) is already calculated for this scenario, overwrite current layer?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes)
            msgBox.addButton(QtGui.QMessageBox.No)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.layerFreqNodes()
        else:
            self.layerFreqNodes()

    def filterNodes(self):
        nodesLayer = uf.getLegendLayerByName(self.iface, "PT Network Nodes")
        nodes = nodesLayer.getFeatures()
        value = uf.convertNumeric(self.sliderValue_2.text())
        timeslot_field = self.setTimeSlot()
        filtered_points = []
        attributes= []
        for feature in nodes:
            #print feature
            column = feature.attribute(timeslot_field)
            #print column
            if column > value:
                values = []
                values.append(feature.attribute('id'))
                values.append(feature.attribute('name'))
                values.append(feature.attribute('ModeType'))
                values.append(feature.attribute(timeslot_field))

                attributes.append(values)
                filtered_points.append(feature.geometry().asPoint())

        return filtered_points,attributes

    def layerFreqNodes(self):
            # delete old layer if present
        old_layer = uf.getLegendLayerByName(self.iface,'_nodes_filtered')
        if old_layer:
            QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())

            # create one if it doesn't exist and add suffix for the scenario
        nodeLayer = uf.getLegendLayerByName(self.iface, "PT Network Nodes")
        freq_layer = uf.getLegendLayerByName(self.iface,'_nodes_filtered')
        if not freq_layer:
            timeslot_field = self.setTimeSlot()
            attribs = ['id', 'name', 'ModeType', timeslot_field]
            types = [QtCore.QVariant.Int, QtCore.QVariant.String, QtCore.QVariant.String, QtCore.QVariant.Int]
            freq_layer = uf.createTempLayer('_nodes_filtered','POINT',nodeLayer.crs().postgisSrid(), attribs, types)
            freq_layer.setLayerName('_nodes_filtered')
            uf.loadTempLayer(freq_layer)

            # insert pointsgeom & values
        tuple = self.filterNodes()

        uf.insertTempFeatures(freq_layer, tuple[0], tuple[1])

    def MaxThresholdText(self):
        timeslot_field = self.setTimeSlot()
        if timeslot_field == 'Rh1_Wd/h':
            self.label_10.setText('35 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')
        elif timeslot_field == 'Rh2_Wd/h':
            self.label_10.setText('30 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')
        elif timeslot_field == 'NRh_Wd/h':
            self.label_10.setText('25 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')
        elif timeslot_field == 'Rh1_We/h':
            self.label_10.setText('30 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')
        elif timeslot_field == 'Rh2_We/h':
            self.label_10.setText('26 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')
        elif timeslot_field == 'NRh_We/h':
            self.label_10.setText('20 is the maximum frequency per hour value that a mode(s) pass\n from a node for the selected timeslot')


        # analysis functions

    def warningbuffer(self):

        # check if layer already exists
        layer = uf.getLegendLayerByName(self.iface,'Buffers')
        if layer:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("The Buffer Layer is already calculated for this scenario, overwrite current layer?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes)
            msgBox.addButton(QtGui.QMessageBox.No)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.calculateBuffer()
        else:
            self.calculateBuffer()

    def savemap(self):
        path = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'PNG(*.png)')
        if path:
            self.canvas.saveAsImage(path, None, "PNG")

    def sliderInit(self):
        value = self.sliderValue.text()
        self.stationDistanceSlider.setValue(2000)
        self.stationDistanceSlider.setValue(int(value))

    def sliderTextChanged(self):
        value = self.sliderValue.text()
        try:
            self.stationDistanceSlider.setValue(int(value))
        except:
            print 'fill in a number'

    def sliderMoved(self, value):
        self.sliderValue.setText(str(value))


            # buffer functions

    def distanceVisible(self):
        layer_name ="Buffers"
        checked = self.distanceVisiblecheckBox.isChecked()
        if checked is True:
            self.setLayerVisibility(layer_name, True)
        elif checked is False:
            self.setLayerVisibility(layer_name, False)


    def initialVisible(self):

        layer_name = "initial_areas"
        checked = self.initialareasVisiblecheckBox.isChecked()
        if checked is True:
            self.setLayerVisibility(layer_name, True)
        elif checked is False:
            self.setLayerVisibility(layer_name, False)

    def setLayerVisibility(self, layer_name, bool):
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        if layer:
            legend = self.iface.legendInterface()
            legend.setLayerVisible(layer, bool)

    def getBufferCutoff(self):
        cutoff = self.bufferCutoffEdit.text()
        if uf.isNumeric(cutoff):
            return uf.convertNumeric(cutoff)
        else:
            return 0

    def getSelectedLayer(self):
        layer_name = self.selectCensusCombo.currentText()
        print layer_name
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    def calculateBuffer(self):
        # store the buffer results in temporary layer called "Buffers"
        old_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        if old_layer:
            QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())
        buffer_layer = uf.getLegendLayerByName(self.iface, "Buffers")
        layer = self.getSelectedLayer()
        origins = layer.getFeatures()
        if origins > 0:
            cutoff_distance = uf.convertNumeric(self.sliderValue.text())
            buffers = []
            attributes = []
            for point in origins:
                values = []
                values.append(point.attribute('sid'))
                values.append(point.attribute('inw2014'))
                values.append(point.attribute('group_pop'))
                values.append(point.attribute('popden10m2'))

                attributes.append(values)
                geom = point.geometry()
                buffers.append(geom.buffer(cutoff_distance,12).asPolygon())
            # create one if it doesn't exist
            if not buffer_layer:
                attribs = ['sid','inw2014','group_pop','popden10m2']
                types = [QtCore.QVariant.Double, QtCore.QVariant.Double, QtCore.QVariant.Double, QtCore.QVariant.Double]
                buffer_layer = uf.createTempLayer('Buffers','POLYGON',layer.crs().postgisSrid(), attribs, types)
                buffer_layer.setLayerName('Buffers')
                uf.loadTempLayer(buffer_layer)
                legend = self.iface.legendInterface()
                legend.setLayerVisible(buffer_layer, False)
            # insert buffer polygons
            uf.insertTempFeatures(buffer_layer, buffers , attributes)


    def getSelectedLayer(self):
        layer_name = self.selectCensusCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    # show buffers with nodes inside in order to delete them
    def getfeaturesforinitialareas(self):
        NetworkNodes_layer = uf.getLegendLayerByName(self.iface, "_nodes_filtered")
        buffer = uf.getLegendLayerByName(self.iface, 'Buffers')
        bufferfeatures=buffer.getFeatures()

        features = uf.getFeaturesByIntersection(buffer, NetworkNodes_layer, True)

        values = []

        for i in features:
            values.append(i.attribute('sid'))

        geometrybuffer=[]
        attributes=[]

        for i in bufferfeatures:
            column =i.attribute('sid')
            if column not in values:

                val = []
                val.append(i.attribute('sid'))
                val.append(i.attribute('inw2014'))
                val.append(i.attribute('group_pop'))
                val.append(i.attribute('popden10m2'))

                attributes.append(val)
                geometrybuffer.append(i.geometry().asPolygon())

        return attributes, geometrybuffer

    def layer_initial(self):
        layer=uf.getLegendLayerByName(self.iface,'Buffers')
        # delete old layer if present
        old_layer = uf.getLegendLayerByName(self.iface,'initial_areas')
        if old_layer:
            QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())

            # create one if it doesn't exist and add suffix for the scenario
        initial_areas = uf.getLegendLayerByName(self.iface, 'initial_areas')
        if not initial_areas:
            attribs = ['sid', 'inw2014', 'group_pop', 'popden10m2']
            types = [QtCore.QVariant.Double, QtCore.QVariant.Double, QtCore.QVariant.Double, QtCore.QVariant.Double]
            initial_areas = uf.createTempLayer('initial_areas', 'POLYGON', layer.crs().postgisSrid(), attribs, types)
            initial_areas.setLayerName('initial_areas')
            uf.loadTempLayer(initial_areas)
            legend = self.iface.legendInterface()
            legend.setLayerVisible(initial_areas, False)

            # insert pointsgeom & values
        tuple = self.getfeaturesforinitialareas()

        uf.insertTempFeatures(initial_areas, tuple[1], tuple[0])


    def filter_with_population(self):
        initialLayer = uf.getLegendLayerByName(self.iface, "initial_areas")
        areas = initialLayer.getFeatures()
        threshold = uf.convertNumeric(self.populationthreshold.text())
        filtered_areas = []
        attributes = []
        for feature in areas:
            column = feature.attribute('group_pop')
            if column >= threshold:
                values = []
                values.append(feature.attribute('sid'))
                values.append(feature.attribute('inw2014'))
                values.append(feature.attribute('group_pop'))
                values.append(feature.attribute('popden10m2'))

                attributes.append(values)
                filtered_areas.append(feature.geometry().asPolygon())

        return filtered_areas, attributes

    def layerpopulation(self):
        # delete old layer if present
        old_layer = uf.getLegendLayerByName(self.iface, '_critical_areas')
        if old_layer:
            QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())

            # create one if it doesn't exist and add suffix for the scenario
        Layer = uf.getLegendLayerByName(self.iface, 'initial_areas')
        critical_layer = uf.getLegendLayerByName(self.iface, '_critical_areas')
        if not critical_layer:
            timeslot_field = self.setTimeSlot()
            attribs = ['sid', 'inw2014', 'group_pop', 'popden10m2']
            types = [QtCore.QVariant.Int, QtCore.QVariant.Double, QtCore.QVariant.Double, QtCore.QVariant.Double]
            critical_layer = uf.createTempLayer( '_critical_areas', 'POLYGON',Layer.crs().postgisSrid(), attribs, types)
            critical_layer.setLayerName( '_critical_areas')
            uf.loadTempLayer(critical_layer)

            # insert pointsgeom & values
        tuple = self.filter_with_population()

        uf.insertTempFeatures(critical_layer, tuple[0], tuple[1])

        self.cliplayer()

        # create clip layer
    def cliplayer(self):
        overlay_layer = uf.getLegendLayerByName(self.iface,'Neighbourhoods population')
        to_clip= uf.getLegendLayerByName(self.iface, '_critical_areas')
        #calling clip function import processing need
        result = processing.runandload("qgis:clip", overlay_layer , to_clip ,None)

        clip_layer = uf.getLegendLayerByName(self.iface, "Clipped")

        prov= clip_layer.dataProvider()
        areas = [feat.geometry().area() for feat in clip_layer.getFeatures()]
        field = QgsField('iso_area', QtCore.QVariant.Double)
        prov.addAttributes([field])
        clip_layer.updateFields()

        idx = clip_layer.fieldNameIndex('iso_area')

        for area in areas:
            new_values = {idx: float(round(area,4))}
            prov.changeAttributeValues({areas.index(area): new_values})

    def max_popagegroup_initialcritical(self):
        max_pop_layer = uf.getLegendLayerByName(self.iface, "initial_areas")
        pop_list = []
        attrs = max_pop_layer.getFeatures()
        if max_pop_layer:
            for feature in attrs:
                pop_list.append(feature.attribute('group_pop'))
            pop_list.sort(reverse=True)
            result = []
            for i in pop_list:
                result.append(i)
            return result[0]

    def MaxThresholdCritical(self):
        pop_threshold = self.max_popagegroup_initialcritical()
        to_print = 'max(%s)' % (pop_threshold)
        self.label_22.setText(to_print)



        #report functions#
    def getsummary(self):
        self.textagegroup.clear()
        x=self.selectCensusCombo.currentText()
        self.textagegroup.insertItem(0, x)

        self.texttimeslot.clear()
        y=self.selecttimeCombo.currentText()
        self.texttimeslot.insertItem(0, y)

        self.textfreq.clear()
        i=self.sliderValue_2.text()
        self.textfreq.insertItem(0,i)

        self.textbufferdist.clear()
        z=self.sliderValue.text()
        self.textbufferdist.insertItem(0, z)

        self.popthreshold.clear()
        d=self.populationthreshold.text()
        self.popthreshold.insertItem(0, d)


    def extractAttributeSummary(self, attribute):
        # get summary of the attribute
        attribute='bu_naam'
        attribute2='iso_area'
        layer = uf.getLegendLayerByName(self.iface, "Clipped")
        summary = []
        # only use the first attribute in the list
        for feature in layer.getFeatures():
            summary.append(( feature.attribute(attribute), feature.attribute(attribute2)))
        # send this to the table
        self.clearTable()
        self.updateTable(summary)

    def clearTable(self):
        self.statisticsTable.clear()


    def updateTable(self, values):
        # takes a list of label / value pairs, can be tuples or lists. not dictionaries to control order
        self.statisticsTable.setColumnCount(2)
        self.statisticsTable.setHorizontalHeaderLabels(['Isolated Neighbourhood', 'Area m2'])
        self.statisticsTable.setRowCount(len(values))
        for i, item in enumerate(values):
            # i is the table row, items mus tbe added as QTableWidgetItems
            self.statisticsTable.setItem(i, 0, QtGui.QTableWidgetItem(str(item[0])))
            self.statisticsTable.setItem(i, 1, QtGui.QTableWidgetItem(str(item[1])))
        self.statisticsTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.statisticsTable.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.statisticsTable.resizeRowsToContents()

    def saveTable(self):
        path = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)')
        if path:
            with open(unicode(path), 'wb') as stream:
                # open csv file for writing
                writer = csv.writer(stream)
                # write header
                header = []
                for column in range(self.statisticsTable.columnCount()):
                    item = self.statisticsTable.horizontalHeaderItem(column)
                    header.append(unicode(item.text()).encode('utf8'))
                writer.writerow(header)
                # write data
                for row in range(self.statisticsTable.rowCount()):
                    rowdata = []
                    for column in range(self.statisticsTable.columnCount()):
                        item = self.statisticsTable.item(row, column)
                        if item is not None:
                            rowdata.append(
                                unicode(item.text()).encode('utf8'))
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)







