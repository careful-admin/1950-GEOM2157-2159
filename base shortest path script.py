#import required libraries
import sys
import gdal_merge as gm
import processing

#define input and output filepaths
filepath = "C:\\Users\\zacst\\Desktop\\HELP\\progAss\\data\\"
output = filepath + "output3\\"

#I had quite a lot of issues using gdal merge raster layer processing
#I was only able to get it to work using this format

sys.path.append('C:\\OSGeo4W64\\bin')
gm.main(['', '-separate', '-o', output + 'merged5.tif', filepath + 'bbbbb1.tif', filepath + 'bbbbb2.tif', filepath + 'bbbbb3.tif'])

#define merged raster layer and training area data
#and yes, I know that the training area data name 
#is misspelt

raster = output + "merged5.tif"
training = filepath + 'training.shp'

#add merged raster layer to project 
addRaster = iface.addRasterLayer(raster, "raster")


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

#just a typo???
#would be really helpful if it was consistent with other processing algs with error messages

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


















