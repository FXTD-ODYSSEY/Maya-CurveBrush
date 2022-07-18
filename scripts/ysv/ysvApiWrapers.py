import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaUI as omui

import math
import sys

apiTypes = [(k, om.MFn.__dict__[k]) for k in om.MFn.__dict__ if k.startswith('k')]

def type2Str(intType):
    for name, id in apiTypes:
        if id == intType: return name
        
def getCompElems(mfn):
    elems = om.MIntArray()
    mfn.getElements(elems)
    return list(elems)

class dataTypes():
    '''
    types = []
    for kType in om.MFnData.__dict__:
        if not kType.startswith('_'):
            if kType.startswith('k'):
                kTypeName = 'k'+kType[1:]
                types.append( (kTypeName, ' = om.MFnData.{0}'.format(kType)) )
    types = sorted(types, key = lambda x:x[0])
    
    for k, v in types:
        print k, v
    
    '''
    kAny = om.MFnData.kAny
    kComponentList = om.MFnData.kComponentList
    kDoubleArray = om.MFnData.kDoubleArray
    kDynArrayAttrs = om.MFnData.kDynArrayAttrs
    kDynSweptGeometry = om.MFnData.kDynSweptGeometry
    kFloatArray = om.MFnData.kFloatArray
    kIntArray = om.MFnData.kIntArray
    kInvalid = om.MFnData.kInvalid
    kLast = om.MFnData.kLast
    kLattice = om.MFnData.kLattice
    kMatrix = om.MFnData.kMatrix
    kMesh = om.MFnData.kMesh
    kNId = om.MFnData.kNId
    kNObject = om.MFnData.kNObject
    kNumeric = om.MFnData.kNumeric
    kNurbsCurve = om.MFnData.kNurbsCurve
    kNurbsSurface = om.MFnData.kNurbsSurface
    kPlugin = om.MFnData.kPlugin
    kPluginGeometry = om.MFnData.kPluginGeometry
    kPointArray = om.MFnData.kPointArray
    kSphere = om.MFnData.kSphere
    kString = om.MFnData.kString
    kStringArray = om.MFnData.kStringArray
    kSubdSurface = om.MFnData.kSubdSurface
    kVectorArray = om.MFnData.kVectorArray
    
    n2Double = om.MFnNumericData.k2Double
    n2Float = om.MFnNumericData.k2Float
    n2Int = om.MFnNumericData.k2Int
    n2Long = om.MFnNumericData.k2Long
    n2Short = om.MFnNumericData.k2Short
    n3Double = om.MFnNumericData.k3Double
    n3Float = om.MFnNumericData.k3Float
    n3Int = om.MFnNumericData.k3Int
    n3Long = om.MFnNumericData.k3Long
    n3Short = om.MFnNumericData.k3Short
    n4Double = om.MFnNumericData.k4Double
    nAddr = om.MFnNumericData.kAddr
    nBoolean = om.MFnNumericData.kBoolean
    nByte = om.MFnNumericData.kByte
    nChar = om.MFnNumericData.kChar
    nDouble = om.MFnNumericData.kDouble
    nFloat = om.MFnNumericData.kFloat
    nInt = om.MFnNumericData.kInt
    nInvalid = om.MFnNumericData.kInvalid
    nLast = om.MFnNumericData.kLast
    nLong = om.MFnNumericData.kLong
    nShort = om.MFnNumericData.kShort
    
    uAngle = om.MFnUnitAttribute.kAngle
    uDistance = om.MFnUnitAttribute.kDistance
    uInvalid = om.MFnUnitAttribute.kInvalid
    uLast = om.MFnUnitAttribute.kLast
    uTime = om.MFnUnitAttribute.kTime
    
