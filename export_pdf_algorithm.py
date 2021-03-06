# -*- coding: utf-8 -*-

"""
/***************************************************************************
 LociTools
                                 A QGIS plugin
 Various tools created by LociGeo.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-26
        copyright            : (C) 2019 by LociGeo
        email                : davidlgalt.gis@gmail.com
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

__author__ = 'LociGeo'
__date__ = '2019-08-26'
__copyright__ = '(C) 2019 by LociGeo'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterLayout,
                       QgsLayoutExporter,
                       QgsVectorLayer,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       #QgsProcessingParameterFileOutput,
                       #QgsProcessingParameterFolder,
                       QgsMessageLog,
                       QgsApplication,
                       QgsFeatureRequest,
                       Qgis,
                       QgsProject)
import processing, os


class ExportPdfAlgorithm(QgsProcessingAlgorithm):

    project = QgsProject.instance()
    projectLayoutManager = project.layoutManager()
    root = project.layerTreeRoot()
    layers = root.findLayers()

    log = {}
    all_spatial_layers = []
    all_vector_layers = []
    
    def initAlgorithm(self, config):
       
        try:
            self.addParameter(QgsProcessingParameterLayout('Layout', 'Print Layout Name', defaultValue=self.projectLayoutManager.layouts()[0].name()))
        except:
            self.addParameter(QgsProcessingParameterLayout('Layout', 'Print Layout Name', defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('OutputFilePath',self.tr('Output File'),'PDF File (*.pdf)'))
        #self.addParameter(QgsProcessingParameterFolder('OutputFolder','Output folder',defaultValue=''))
        #self.addParameter(QgsProcessingParameterString('FileName','Name of PDF file',defaultValue=''))
        self.addParameter(QgsProcessingParameterNumber('DPI','DPI',defaultValue=300))
        self.addParameter(QgsProcessingParameterBoolean('AlwaysVector','Always export as vectors', defaultValue=False)) 
        self.addParameter(QgsProcessingParameterBoolean('AppendGeorefInfo','Append georeference information', defaultValue=True)) 
        self.addParameter(QgsProcessingParameterBoolean('RdfMetadata','Export RDF metadata (title, author, etc.)', defaultValue=True)) 
        self.addParameter(QgsProcessingParameterEnum('TextRenderingFormat','Text Rendering Format', ['Always Export Text as Paths (Recommended)', 'Always Export Text as Text Objects'], allowMultiple=False, defaultValue='Always Export Text as Paths (Recommended)'))
        self.addParameter(QgsProcessingParameterBoolean('CreateGeoPdf', 'Create Geospatial PDF (GeoPDF)', defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean('Simplify','Simplify geometries to reduce output file size', defaultValue=True)) 
        self.addParameter(QgsProcessingParameterBoolean('DisableTiledRaster','Disable tiled raster data exports', defaultValue=False))

        sn=0
        vn=0
        lyr_list = []
        
        self.all_spatial_layers = []
        self.all_vector_layers = []
        for lyr in self.layers: 
            if lyr.layer().isSpatial() and self.root.findLayer(lyr.layer().id()).isVisible():
                self.all_spatial_layers.append(lyr.name())
                self.log[f'Spatial Layer: {lyr.name()}'] = sn
                sn+=1
                if  isinstance(lyr.layer(),QgsVectorLayer): #lyr.type() == QgsMapLayer.VectorLayer:
                    self.log[f'Vector Layer: {lyr.name()}'] = vn
                    self.all_vector_layers.append(lyr.name())
                    vn+=1
                #else:
                #    self.all_vector_layers.append(f'{lyr.type()}'')
                #    vn+=1

        self.addParameter(QgsProcessingParameterEnum('VisibleLayers','Initially visible layers', self.all_spatial_layers, allowMultiple=True, optional=True))
        self.addParameter(QgsProcessingParameterEnum('DataLayers','Include layer attributes in PDF', self.all_vector_layers, allowMultiple=True, optional=True))

        self.log['init'] = 'ended'
               

    def getLayers(self, layers):
        # Get's list of layers whose names match lyr_name_str
        # If lyr_names_str is none returns list of all visible layers
        lyr_list = []
        lyr_names = []
        for lyr in self.layers:
            if layers == [] and lyr.isVisible() and lyr.layer():
                lyr_list.append(lyr.layer())
            elif lyr.name() in  layers and lyr.layer():
                if lyr.name in lyr_names:
                    QgsMessageLog.logMessage(f'{lyr.name} name is duplicated. Both layers will be included.')
                else:
                    lyr_names.append(lyr)
                lyr_list.append(lyr.layer())

        return lyr_list


    def processAlgorithm(self, parameters, context, feedback):

        layout_name = parameters['Layout']

        project = QgsProject.instance()
        projectLayoutManager = project.layoutManager()
        layout = projectLayoutManager.layoutByName(layout_name)
        exporter = QgsLayoutExporter(layout)
        export_settings = exporter.PdfExportSettings()

        export_settings.forceVectorOutput = parameters['AlwaysVector']
        export_settings.exportMetadata = parameters['RdfMetadata']
        export_settings.textRenderFormat = parameters['TextRenderingFormat']
        export_settings.writeGeoPdf = parameters['CreateGeoPdf']
        if parameters['CreateGeoPdf']:
            export_settings.includeGeoPdfFeatures = True
        else:
            export_settings.includeGeoPdfFeatures = False
        export_settings.simplifyGeometries = parameters['Simplify']
        export_settings.appendGeoreference = parameters['AppendGeorefInfo']
        export_settings.rasterizeWholeImage = parameters['DisableTiledRaster']
        export_settings.DPI = parameters['DPI']
        visible_layers_numbers = parameters['VisibleLayers']
        data_layers_numbers = parameters['DataLayers']

        #output_folder = parameters['OutputFolder']
        output_file = parameters['OutputFilePath']

        visible_layers_list = []
        for n in visible_layers_numbers:
            visible_layers_list.append(self.all_spatial_layers[n])

        data_layers_list = []
        for n in data_layers_numbers:
            data_layers_list.append(self.all_vector_layers[n])


        for lyr in self.layers:
            if lyr.layer().isSpatial():
                if lyr.name() in visible_layers_list:
                    feedback.pushInfo(f'1a {lyr.name()}')
                    lyr.layer().setCustomProperty('geopdf/initiallyVisible', True)
                else:
                    feedback.pushInfo(f'1b {lyr.name()}') 
                    lyr.layer().setCustomProperty('geopdf/initiallyVisible', False)

                if isinstance(lyr.layer(),QgsVectorLayer):
                    if lyr.name() in data_layers_list:
                        lyr.layer().setCustomProperty('geopdf/includeFeatures', True)
                        feedback.pushInfo(f'2a {lyr.name()}')
                    else:
                        lyr.layer().setCustomProperty('geopdf/includeFeatures', False)
                        feedback.pushInfo(f'2b {lyr.name()}') 

       
        exporter.exportToPdf(output_file, export_settings)
     
        #map.refresh()

        for key in self.log:
            feedback.pushInfo(f'{key}: {self.log[key]}')
        return {}


    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it.
        """
        return self.tr(
            "This processing exports the specified layout as a pdf.")


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Export to PDF'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Layout Tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'layout'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportPdfAlgorithm()
