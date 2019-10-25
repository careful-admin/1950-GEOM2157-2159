# -*- coding: utf-8 -*-

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink)
import processing
import gdal_merge as gm
import os


class ShortestPathCalculator(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUTRASTER = 'OUTPUTRASTER'
    OUTPUTVECTOR = 'OUTPUTVECTOR'
    TRAINING = 'TRAINING'
    PREDICATE = 'PREDICATE'
    RASTER = 'RASTER'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ShortestPathCalculator()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'shortestpathcalculator'

    def displayName(self):
        """
        Calculates the shortest path reading from a raster file
        """
        return self.tr('Calculate shortest path between two points using road networks from a raster file')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.predicates = (
            ('Yes', self.tr('Yes')),
            ('No', self.tr('No'))
            )
            
        predicate = QgsProcessingParameterEnum(self.PREDICATE,
                                               self.tr('Do you require to merge multiple raster files?'),
                                               options=[p[1] for p in self.predicates],
                                               allowMultiple=False, 
                                               defaultValue=[0])

        predicate.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers.EnumWidgetWrapper',
                'useCheckBoxes': True,
                'columns': 2}})
                
        self.addParameter(predicate)
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.RASTER,
                self.tr('Input raster file'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TRAINING,
                self.tr('Input training vector layer'),
                [QgsProcessing.TypeVector],
                optional = True
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTRASTER,
                self.tr('Output Raster')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTVECTOR,
                self.tr('Output Shortest Path')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        """
        Here is where the processing itself takes place.
        """


        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.RASTER,
            context
        )
        
        source2 = self.parameterAsSource(
            parameters,
            self.TRAINING,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        #if source is None:
        #    raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUTRASTER,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUTVECTOR,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated

        chosenFile = self.parameterDefinition('RASTER').valueAsPythonString(parameters['RASTER'], context)
        filepath = os.path.dirname(chosenFile[1:]) + '/'
        
        options = [self.predicates[i][0] for i in
                        self.parameterAsEnums(parameters, self.PREDICATE, context)]
        
        if 'Yes' in options:
            
            sys.path.append('C:\\OSGeo4W64\\bin')
            
            output = filepath + 'newoutput\\'
            
            layers = ['', '-separate', '-o', output + 'merged5.tif']
            feedback.pushInfo(filepath)
            
            for file in os.listdir(filepath):
                next = filepath + file
                layers.append(next)
            
            gm.main(layers)
        
        elif 'No' in options:
            
            output = filepath + 'newoutput\\'
            
            raster = self.parameterDefinition('RASTER').valueAsPythonString(parameters['RASTER'], context)
            training = self.parameterDefinition('TRAINING').valueAsPythonString(parameters['TRAINING'], context)
            
            feedback.pushInfo(raster)
            feedback.pushInfo(training)
            
            iface.addRasterLayer(raster, "raster")
            
            #define parameters required for merged raster statistics
            parametersDict = {"il": raster,
                            "out": (output + "merged5Stats.xml")}

            #execute raster statistics
            processing.run("otb:ComputeImagesStatistics", parametersDict)

            #store merged raster statistics file as variable
            stats = output + "merged5Stats.xml"

            #define parameters required for classifier training
            parametersDict = {"io.il": raster,
                            "io.vd": training,
                            "io.imstat": (output + "merged5stats.xml"),
                            "io.out": (output + "merged5.model"),
                            "io.confmatout": (output + "merged5Conf.csv"),
                            "cleanup": True,
                            "sample.vfn": 'id',
                            "classifier": 'libsvm',
                            "classifier.libsvm.k": 'rbf', 
                            "classifier.libsvm.m": 'oneclass'} 
                            #"classifier.libsvm.c": 1, 
                            #"classifier.libsvm.nu": 0.5, 
                            #"classifier.libsvm.opt": False, 
                            #"classifier.libsvm.prob": False, 
                            #"rand": 0}

            #execute raster classifier
            processing.run("otb:TrainImagesClassifier", parametersDict)

            #store raster classifier model file as variable
            model = output + "merged5.model"

            #define parameters required for raster classification

            #just a typo for dictionary key???
            #would be really helpful if it was consistent with other processing 
            #algs with error messages rather than just saying 'error encountered'

            parametersDict = {"in": raster,
                            'mask' : None,
                            "model": model,
                            "imstat": stats,
                            'nodatalabel' : 0, 
                            "out": (output + 'classification.tif'),
                            "confmap": (output + 'confmap.tif'),
                            "outputpixeltype": 5}

            #execute raster classification
            processing.run("otb:ImageClassifier", parametersDict)

            #store raster classification as variable
            classification = output + "classification.tif"

            #define parameters required for Binary Morphological Operation (dilate)
            parametersDict = {"in": classification,
                            "out": (output + "classificationMorphDilate10.tif"),
                            "structype": 'ball',
                            "structype.ball.xradius": 10,
                            "structype.ball.yradius": 10,
                            "filter": 'dilate',
                            "filter.dilate.backval": 0,
                            "filter.dilate.foreval": 1,
                            "outputpixeltype": 5}

            #execute Binary Morphological Operation
            processing.run("otb:BinaryMorphologicalOperation", parametersDict)

            #store binary Morphological Operation as variable
            binaryDilate = output + "classificationMorphDilate10.tif"

            #define parameters for Binary Morphological Operation (opening)
            parametersDict = {"in": binaryDilate,
                            "out": (output + "binaryDilateOpening10.tif"),
                            "structype": 'ball',
                            "structype.ball.xradius": 10,
                            "structype.ball.yradius": 10,
                            "filter": 'opening',
                            "filter.dilate.backval": 0,
                            "filter.dilate.foreval": 1,
                            "outputpixeltype": 5}

            #execute Binary Morphological Operation
            processing.run("otb:BinaryMorphologicalOperation", parametersDict)

            #store binary Morphological Operation as variable
            binaryDilateOpening = output + "binaryDilateOpening10.tif"

            #define parameters for Sieve filter
            parametersDict = {"INPUT": binaryDilateOpening,
                            "THRESHOLD": 10000,
                            "EIGHT_CONNECTEDNESS": True,
                            "NO_MASK": False,
                            "OUTPUT": (output + "sieved10000.tif")}

            #execute Sieve
            processing.run("gdal:sieve", parametersDict)

            #store Sieve as variable
            sieved = output + "sieved10000.tif"

            #define parameters for Binary Morphological Operation (dilate)
            #the output from this operation will be used to store raster values
            #for points that we will created later

            parametersDict = {"in": sieved,
                            "out": (output + "sieved10000P.tif"),
                            "structype": 'ball',
                            "structype.ball.xradius": 5,
                            "structype.ball.yradius": 5,
                            "filter": 'dilate',
                            "filter.dilate.backval": 0,
                            "filter.dilate.foreval": 1,
                            "outputpixeltype": 5}

            #execute Binary Morphological Operation
            processing.run("otb:BinaryMorphologicalOperation", parametersDict)

            #store Binary Morphological Operation as variable
            sieved10000P = output + "sieved10000P.tif"

            #define parameters for polygonize
            parametersDict = {"INPUT": sieved,
                            "BAND": 1,
                            "FIELD": 'polygon',
                            "EIGHT_CONNECTEDNESS": True,
                            "OUTPUT": (output + "polygons.shp")}

            #execute polygonize
            processing.run("gdal:polygonize", parametersDict)

            #store polygonize as variable
            polygons = output + "polygons.shp"

            #define parameters for polygon to lines conversion
            parametersDict = {"POLYGONS": polygons,
                            "LINES": (output + "lines.shp")}

            #execute polygon to lines
            processing.run("saga:convertpolygonstolines", parametersDict)

            #store lines as variable
            lines = output + "lines.shp"

            #define parameters for points along lines
            parametersDict = {"INPUT": lines,
                            "DISTANCE": 100,
                            "START_OFFSET": 0,
                            "END_OFFSET": 0,
                            "OUTPUT": (output + 'points.shp')}

            #execute points along lines
            processing.run("qgis:pointsalonglines", parametersDict)

            #store points as variable
            points = output + "points.shp"

            #define parameters for add raster values to points
            parametersDict = {"SHAPES": points,
                            "GRIDS": sieved10000P,
                            "RESAMPLING": 0,
                            "RESULT": (output + "pointsWithValues.shp")}

            #execute add raster values to points
            processing.run("saga:addrastervaluestopoints", parametersDict)

            #store updated points as variable
            pointsWithValues = output + "pointsWithValues.shp"

            #define parameters for vector edit (points)
            #this process will be deleting any points which 
            #dont overlap with our road network raster (sieved10000)
            parametersDict = {"map": pointsWithValues,
                            "type": 0,
                            "tool": 2,
                            "where": 'sieved10000P != 1',
                            "output": (output + "editedPointsWithValues.shp")}

            #execute vector edit
            processing.run("grass7:v.edit", parametersDict)

            #store vector edit output as variable
            editedPointsWithValues = output + "editedPointsWithValues.shp"

            #define parameters for voronoi polygon creation
            parametersDict = {"input": editedPointsWithValues,
                            "GRASS_OUTPUT_TYPE_PARAMETER": 0,
                            "output": (output + "voronoi.shp")}

            #execute voronoi polygon
            processing.run("grass7:v.voronoi", parametersDict)

            #store voronoi polygon as variable
            voronoi = output + "voronoi.shp"

            #define parameters for polygon to lines conversion
            parametersDict = {"POLYGONS": voronoi,
                            "LINES": (output + "voronoiLines.shp")}

            #convert polygon to lines conversion
            processing.run("saga:convertpolygonstolines", parametersDict)

            #store lines as variable
            voronoiLines = output + "voronoiLines.shp"

            #define parameters for add raster values to features
            parametersDict = {"SHAPES": voronoiLines,
                            "GRIDS": sieved,
                            "RESAMPLING": 0,
                            "RESULT": (output + "linesWithValues.shp")}

            #execute add raster values to features
            processing.run("saga:addrastervaluestofeatures", parametersDict)

            #store raster values to features as variable
            linesWithValues = output + "linesWithValues.shp"

            #define parameters for vector edit process
            parametersDict = {"map": linesWithValues,
                            "type": 1,
                            "tool": 2,
                            "where": 'sieved10000 < 0.2',
                            "output": (output + "network.shp")}

            #execute vector edit
            processing.run("grass7:v.edit", parametersDict)

            #store edited vector as variable
            network = output + "network.shp"

            #define parameters for shortest path calculation
            #if you want to repeat this calculation, be sure to either move or 
            #delete the output file, as the process will encounter an error
            #(for some reason can find directory if file already exists for
            #output?
            parametersDict = {"INPUT": network,
                            "STRATEGY": 0,
                            "START_POINT": '779447, 524079',
                            "END_POINT": '776142, 531919',
                            "OUTPUT": (output + "shortestPath.shp")}

            #execute shortest path calculation
            processing.run("native:shortestpathpointtopoint", parametersDict)

            #store shortest path as variable
            shortestPath = output + "shortestPath.shp"

            #add shortest path to project 
            final =  iface.addVectorLayer(shortestPath, "vector", 'ogr')
            
        
        return {self.OUTPUTRASTER: dest_id}
        return {self.OUTPUTVECTOR: dest_id}