class mfn():
    '''
    i = 1
    for k, v in om.__dict__.iteritems():
        if k.startswith('MFn') and not '_' in k and not'Data' in k:
            #print i, '\t\t', k, '\t\t\t',  v
            print k[3:], ' = om.' + k
    '''
    Assembly = om.MFnAssembly
    SpotLight = om.MFnSpotLight
    BlinnShader = om.MFnBlinnShader
    NumericAttribute = om.MFnNumericAttribute
    AreaLight = om.MFnAreaLight
    PhongEShader = om.MFnPhongEShader
    NurbsCurve = om.MFnNurbsCurve
    MatrixAttribute = om.MFnMatrixAttribute
    ContainerNode = om.MFnContainerNode
    CameraSet = om.MFnCameraSet
    Component = om.MFnComponent
    SubdNames = om.MFnSubdNames
    DirectionalLight = om.MFnDirectionalLight
    Light = om.MFnLight
    NonExtendedLight = om.MFnNonExtendedLight
    Expression = om.MFnExpression
    Mesh = om.MFnMesh
    Attribute = om.MFnAttribute
    Uint64SingleIndexedComponent = om.MFnUint64SingleIndexedComponent
    LambertShader = om.MFnLambertShader
    GenericAttribute = om.MFnGenericAttribute
    Camera = om.MFnCamera
    Base = om.MFnBase
    SingleIndexedComponent = om.MFnSingleIndexedComponent
    VolumeLight = om.MFnVolumeLight
    Reference = om.MFnReference
    CompoundAttribute = om.MFnCompoundAttribute
    MFn = om.MFn
    AnisotropyShader = om.MFnAnisotropyShader
    NurbsSurface = om.MFnNurbsSurface
    PhongShader = om.MFnPhongShader
    Subd = om.MFnSubd
    NonAmbientLight = om.MFnNonAmbientLight
    Set = om.MFnSet
    LayeredShader = om.MFnLayeredShader
    Transform = om.MFnTransform
    EnumAttribute = om.MFnEnumAttribute
    TripleIndexedComponent = om.MFnTripleIndexedComponent
    ReflectShader = om.MFnReflectShader
    AmbientLight = om.MFnAmbientLight
    TypedAttribute = om.MFnTypedAttribute
    MessageAttribute = om.MFnMessageAttribute
    UnitAttribute = om.MFnUnitAttribute
    DagNode = om.MFnDagNode
    DoubleIndexedComponent = om.MFnDoubleIndexedComponent
    PointLight = om.MFnPointLight
    DependencyNode = om.MFnDependencyNode
    Partition = om.MFnPartition

class mfnd():
    LightDataAttribute = om.MFnLightDataAttribute
    GeometryData = om.MFnGeometryData
    PluginData = om.MFnPluginData
    MeshData = om.MFnMeshData
    NurbsCurveData = om.MFnNurbsCurveData
    PointArrayData = om.MFnPointArrayData
    NurbsSurfaceData = om.MFnNurbsSurfaceData
    UInt64ArrayData = om.MFnUInt64ArrayData
    FloatArrayData = om.MFnFloatArrayData
    SphereData = om.MFnSphereData
    StringData = om.MFnStringData
    IntArrayData = om.MFnIntArrayData
    NumericData = om.MFnNumericData
    LatticeData = om.MFnLatticeData
    Data = om.MFnData
    StringArrayData = om.MFnStringArrayData
    DoubleArrayData = om.MFnDoubleArrayData
    MatrixData = om.MFnMatrixData
    ComponentListData = om.MFnComponentListData
    VectorArrayData = om.MFnVectorArrayData
    ArrayAttrsData = om.MFnArrayAttrsData
    SubdData = om.MFnSubdData

class simpleTypes():
    MAngle = om.MAngle
    MBoundingBox = om.MBoundingBox
    MColor = om.MColor
    MColorArray = om.MColorArray
    MDistance = om.MDistance
    MDoubleArray = om.MDoubleArray
    MFloatArray = om.MFloatArray
    MFloatMatrix = om.MFloatMatrix
    MFloatPoint = om.MFloatPoint
    MFloatPointArray = om.MFloatPointArray
    MFloatVector = om.MFloatVector
    MFloatVectorArray = om.MFloatVectorArray
    MPoint = om.MPoint
    MPointArray = om.MPointArray
    MPointOnMesh = om.MPointOnMesh
    MPointOnNurbs = om.MPointOnNurbs
    MMatrix = om.MMatrix
    MMatrixArray = om.MMatrixArray
    MQuaternion = om.MQuaternion
    MUint64Array = om.MUint64Array
    MUintArray = om.MUintArray
    MVector = om.MVector
    MVectorArray = om.MVectorArray
    MWeight = om.MWeight

class commonTypes():
    
    pass
    
