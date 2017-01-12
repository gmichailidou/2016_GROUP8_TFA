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
from qgis.core import *                   #error
from qgis.networkanalysis import *         #error
from qgis.gui import *                 #error
import processing                      #error

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
        #self.createScenarioButton.clicked.connect(self.createScenario)
        #self.scenarioCombo.currentIndexChanged.connect(self.scenarioChanged)
        self.scenarioPath = QgsProject.instance().homePath()
        self.scenarioCombo.clear()
        self.scenarioCombo.addItem('base')
        self.scenarioAttributes = {}
        self.subScenario = {}




        # indicators
        self.sliderValue_2.textChanged.connect(self.sliderTextChanged)

        self.selecttimeCombo.activated.connect(self.setTimeSlot)
        self.selecttimeCombo.activated.connect(self.selectfreq)
        self.horizontalSlider.sliderMoved.connect(self.sliderMoved)

        self.horizontalSlider.valueChanged.connect(self.sliderValueChanged)


        self.agegroupBox.activated.connect(self.setAgeGroup)

        # initialize
        #self.sliderInit()
        # analysis
        self.sliderValue.textChanged.connect(self.sliderTextChanged)
        self.stationDistanceSlider.sliderMoved.connect(self.sliderMoved)
        # self.stationDistanceSlider.valueChanged.connect(self.sliderValueChanged)
        #self.distanceVisiblecheckBox.stateChanged.connect(self.toggleBufferLayer)
        self.bufferbutton.clicked.connect(self.calculatebuffer)
        # self.initialareasVisiblecheckBox.connect()
        # self.criticalVisiblecheckBox.connect()
        self.screenshotButton.clicked.connect(self.savemap)
        # self.savesenariobuttom.connect()

        # report
        # self.statistics1table.connect()
        # self.statistics2table.connect()
        # self.saveStatisticsButtom.connect()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    # data functions
    def getScenarios(self):
        scenarios = [self.scenarioCombo.itemText(i) for i in range(self.scenarioCombo.count())]
        return scenarios

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
            # add scenario to current scenario combo and select it
            self.scenarioCombo.addItem(current_scenario)
            index = self.scenarioCombo.count() - 1
            self.scenarioCombo.setCurrentIndex(index)
            filename = current_scenario + '_nodes'
            pathStyle = "%s/Styles/" % QgsProject.instance().homePath()
            # save the layer as shapefile
            vlayer = uf.copyLayerToShapeFile(vl, path, filename)
            # add scenario to the project
            QgsMapLayerRegistry.instance().addMapLayer(vlayer, False)

            root = QgsProject.instance().layerTreeRoot()
            scenario_group = root.insertGroup(0, current_scenario)
            scenario_group.insertLayer(0, vlayer)
            root.findLayer(vlayer.id()).setExpanded(False)

            layer = uf.getLegendLayerByName(self.iface, filename)
            layer.loadNamedStyle("{}styleNodes.qml".format(pathStyle))
            layer.triggerRepaint()
            self.iface.legendInterface().refreshLayerSymbology(layer)


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

        # remove scenario if deleted
        scenarios = self.getScenarios()
        current_scenario = self.scenarioCombo.currentText()
        self.scenarioCombo.clear()
        index = 0
        for scenario in scenarios:
            root = QgsProject.instance().layerTreeRoot()
            scenario_group = root.findGroup(scenario)
            if scenario_group or scenario == 'base':
                self.scenarioCombo.addItem(scenario)
                if scenario == current_scenario:
                    self.scenarioCombo.setCurrentIndex(index)
                index = index + 1
            else:
                self.scenarioAttributes.pop(scenario, None)
                # send this to the table
                #self.clearTable()
                #self.updateTable1()
                #self.updateTable2()

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
        #self.baseAttributes()

        #initialize
        self.sliderInit()

    def baseAttributes(self):
        # get summary of the attribute
        layer = uf.getLegendLayerByName(self.iface, "Population")
        summary = []
        # only use the first attribute in the list
        for feature in layer.getFeatures():
            summary.append(feature)  # , feature.attribute(attribute)))
        self.scenarioAttributes["base"] = summary
        # send this to the table
        #self.clearTable()
        #self.updateTable1()
        #self.updateTable2()

    def getNodesLayer(self):
        layer_name = self.selectNodesCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    def getBaseNodeLayer(self):
        layer_name = self.selectNodeCombo.currentText()
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    def getCurrentNodeLayer(self):
        layer_name = self.scenarioCombo.currentText() + '_nodes'
        layer = uf.getLegendLayerByName(self.iface, layer_name)

        if layer == None:
            layer_name = 'Nodes'
            layer = uf.getLegendLayerByName(self.iface, layer_name)
        return layer

    #
    ####indicators functions
    #

    def selectfreq(self):
        sel_freq = self.run_mouse()

    def run_mouse(self):
        self.canvas.setMapTool(self.panTool)

    #6 fields from layer RT Network Nodes appear with full names and user can choose
    def setTimeSlot(self):
        value = self.sliderValue_2.text()
        if self.selecttimeCombo.currentText() == 'Select time-slot':
            self.horizontalSlider.setEnabled(False)
            self.sliderValue_2.setEnabled(False)
        else:
            self.horizontalSlider.setEnabled(True)
            self.sliderValue_2.setEnabled(True)


    #maximum threshold value
    def sliderInit(self):
        value = self.sliderValue_2.text()
        self.horizontalSlider.setValue(96)
        self.horizontalSlider.setValue(int(value))

    #check if threshold is empty
    def sliderTextChanged(self):

        try:
            self.horizontalSlider.setValue(int(value))
        except:
            print 'Fill in a number.'


    def sliderMoved(self, value):
        self.sliderValue_2.setText(str(value))

    #filters the network nodes and shows/keeps only those that have frequency lower or equal than the threshold according to the setTimeSlot(self)
    def sliderValueChanged(self):
        value = self.sliderValue_2.text()
        if self.setTimeSlot() == 'Weekdays - Afternoon Rush Hours' and value > 76:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Maximum frequency value for the selected timeslot is 76.\nChoose a lower (valid) threshold")
            msgBox.addButton(QtGui.QPushButton('Ok'), QtGui.QMessageBox.RejectRole)
            message = msgBox.exec_()
            if message == 0:
                return
        elif self.setTimeSlot() == 'Weekdays - Morning Rush Hours' and value > 96:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Maximum frequency value for the selected timeslot is 96.\nChoose a lower (valid) threshold")
            msgBox.addButton(QtGui.QPushButton('Ok'), QtGui.QMessageBox.RejectRole)
            message = msgBox.exec_()
            if message == 0:
                return
    def setAgeGroup(self):
        pass

        # analysis functions

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

        def sliderValueChanged(self):
            current_scenario = self.scenarioCombo.currentText()
            filename = current_scenario + '_dist2station'
            raster_layer = uf.getLegendLayerByName(self.iface, filename)
            if raster_layer:
                self.styleStationDistance(raster_layer)

        # buffer functions

        def toggleBufferLayer(self):
            cur_user = self.selectCensusCombo.currentText()
            layer = uf.getLegendLayerByName(self.iface, 'Buffers_{}'.format(cur_user))
            if not layer:
                self.bufferbutton.setChecked(False)
                return
            else:
                state = self.bufferbutton.checkState()

                if state == 0:
                    self.iface.legendInterface().setLayerVisible(layer, False)
                    self.refreshCanvas(layer)
                elif state == 2:
                    self.iface.legendInterface().setLayerVisible(layer, True)
                    self.refreshCanvas(layer)

        def calculateBuffer(self):
            layer = uf.getLegendLayerByName(self.iface, "PT Network Nodes")
            origins = layer.getFeatures()
            if origins > 0:
                cutoff_distance = uf.convertNumeric(self.sliderValue.text())
                buffers = {}
                for point in origins:
                    geom = point.geometry()
                    buffers[point.id()] = geom.buffer(cutoff_distance, 12).asPolygon()
                # store the buffer results in temporary layer called "Buffers"
                buffer_layer = uf.getLegendLayerByName(self.iface, "Buffers")
                # create one if it doesn't exist
                if not buffer_layer:
                    attribs = ['id', 'distance']
                    types = [QtCore.QVariant.String, QtCore.QVariant.Double]
                    buffer_layer = uf.createTempLayer('Buffers', 'POLYGON', layer.crs().postgisSrid(), attribs, types)
                    uf.loadTempLayer(buffer_layer)
                    buffer_layer.setLayerName('Buffers')
                # insert buffer polygons
                geoms = []
                values = []
                for buffer in buffers.iteritems():
                    # each buffer has an id and a geometry
                    geoms.append(buffer[1])
                    # in the case of values, it expects a list of multiple values in each item - list of lists
                    values.append([buffer[0], cutoff_distance])
                uf.insertTempFeatures(buffer_layer, geoms, values)
                self.refreshCanvas(buffer_layer)

        def getSelectedLayer(self):
            layer_name = self.selectCensusCombo.currentText()
            layer = uf.getLegendLayerByName(self.iface, layer_name)
            return layer