class unsorted():
    MAddRemoveAttrEdit = om.MAddRemoveAttrEdit
    MArgDatabase = om.MArgDatabase
    MArgList = om.MArgList
    MArgParser = om.MArgParser
    MArrayDataBuilder = om.MArrayDataBuilder
    MArrayDataHandle = om.MArrayDataHandle
    MAttributeIndex = om.MAttributeIndex
    MAttributePattern = om.MAttributePattern
    MAttributePatternArray = om.MAttributePatternArray
    MAttributeSpec = om.MAttributeSpec
    MAttributeSpecArray = om.MAttributeSpecArray
    MCacheFormatDescription = om.MCacheFormatDescription
    MCallbackIdArray = om.MCallbackIdArray
    MCameraSetMessage = om.MCameraSetMessage
    MCommandMessage = om.MCommandMessage
    MCommandResult = om.MCommandResult
    MComputation = om.MComputation
    MConditionMessage = om.MConditionMessage
    MConnectDisconnectAttrEdit = om.MConnectDisconnectAttrEdit
    MContainerMessage = om.MContainerMessage
    MDAGDrawOverrideInfo = om.MDAGDrawOverrideInfo
    MDGContext = om.MDGContext
    MDGMessage = om.MDGMessage
    MDGModifier = om.MDGModifier
    MDagMessage = om.MDagMessage
    MDagModifier = om.MDagModifier
    MDagPath = om.MDagPath
    MDagPathArray = om.MDagPathArray
    MDataBlock = om.MDataBlock
    MDataHandle = om.MDataHandle
    MEdit = om.MEdit
    MEulerRotation = om.MEulerRotation
    MEventMessage = om.MEventMessage
    MFcurveEdit = om.MFcurveEdit
    MFileIO = om.MFileIO
    MFileObject = om.MFileObject
    MGlobal = om.MGlobal
    MIffFile = om.MIffFile
    MIffTag = om.MIffTag
    MImage = om.MImage
    MImageFileInfo = om.MImageFileInfo
    MIntArray = om.MIntArray
    MItCurveCV = om.MItCurveCV
    MItDag = om.MItDag
    MItDependencyGraph = om.MItDependencyGraph
    MItDependencyNodes = om.MItDependencyNodes
    MItEdits = om.MItEdits
    MItGeometry = om.MItGeometry
    MItInstancer = om.MItInstancer
    MItMeshEdge = om.MItMeshEdge
    MItMeshFaceVertex = om.MItMeshFaceVertex
    MItMeshPolygon = om.MItMeshPolygon
    MItMeshVertex = om.MItMeshVertex
    MItSelectionList = om.MItSelectionList
    MItSubdEdge = om.MItSubdEdge
    MItSubdFace = om.MItSubdFace
    MItSubdVertex = om.MItSubdVertex
    MItSurfaceCV = om.MItSurfaceCV
    MIteratorType = om.MIteratorType
    MLockMessage = om.MLockMessage
    
    MMeshIntersector = om.MMeshIntersector
    MMeshIsectAccelParams = om.MMeshIsectAccelParams
    MMeshSmoothOptions = om.MMeshSmoothOptions
    MMessage = om.MMessage
    MMessageNode = om.MMessageNode
    MModelMessage = om.MModelMessage
    MNamespace = om.MNamespace
    MNodeClass = om.MNodeClass
    MNodeMessage = om.MNodeMessage
    MNurbsIntersector = om.MNurbsIntersector
    MObject = om.MObject
    MObjectArray = om.MObjectArray
    MObjectHandle = om.MObjectHandle
    MObjectSetMessage = om.MObjectSetMessage
    MParentingEdit = om.MParentingEdit
    MPlane = om.MPlane
    MPlug = om.MPlug
    MPlugArray = om.MPlugArray
    
    MPolyMessage = om.MPolyMessage
    # MProfiler  = om.MProfiler
    # MProfilingScope  = om.MProfilingScope
    
    MRampAttribute = om.MRampAttribute
    MRenderPassDef = om.MRenderPassDef
    MRenderPassRegistry = om.MRenderPassRegistry
    MRichSelection = om.MRichSelection
    MSceneMessage = om.MSceneMessage
    MScriptUtil = om.MScriptUtil
    MSelectionList = om.MSelectionList
    MSelectionMask = om.MSelectionMask
    MSetAttrEdit = om.MSetAttrEdit
    MSpace = om.MSpace
    MStreamUtils = om.MStreamUtils
    MSyntax = om.MSyntax
    MTesselationParams = om.MTesselationParams
    MTime = om.MTime
    MTimeArray = om.MTimeArray
    MTimer = om.MTimer
    MTimerMessage = om.MTimerMessage
    MTransformationMatrix = om.MTransformationMatrix
    MTrimBoundaryArray = om.MTrimBoundaryArray
    MTypeId = om.MTypeId
    MURI = om.MURI
    
    MUserData = om.MUserData
    MUserEventMessage = om.MUserEventMessage
    
    NULL = om.NULL
    array2dDouble = om.array2dDouble
    array2dFloat = om.array2dFloat
    array3dDouble = om.array3dDouble
    array3dFloat = om.array3dFloat
    array3dInt = om.array3dInt
    array4dDouble = om.array4dDouble
    array4dFloat = om.array4dFloat
    array4dInt = om.array4dInt
    boolPtr = om.boolPtr
    boolRefValue = om.boolRefValue
    charPtr = om.charPtr
    charRefValue = om.charRefValue
    createBoolRef = om.createBoolRef
    createCharRef = om.createCharRef
    createDoubleRef = om.createDoubleRef
    createFloatRef = om.createFloatRef
    createIntRef = om.createIntRef
    createShortRef = om.createShortRef
    createUCharRef = om.createUCharRef
    createUIntRef = om.createUIntRef
    cvar = om.cvar
    doublePtr = om.doublePtr
    doubleRefValue = om.doubleRefValue
    floatPtr = om.floatPtr
    floatRefValue = om.floatRefValue
    intPtr = om.intPtr
    intRefValue = om.intRefValue
    kDefaultNodeType = om.kDefaultNodeType
    kEulerRotationEpsilon = om.kEulerRotationEpsilon
    kMFnMeshInstanceUnspecified = om.kMFnMeshInstanceUnspecified
    kMFnMeshPointTolerance = om.kMFnMeshPointTolerance
    kMFnMeshTolerance = om.kMFnMeshTolerance
    kMFnNurbsEpsilon = om.kMFnNurbsEpsilon
    kMFnSubdPointTolerance = om.kMFnSubdPointTolerance
    kMFnSubdTolerance = om.kMFnSubdTolerance
    kQuaternionEpsilon = om.kQuaternionEpsilon
    kUnknownParameter = om.kUnknownParameter
    setRefValue = om.setRefValue
    shortPtr = om.shortPtr
    shortRefValue = om.shortRefValue
    uCharPtr = om.uCharPtr
    uCharRefValue = om.uCharRefValue
    uIntPtr = om.uIntPtr
    uIntRefValue = om.uIntRefValue
    weakref = om.weakref

def mIter(MArray):
    lng = MArray.length()
    
    for i in range(lng):
        yield MArray[i]

def mIterRv(MArray):
    lng = MArray.length()
    
    for i in range(lng - 1, -1, -1):
        yield MArray[i]

def createNumAt(name, bName, atType, mn=None, df=None, mx=None, smn=None, smx=None):
    unitTypes = [om.MFnUnitAttribute.kAngle, om.MFnUnitAttribute.kDistance, om.MFnUnitAttribute.kTime]
    if atType in unitTypes:
        fn = om.MFnUnitAttribute()
    else:
        fn = om.MFnNumericAttribute()
    at = fn.create(name, bName, atType)
    if mn: fn.setMin(mn)
    if df: fn.setDefault(df)
    if mx: fn.setMax(mx)
    if smn: fn.setSoftMin(smn)
    if smx: fn.setSoftMax(smx)
    return at, fn

def meshClosestPoint(inPnt, intersector):
    '''
    inPnt type: MPoint, MFloatPoint, MVector, MFloatVector, float[4]
    return types: MPoint, MVector, int (point, normal, faceId
    
    inersector creation:
        intersector = om.MMeshIntersector()
        intersector.create(meshMO)
    '''
    
    meshPnt = om.MPointOnMesh()
    
    if not type(inPnt) == om.MPoint:
        inPnt = om.MPoint(inPnt)
    intersector.getClosestPoint(inPnt, meshPnt)
    
    outPnt = om.MPoint(meshPnt.getPoint())
    outNorm = om.MVector(meshPnt.getNormal())
    faceId = meshPnt.faceIndex()
    
    return outPnt, outNorm, faceId

def createCurve(pnts, outCurveMO):
    curveFn = om.MFnNurbsCurve()
    
    try:
        curveFn.createWithEditPoints(pnts,
                        3,
                        om.MFnNurbsCurve.kOpen,
                        0, 0, 0,
                        outCurveMO)
         
        # print 'curve created'
    except:
        print 'ERROR IN: createCurve\n, \t\t{0}'.format('invalid curve')
        pass

def getCurvePntsFromCVs(curveFn):
    crvPntsData = []
    
    pnts = om.MPointArray()
    curveFn.getCVs(pnts, om.MSpace.kWorld)
    
    for i in range(pnts.length()):
        pnt = pnts[i]
        
        util = om.MScriptUtil()
        util.createFromDouble(0.0)
        dPtr = util.asDoublePtr()
        
        curveFn.closestPoint(pnts[i], dPtr, 0.1, om.MSpace.kWorld)
        param = om.MScriptUtil(dPtr).asDouble()
        # print 'param for point{0} :{1}'.format(i, param)
        
        crvTangent = curveFn.tangent(param, om.MSpace.kWorld)
        
        crvPnt = om.MPoint()
        curveFn.getPointAtParam(param, crvPnt, om.MSpace.kWorld)
        
        crvPntsData.append((crvPnt, crvTangent))
    
    return crvPntsData
    
def getCurveEvenPoints(curveFn, step, offset=0):
    crvPntsData = []

    crvLng = curveFn.length() - 2 * offset
    samples = int(crvLng / step)

    if samples < 2: samples = 2
    step = crvLng / (samples - 1)
    
    for i in range(samples):
        par = curveFn.findParamFromLength(offset + i * step)
        
        crvPnt = om.MPoint()
        curveFn.getPointAtParam(par, crvPnt, om.MSpace.kWorld)
        
        crvTangent = curveFn.tangent(par, om.MSpace.kWorld)
        
        crvPntsData.append((crvPnt, crvTangent))
        
    return crvPntsData

def getCurveRangeEvenPoints(curveFn, sPar, ePar, samples, reverse):
    pnts = []

    crvLng = curveFn.length()
    minPar, maxPar = getCurveRange(curveFn)
    
    crvParLng = maxPar - minPar
    rangeParLng = ePar - sPar
    
    rangeLng = crvLng * rangeParLng / crvParLng
    
    startLngOffset = crvLng * (sPar - minPar) / crvParLng
    
    step = rangeLng / (samples - 1)
    
    for i in range(samples):
        par = curveFn.findParamFromLength(startLngOffset + i * step)
        
        crvPnt = om.MPoint()
        curveFn.getPointAtParam(par, crvPnt, om.MSpace.kWorld)
        
        #crvTangent = curveFn.tangent(par, om.MSpace.kWorld)
        
        pnts.append(crvPnt)
    if  reverse:
        pnts.reverse()    
    return pnts

def getCurveSamplePoints(curveFn, samples=None):
    crvPnts = []
    
    
    if not samples:
        numCVs = curveFn.numCVs()
        for i in range(numCVs):
            crvPnt = om.MPoint()
            curveFn.getCV(i, crvPnt, om.MSpace.kWorld)
            crvPnts.append(crvPnt)
            
    else:
        crvLng = curveFn.length()
        
        if samples < 2: samples = 2
        step = crvLng / (samples - 1)
        
        for i in range(samples):
            par = curveFn.findParamFromLength(i * step)
            
            crvPnt = om.MPoint()
            curveFn.getPointAtParam(par, crvPnt, om.MSpace.kWorld)
            
            crvPnts.append(crvPnt)
        
    return crvPnts

def getCurveRange(curveFn):
    lng = curveFn.length()
    minPar = curveFn.findParamFromLength(0)
    maxPar = curveFn.findParamFromLength(lng)
    return minPar, maxPar

def getCurveEnds(curveFn):
    lng = curveFn.length()
    
    minPar = curveFn.findParamFromLength(0)
    maxPar = curveFn.findParamFromLength(lng)
    
    sPnt, ePnt = om.MPoint(), om.MPoint()
    curveFn.getPointAtParam(minPar, sPnt, om.MSpace.kWorld)
    curveFn.getPointAtParam(maxPar, ePnt, om.MSpace.kWorld)
    
    return sPnt, ePnt

def closestMeshPoint(inPnt, intersector):
    meshPnt = om.MPointOnMesh()
    
    if not type(inPnt) == om.MPoint:
        inPnt = om.MPoint(inPnt)
    intersector.getClosestPoint(inPnt, meshPnt)
    
    return om.MPoint(meshPnt.getPoint()), meshPnt.faceIndex()

def closestMeshPntNorm(inPnt, intersector):
    meshPnt = om.MPointOnMesh()
    
    if not type(inPnt) == om.MPoint:
        inPnt = om.MPoint(inPnt)
    intersector.getClosestPoint(inPnt, meshPnt)
    
    outPnt = om.MPoint(meshPnt.getPoint())
    outNorm = om.MVector(meshPnt.getNormal())
    faceId = meshPnt.faceIndex()
    
    return outPnt, outNorm, faceId

def mergeArrays(arrays):
    arLen = 0
    for i in range(len(arrays)):
        arLen += arrays[i].length()
    
    t = type(arrays[0])
    resultAr = t(arLen)
    
    currLen = 0
    for i in range(len(arrays)): 
        for j in range(arrays[i].length()):
            ar = arrays[i]
            pos = currLen + j
            resultAr.set(ar[j], pos)
        currLen += arrays[i].length()
        
    return resultAr

def mergeConnects(connectsArrays, vertexArrays):
    arLen = 0
    for connects in connectsArrays:
        arLen += connects.length()
    
    resultAr = om.MIntArray(arLen)
    
    currLen = 0
    vertIdOffset = 0  
    for i in range(len(connectsArrays)):
        for j in range(connectsArrays[i].length()):
            ar = connectsArrays[i]
            pos = currLen + j
            vertId = ar[j] + vertIdOffset
            
            resultAr.set(vertId, pos)
        
        currLen += connectsArrays[i].length()
        vertIdOffset += vertexArrays[i].length()
        
    return resultAr

def mergeMeshDatas(meshDatas):
    numVertsT, numFacesT = 0, 0
    vertexArrays, countsArrays, connectsArrays = [], [], []
    
    for meshData in meshDatas:
        numVerts, numFaces, vertexArray, polygonCounts, polygonConnects = meshData
        
        numVertsT += numVerts
        numFacesT += numFaces
        vertexArrays.append(vertexArray)
        countsArrays.append(polygonCounts)
        connectsArrays.append(polygonConnects)
        
    vertArray = mergeArrays(vertexArrays)
    counts = mergeArrays(countsArrays)
    connects = mergeConnects(connectsArrays, vertexArrays)
    
    # if skipCount > 0:
        # print '{0} meshDatas skipped'.format(skipCount)
        
    return numVertsT, numFacesT, vertArray, counts, connects

def stripPnts2MeshData(pnts):
    pnts0, pnts1, pnts2 = pnts
    vNum = pnts0.length() + pnts1.length() + pnts2.length()
    fNum = (pnts0.length() - 1) * 2
    
    vAr = om.MPointArray(vNum)
    counts = om.MIntArray(fNum, 4)
    connects = om.MIntArray(fNum * 4)
    
    for i in range(pnts0.length() - 1):
        vi, fConPos = i * 3, i * 8
        
        # CW ([0, 3, 4, 1]) ([1, 4, 5, 2]) #CCW ([1, 4, 3, 0, ]) ([2, 5, 4, 1])
        for arOffset, vertIndexOffset in enumerate([1, 4, 3, 0, 2, 5, 4, 1]):
            connects.set(vi + vertIndexOffset, fConPos + arOffset)
                    
        vAr.set(pnts1[i], vi)
        vAr.set(pnts0[i], vi + 1)
        vAr.set(pnts2[i], vi + 2)
        
    i = pnts0.length() - 1
    vi = i * 3
    vAr.set(pnts1[i], vi)
    vAr.set(pnts0[i], vi + 1)
    vAr.set(pnts2[i], vi + 2)
    
    return vNum, fNum, vAr, counts, connects
    # print 'new corner mesh, faces: ', fNum

def conformedNormalsData(meshFn, intersector, parent):
    vNum = meshFn.numVertices()
    fNum = meshFn.numPolygons()
    
    vAr = om.MPointArray()
    meshFn.getPoints(vAr)

    counts, connects = om.MIntArray(), om.MIntArray()
    # meshFn.getVertices(counts, connects)
     
    for i in range(fNum):
        vertices = om.MIntArray()
        meshFn.getPolygonVertices(i, vertices)
        
        fVertCount = meshFn.polygonVertexCount(i)
        counts.append(fVertCount)
        
        cp = om.MPoint()
        for v in mIter(vertices):
            vPnt = om.MPoint() 
            meshFn.getPoint(v, vPnt)
            cp += om.MVector(vPnt)
        cp = cp / fVertCount
        
        normal = closestMeshPntNorm(cp, intersector)[1]

        fNormal = om.MVector()
        meshFn.getPolygonNormal(i, fNormal)
        
        needReverse = normal * fNormal < 0
        
        if needReverse:
            for v in mIterRv(vertices): connects.append(v)
        else:
            for v in mIter(vertices): connects.append(v)
            
    return vNum, fNum, vAr, counts, connects

def setHardEdges(meshFn, parent):
    f1n, f2n = om.MVector(), om.MVector()
    faces = om.MIntArray()

    smthA = math.radians(30)
    
    eIter = om.MItMeshEdge(parent)
    eIter.reset()
    while not eIter.isDone():
        if not eIter.onBoundary():
            eIter.getConnectedFaces(faces)
                
            if faces.length() == 2:
                meshFn.getPolygonNormal(faces[0], f1n)
                meshFn.getPolygonNormal(faces[1], f2n)
                angle = f1n.angle(f2n)
                if angle > smthA:
                    eIter.setSmoothing(False)
                 
        eIter.next()
            
class faceIter():
    def __init__(self, meshMO):
        self.i = om.MItMeshPolygon(meshMO)
    
    def set(self, id):
        intPtr = om.MScriptUtil().asIntPtr()
        
        self.i.setIndex(id, intPtr)


class mesh():
    '''
    for k in sorted([k for k in om.MFnMesh.__dict__.keys()]):
        print '\tdef ', k, '(self):\n\t\tpass\n'
    '''
    def  __del__ (self):
        pass

    def  __doc__ (self):
        pass

    def  __getattr__ (self):
        pass

    def  __init__ (self):
        pass

    def  __module__ (self):
        pass

    def  __repr__ (self):
        pass

    def  __setattr__ (self):
        pass

    def  __swig_destroy__ (self):
        pass

    def  __swig_getmethods__ (self):
        pass

    def  __swig_setmethods__ (self):
        pass

    def  _s (self):
        pass

    def  addHoles (self):
        pass

    def  addPolygon (self):
        pass

    def  allIntersections (self):
        pass

    def  anyIntersection (self):
        pass

    def  assignColor (self):
        pass

    def  assignColors (self):
        pass

    def  assignUV (self):
        pass

    def  assignUVs (self):
        pass

    def  autoUniformGridParams (self):
        pass

    def  binaryBlindDataComponentId (self):
        pass

    def  booleanOp (self):
        pass

    def  booleanOps (self):
        pass

    def  cachedIntersectionAcceleratorInfo (self):
        pass

    def  className (self):
        pass

    def  cleanupEdgeSmoothing (self):
        pass

    def  clearBlindData (self):
        pass

    def  clearColors (self):
        pass

    def  clearGlobalIntersectionAcceleratorInfo (self):
        pass

    def  clearUVs (self):
        pass

    def  closestIntersection (self):
        pass

    def  collapseEdges (self):
        pass

    def  collapseFaces (self):
        pass

    def  componentTypeFromName (self):
        pass

    def  componentTypeName (self):
        pass

    def  copy (self):
        pass

    def  copyInPlace (self):
        pass

    def  copyUVSetWithName (self):
        pass

    def  create (self):
        pass

    def  createBlindDataType (self):
        pass

    def  createColorSetDataMesh (self):
        pass

    def  createColorSetWithName (self):
        pass

    def  createInPlace (self):
        pass

    def  createUVSetDataMeshWithName (self):
        pass

    def  createUVSetWithName (self):
        pass

    def  currentColorSetName (self):
        pass

    def  currentUVSetName (self):
        pass

    def  deleteColorSet (self):
        pass

    def  deleteEdge (self):
        pass

    def  deleteFace (self):
        pass

    def  deleteUVSet (self):
        pass

    def  deleteVertex (self):
        pass

    def  displayColors (self):
        pass

    def  duplicateFaces (self):
        pass

    def  extractFaces (self):
        pass

    def  extrudeEdges (self):
        pass

    def  extrudeFaces (self):
        pass

    def  freeCachedIntersectionAccelerator (self):
        pass

    def  generateSmoothMesh (self):
        pass

    def  getAssignedUVs (self):
        pass

    def  getAssociatedColorSetInstances (self):
        pass

    def  getAssociatedUVSetInstances (self):
        pass

    def  getAssociatedUVSetTextures (self):
        pass

    def  getBinaryBlindData (self):
        pass

    def  getBinormals (self):
        pass

    def  getBlindDataAttrNames (self):
        pass

    def  getBlindDataFaceVertexIndices (self):
        pass

    def  getBlindDataTypes (self):
        pass

    def  getBoolBlindData (self):
        pass

    def  getCheckSamePointTwice (self):
        pass

    def  getClosestNormal (self):
        pass

    def  getClosestPoint (self):
        pass

    def  getClosestPointAndNormal (self):
        pass

    def  getColor (self):
        pass

    def  getColorIndex (self):
        pass

    def  getColorRepresentation (self):
        pass

    def  getColorSetFamilyNames (self):
        pass

    def  getColorSetNames (self):
        pass

    def  getColorSetsInFamily (self):
        pass

    def  getColors (self):
        pass

    def  getConnectedShaders (self):
        pass

    def  getCreaseEdges (self):
        pass

    def  getCreaseVertices (self):
        pass

    def  getDoubleBlindData (self):
        pass

    def  getEdgeVertices (self):
        pass

    def  getFaceNormalIds (self):
        pass

    def  getFaceUVSetNames (self):
        pass

    def  getFaceVertexBinormal (self):
        pass

    def  getFaceVertexBinormals (self):
        pass

    def  getFaceVertexBlindDataIndex (self):
        pass

    def  getFaceVertexColorIndex (self):
        pass

    def  getFaceVertexColors (self):
        pass

    def  getFaceVertexNormal (self):
        pass

    def  getFaceVertexNormals (self):
        pass

    def  getFaceVertexTangent (self):
        pass

    def  getFaceVertexTangents (self):
        pass

    def  getFloatBlindData (self):
        pass

    def  getHoles (self):
        pass

    def  getIntBlindData (self):
        pass

    def  getInvisibleFaces (self):
        pass

    def  getNormalIds (self):
        pass

    def  getNormals (self):
        pass

    def  getPoint (self):
        pass

    def  getPointAtUV (self):
        pass

    def  getPoints (self):
        pass

    def  getPolygonNormal (self):
        pass

    def  getPolygonTriangleVertices (self):
        pass

    def  getPolygonUV (self):
        pass

    def  getPolygonUVid (self):
        pass

    def  getPolygonVertices (self):
        pass

    def  getRawNormals (self):
        pass

    def  getRawPoints (self):
        pass

    def  getSmoothMeshDisplayOptions (self):
        pass

    def  getStringBlindData (self):
        pass

    def  getTangentId (self):
        pass

    def  getTangents (self):
        pass

    def  getTriangleOffsets (self):
        pass

    def  getTriangles (self):
        pass

    def  getUV (self):
        pass

    def  getUVAtPoint (self):
        pass

    def  getUVSetFamilyNames (self):
        pass

    def  getUVSetNames (self):
        pass

    def  getUVSetsInFamily (self):
        pass

    def  getUVs (self):
        pass

    def  getUvShellsIds (self):
        pass

    def  getVertexColors (self):
        pass

    def  getVertexNormal (self):
        pass

    def  getVertexNormals (self):
        pass

    def  getVertices (self):
        pass

    def  globalIntersectionAcceleratorsInfo (self):
        pass

    def  hasAlphaChannels (self):
        pass

    def  hasBlindData (self):
        pass

    def  hasBlindDataComponentId (self):
        pass

    def  hasColorChannels (self):
        pass

    def  intersect (self):
        pass

    def  isBlindDataTypeUsed (self):
        pass

    def  isColorClamped (self):
        pass

    def  isColorSetPerInstance (self):
        pass

    def  isEdgeSmooth (self):
        pass

    def  isNormalLocked (self):
        pass

    def  isPolygonConvex (self):
        pass

    def  isRightHandedTangent (self):
        pass

    def  isUVSetPerInstance (self):
        pass

    def  kAlpha (self):
        pass

    def  kDifference (self):
        pass

    def  kInternalPoint (self):
        pass

    def  kIntersection (self):
        pass

    def  kInvalid (self):
        pass

    def  kOnEdge (self):
        pass

    def  kRGB (self):
        pass

    def  kRGBA (self):
        pass

    def  kUnion (self):
        pass

    def  lockFaceVertexNormals (self):
        pass

    def  lockVertexNormals (self):
        pass

    def  numColorSets (self):
        pass

    def  numColors (self):
        pass

    def  numEdges (self):
        pass

    def  numFaceVertices (self):
        pass

    def  numNormals (self):
        pass

    def  numPolygons (self):
        pass

    def  numUVSets (self):
        pass

    def  numUVs (self):
        pass

    def  numVertices (self):
        pass

    def  onBoundary (self):
        pass

    def  polyTriangulate (self):
        pass

    def  polygonVertexCount (self):
        pass

    def  removeFaceColors (self):
        pass

    def  removeFaceVertexColors (self):
        pass

    def  removeVertexColors (self):
        pass

    def  renameUVSet (self):
        pass

    def  setBinaryBlindData (self):
        pass

    def  setBoolBlindData (self):
        pass

    def  setCheckSamePointTwice (self):
        pass

    def  setColor (self):
        pass

    def  setColors (self):
        pass

    def  setCreaseEdges (self):
        pass

    def  setCreaseVertices (self):
        pass

    def  setCurrentColorSetName (self):
        pass

    def  setCurrentUVSetName (self):
        pass

    def  setDisplayColors (self):
        pass

    def  setDoubleBlindData (self):
        pass

    def  setEdgeSmoothing (self):
        pass

    def  setFaceColor (self):
        pass

    def  setFaceColors (self):
        pass

    def  setFaceVertexColor (self):
        pass

    def  setFaceVertexColors (self):
        pass

    def  setFaceVertexNormal (self):
        pass

    def  setFaceVertexNormals (self):
        pass

    def  setFloatBlindData (self):
        pass

    def  setIntBlindData (self):
        pass

    def  setInvisibleFaces (self):
        pass

    def  setIsColorClamped (self):
        pass

    def  setNormals (self):
        pass

    def  setPoint (self):
        pass

    def  setPoints (self):
        pass

    def  setSmoothMeshDisplayOptions (self):
        pass

    def  setSomeColors (self):
        pass

    def  setSomeUVs (self):
        pass

    def  setStringBlindData (self):
        pass

    def  setUV (self):
        pass

    def  setUVs (self):
        pass

    def  setVertexColor (self):
        pass

    def  setVertexColors (self):
        pass

    def  setVertexNormal (self):
        pass

    def  setVertexNormals (self):
        pass

    def  sortIntersectionFaceTriIds (self):
        pass

    def  split (self):
        pass

    def  stringBlindDataComponentId (self):
        pass

    def  subdivideEdges (self):
        pass

    def  subdivideFaces (self):
        pass

    def  syncObject (self):
        pass

    def  type (self):
        pass

    def  uniformGridParams (self):
        pass

    def  unlockFaceVertexNormals (self):
        pass

    def  unlockVertexNormals (self):
        pass

    def  updateSurface (self):
        pass
