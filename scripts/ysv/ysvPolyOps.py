# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from functools import reduce
import math
import operator

# Import third-party modules
# reload (mash_repro_utils)
import mash_repro_aetemplate
import mash_repro_utils
import maya.OpenMaya as om
import maya.cmds as mc
from maya.mel import eval as mEval

# import maya.OpenMayaUI as omui
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt

from . import ysvApiWrapers as ysvApi
from . import ysvCurvesOps as yCrvs
from . import ysvUtils
from . import ysvView


# import sys






# import PySide
# from PySide.QtCore import *
# from PySide.QtGui import *

# import shiboken

# import random as r
# import colorsys
# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------Lists------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
def solidVertices(listVertices):
    ids = []
    node = None
    for v in listVertices:
        if not type(v) == MeshVertex:
            continue
        ids += v.indices()
        if not node:
            node = v.node()
    return node.vtx[ids]


def solidEdges(listEdges):
    ids = []
    node = None
    for e in listEdges:
        if not type(e) == MeshEdge:
            continue
        ids += e.indices()
        if not node:
            node = e.node()
    return node.e[ids]


def solidFaces(listFaces):
    ids = []
    node = None
    for f in listFaces:
        if not type(f) == MeshFace:
            continue
        ids += f.indices()
        if not node:
            node = f.node()
    return node.f[ids]


def getMatsAssignments(mesh, getIds=1, getShGroups=0):
    if not mesh or not type(mesh) == nt.Mesh:
        return None, None

    shadersAr = om.MObjectArray()
    shIdsForFaces = om.MIntArray()

    mesh.__apimfn__().getConnectedShaders(0, shadersAr, shIdsForFaces)

    shGroups = [
        nt.ShadingEngine(shadersAr[i])
        for i in range(shadersAr.length())
        if shadersAr[i].apiTypeStr() == "kShadingEngine"
    ]
    ids = list(shIdsForFaces)

    if getIds and getShGroups:
        return shGroups, ids
    elif getIds and not getShGroups:
        return ids
    elif not getIds and getShGroups:
        return shGroups


def getEdgeBorder(components):
    containedFaces = polyListComponentConversion(
        components, ff=1, fv=1, fe=1, fuv=1, fvf=1, tf=1, internal=1
    )
    if not containedFaces:
        containedFaces = polyListComponentConversion(
            components, ff=1, fv=1, fe=1, fuv=1, fvf=1, tf=1
        )

    if containedFaces:
        edges = polyListComponentConversion(containedFaces, ff=1, te=1, bo=1)
        return ls(edges)


# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------Geometry------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------


def edgeToPointDist(edge, point):
    midPoint = (edge.getPoint(0, "world") + edge.getPoint(1, "world")) / 2
    return (midPoint - point).length()


def closestEdge(point, edges):
    edges = solidEdges(edges)
    mesh = edges.currentItem().node()
    edges = ls(edges, fl=1)

    minDist = edgeToPointDist(edges[0], point)
    resultEdge = edges[0]
    for e in edges:
        dist = edgeToPointDist(e, point)
        if dist < minDist:
            minDist = dist
            resultEdge = e

    return resultEdge


def closestVertexFromFace(inPos, closesetPnt, mesh, faceId):
    points = mesh.f[faceId].getPoints("world")

    for i, pos in enumerate(points):
        lng = (pos - closesetPnt).length()
        if i == 0:
            minDist = lng
            resultPos = pos
            continue
        if lng < minDist:
            minDist = lng
            resultPos = pos

    return resultPos


def closestVertex(inPos, mesh):
    clPnt, fId = mesh.getClosestPoint(inPos, space="world")
    points = mesh.f[fId].getPoints("world")

    minDist = 1000000
    for pos in points:
        lng = (pos - inPos).length()
        if lng < minDist:
            minDist = lng
            resPoint = pos

    return resPoint


def getSelectedVertsIds():
    selListHandle = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(
        selListHandle
    )  # give var 'list' as reference to get MSelectionList object

    comp = om.MObject()
    dPath = om.MDagPath()
    for i in range(selListHandle.length()):
        selListHandle.getDagPath(i, dPath, comp)  #
        if comp.apiTypeStr() == "kMeshVertComponent":
            yield (om.MItMeshVertex(dPath, comp), PyNode(dPath))


def closestVertexFast(inPos, meshFn, intersector):
    pntOnMesh = om.MPointOnMesh()
    intersector.getClosestPoint(inPos, pntOnMesh)
    fId = pntOnMesh.faceIndex()
    # print 'faceid:', fId

    vertIds = om.MIntArray()
    meshFn.getPolygonVertices(fId, vertIds)
    # print 'vertsIds: ', list(vertIds)
    pnt = om.MPoint()

    resPoint = None
    minDist = 1000000
    for i in range(vertIds.length()):
        meshFn.getPoint(vertIds[i], pnt)
        lng = pnt.distanceTo(inPos)
        if lng < minDist:
            minDist = lng
            resPoint = om.MPoint(pnt)

    return resPoint


def snapVertsToMeshVerts():
    currentUnit(l="centimeter")
    makeIdentity(ls(sl=1) + ls(hl=1), a=1, r=1, s=1, t=1)
    # makeIdentity(ls(hl=1), a=1, r=1, s=1, t=1)

    mesh = ls(sl=1, dag=1, et=nt.Mesh)

    if mesh:
        mesh = mesh[0]
    if not mesh:
        return

    t = mc.timerX()
    meshFn = mesh.__apimfn__()
    meshMO = meshFn.object()
    intersector = om.MMeshIntersector()
    meshMatr = mesh.__apimdagpath__().inclusiveMatrix()
    intersector.create(meshMO, meshMatr)
    # intersector.create(meshMO)

    for vIter, mesh in getSelectedVertsIds():
        # om.MItMeshVertex.position()
        vertsPos = []
        while not vIter.isDone():
            pos = closestVertexFast(
                vIter.position(om.MSpace.kWorld), meshFn, intersector
            )
            if pos:
                vertsPos.append((vIter.index(), pos))
            next(vIter)

        for ind, pos in vertsPos:
            move(mesh.vtx[ind], pos.x, pos.y, pos.z, a=1, ws=1)

    print("time:", (mc.timerX() - t))


def snapVertsToMeshVerts_old():
    verts = [v for v in ls(sl=1) if type(v) == MeshVertex]
    mesh = ls(sl=1, dag=1, et=nt.Mesh)[0]

    if not mesh or not verts:
        return

    t = mc.timerX()
    verts = ls(verts, fl=1)
    for v in verts:
        pos = closestVertex(v.getPosition("world"), mesh)
        v.setPosition(pos, "world")

    print("time:", (mc.timerX() - t))


def edge2PntDist(edge, point):
    v0 = edge.getPoint(0, space="world")
    v1 = edge.getPoint(1, space="world")

    edgeVec = v1 - v0
    pnt_Vert0_vec = v0 - point

    pntToEdgeDist = (edgeVec.cross(pnt_Vert0_vec).length()) / edge.getLength(
        space="world"
    )

    return pntToEdgeDist


def closestEdgeRatioDist(edge, point):
    v0 = edge.getPoint(0, space="world")

    pnt2Vert0Dist = (v0 - point).length()
    pntToEdgeDist = edge2PntDist(edge, point)

    distToV0 = math.sqrt(pow(pnt2Vert0Dist, 2) - pow(pntToEdgeDist, 2))

    return distToV0


def splitEdgeRatio(edge, fp1, fp2):
    distToV0 = closestEdgeRatioDist(edge, fp1) + closestEdgeRatioDist(edge, fp2)
    distToV0 = distToV0 / 2

    ratio = distToV0 / edge.getLength(space="world")
    return ratio


def commonEdge(f1, f2):
    edges1 = set(f1.getEdges())
    edges2 = set(f2.getEdges())
    commEdges = edges1 & edges2
    if len(commEdges):
        return list(commEdges)[0]


def splitPolyWCurve():
    curves = ysvUtils.SEL.curves()
    meshes = ysvUtils.SEL.polygons()

    if not curves or not meshes:
        return

    crv = curves[0].getShape()
    mesh = meshes[0].getShape()

    step = 2.0

    iterLng = 0.0
    crvLng = crv.length()

    fPnts = []
    while iterLng < crvLng:
        param = crv.findParamFromLength(iterLng)
        pnt = crv.getPointAtParam(param, space="world")
        fPnts.append(pnt)
        iterLng += step

    param = crv.findParamFromLength(crvLng)
    pnt = crv.getPointAtParam(param, space="world")
    fPnts.append(pnt)

    splitPnts = []

    for fPnt in fPnts:
        fPnt, id = mesh.getClosestPoint(fPnt, space="world")
        move(spaceLocator(), fPnt, a=1, ws=1)
        splitPnts.append((id, fPnt.x, fPnt.y, fPnt.z))

    prevFPntId = splitPnts[0][0]
    for i, fPnt in list(enumerate(splitPnts))[1:]:
        currFPntId = fPnt[0]
        if not prevFPntId == currFPntId:
            f0 = mesh.f[prevFPntId]
            f1 = mesh.f[currFPntId]
            edgeId = commonEdge(f0, f1)

            print("edgeId Getted: ", edgeId)
            edge = mesh.e[edgeId]
            print("edge: ", edge)
            print("getting ratio")
            ratio = splitEdgeRatio(edge, f0, f1)
            print("ratio: ", ratio)

            print(
                "splitting edgeId {0} with ratio {1} at faces {2}{3}: ".format(
                    edgeId, ratio, f0, f1
                )
            )
        prevFPntId = currFPntId


# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------Loops------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
def targetWeld(v1, v2):
    # v1, v2 = ls(sl=1, fl=1)
    pos1 = pointPosition(v1, w=1)
    move(v2, pos1, a=1, ws=1)
    polyMergeVertex([v1, v2], ch=0, d=0.001)


def isEdgeLoop(edges):
    verts = ls(polyListComponentConversion(edges, tv=1), fl=1)
    vertsRepeated = [v for edge in edges for v in ls(edge.connectedVertices(), fl=1)]

    startV = endV = None
    for v in verts:
        if vertsRepeated.count(v) == 1 and startV and endV:
            return
        if vertsRepeated.count(v) == 1:
            if not startV:
                startV = v
            elif not endV:
                endV = v

    if not startV:
        startV = vertsRepeated[0]

    return startV, endV


def nextNeighborVertInLoop(vertex, loopEdgesSolid, restLoopVerts):
    neibEdges = [e for e in loopEdgesSolid if e in vertex.connectedEdges()]
    neibVerts = [
        v
        for e in neibEdges
        for v in e.connectedVertices()
        if not v == vertex and v in restLoopVerts
    ]

    return neibVerts[0]


# ===============================================================================
# def getOrderedLoopVerts_old(edges):
#     verts = ls(polyListComponentConversion(edges, tv=1), fl=1)
#
#     try:
#         select(edges)
#         polyToCurve(f=0, dg=1)
#     except:
#         error('polyToCurveFailed in ysvPolyOps.getOrderedLoopVerts()')
#
#     crv = ls(sl=1, dag=1 , et=nt.NurbsCurve)[0]
#
#     vertParams = [(vert, crv.getParamAtPoint(vert.getPosition('world'), 'world')) for vert in verts]
#     vertParams = sorted(vertParams, key=lambda pair:pair[1])
#     verts = [pair[0] for pair in vertParams]
#
#     delete(crv.getParent())
#     return verts
# ===============================================================================


def getOrderedLoopVerts(edges, deleteCrv=True):
    # t = timerX()
    edges = ysvUtils.SEL.edges(edges)
    try:
        select(edges)
        # print 'edges: ', edges
        polyToCurveRes = polyToCurve(f=0, dg=1)
        # print 'poly to curve res: ', polyToCurveRes
    except:
        error("polyToCurveFailed in ysvPolyOps.getOrderedLoopVerts()")
        return

    crvTr, polyEdgeToCurveNode = polyToCurveRes

    # print 'curve:', crv, node
    ids = PyNode(polyEdgeToCurveNode).ics.get()
    for i, id in enumerate(ids):
        id = id.split("[")[1]
        id = id.split("]")[0]
        ids[i] = int(id)

    # print ids
    if not isinstance(edges, list):
        mesh = edges.node()
    else:
        mesh = edges[0].node()
    # print edges
    # print 'edges mesh node: ', mesh
    # print ids
    verts = [mesh.vtx[id] for id in ids]

    if deleteCrv:
        delete(crvTr)

    # print 'sort time: ', timerX() - t
    if deleteCrv:
        return verts
    else:
        return verts, crvTr, polyEdgeToCurveNode


def flatPoly(outerEdges, holeEdges):
    verts = getOrderedLoopVerts(outerEdges)
    points = [v.getPosition("world") for v in verts]

    if not holeEdges:
        hPoints = []
    else:
        verts = getOrderedLoopVerts(holeEdges)
        hPoints = [v.getPosition("world") for v in verts]

    polyCreateFacet(p=points + [()] + hPoints)


def flatPolyFromCurve():
    results = []

    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    for crv in crvs:
        curveFn = crv.__apimfn__()
        pnts = [pntData[0] for pntData in ysvApi.getCurvePntsFromCVs(curveFn)]
        print("pnts getted")
        pnts = [dt.Point(pnt) for pnt in pnts]
        pnts.reverse()
        res = polyCreateFacet(p=pnts)
        polyMergeVertex(res, d=0.05, ch=0)
        results.append(res)
    select(results)


def circulizeLoop(edges=None):
    if not edges:
        edges = ls(sl=1)
    if not edges:
        return

    verts = getOrderedLoopVerts(edges)

    midId = int((len(verts) - 1) / 2)

    arcNode, crvSh = create3PointArc(
        [verts[0].getPosition(), verts[midId].getPosition(), verts[-1].getPosition()]
    )
    crv = PyNode(crvSh).getParent()

    crv = rebuildCurve(crv, rpo=1, kr=0, kcp=1)[0]
    crv.dispCV.set(1)

    paramStep = 1.0 / (len(verts) - 1)
    for i, v in enumerate(verts):
        pnt = pointPosition(crv.u[paramStep * i], w=1)
        move(v, pnt, a=1, ws=1)

    select(verts, crv, r=1)
    eval("CreateWrap")
    wrapNode = ls(listFuture(crv), et=nt.Wrap)[0]
    wrapNode.autoWeightThreshold.set(0)
    wrapNode.weightThreshold.set(0.1)
    wrapNode.maxDistance.set(50)
    wrapNode.exclusiveBind.set(1)

    select(arcNode, r=1)
    setToolTo("ShowManips")


def distributeLoop(edges=None, crv=None):
    if not edges:
        edges = ls(polyListComponentConversion(te=1), fl=1)
    if not crv:
        if ls(sl=1, dag=1, et=nt.NurbsCurve):
            crv = ls(sl=1, dag=1, et=nt.NurbsCurve)[0]
    if not edges:
        return

    curveFromEdges = False

    if not crv:
        try:
            verts, crvTr, polyEdgeToCurveNode = getOrderedLoopVerts(edges, False)
        except:
            print("fail on sorting vert loop")
            return

        crv = ls(crvTr, dag=1, s=1, ni=1)[0]
        curveFromEdges = True
    else:
        verts = getOrderedLoopVerts(edges)
        if not verts:
            return

    if not crv:
        return

    if not curveFromEdges:
        crv = duplicate(crv)[0]

    if len(verts) <= 100:
        cvRebuildMult = 7
    elif len(verts) > 100 and len(verts) <= 300:
        cvRebuildMult = 5
    elif len(verts) > 300:
        cvRebuildMult = 3

    crv = rebuildCurve(crv, rpo=1, kr=0, kcp=0, d=3, s=len(verts) * cvRebuildMult)[0]

    optionVar(iv=("smoothHairCurvesSmoothFactor", 10 / cvRebuildMult))
    mEval("performSmoothHairCurves 0")
    optionVar(iv=("smoothHairCurvesSmoothFactor", 1))

    fCvPos = pointPosition(crv.cv[0], w=1)
    pos0 = verts[0].getPosition("world")
    pos1 = verts[-1].getPosition("world")
    dist0 = (pos0 - fCvPos).length()
    dist1 = (pos1 - fCvPos).length()
    if dist0 > dist1:
        verts.reverse()

    # TODO: check if curve is closed or periodic
    paramStep = 1.0 / (len(verts) - 1)
    for i, v in enumerate(verts):
        pnt = pointPosition(crv.u[paramStep * i], w=1)
        move(v, pnt, a=1, ws=1)

    delete(crv)


def findClosestCurve(edges):
    allLen = [e.getLength() for e in ls(edges, fl=1)]
    avEdgeLen = reduce(operator.add, allLen) / len(allLen)

    allVerts = ls(polyListComponentConversion(edges, tv=1))
    samples = 4
    st = len(allVerts) / samples
    if st == 0:
        st = 1
    verts = [allVerts[i] for i in range(0, len(allVerts), st)]

    vPnts = [pointPosition(v, w=1) for v in verts]

    distData = []
    curves = [c for c in ls(et=nt.NurbsCurve) if not c.io.get()]
    for crv in curves:
        dist = [crv.distanceToPoint(pnt, "world") for pnt in vPnts]
        dist = reduce(operator.add, dist) / samples
        distData.append((dist, crv))

    dist, crv = min(distData, key=lambda x: x[0])

    if dist < avEdgeLen * 3:
        return crv
    else:
        return False

    # for d in distData: print d
    # print 'curve:', crv


def curveEvenPoints(crv, samples):
    # nt.NurbsCurve.getPoi
    points = []
    lng = crv.length()

    step = lng / (samples - 1)
    for i in range(samples):
        currLen = step * i
        par = crv.findParamFromLength(currLen)
        points.append(crv.getPointAtParam(par, "world"))

    return points


def distributeLoopWClosestCurve():
    edges = ysvUtils.SEL.edges()
    if not edges:
        return

    verts = getOrderedLoopVerts(edges)
    if not verts:
        return

    crv = findClosestCurve(edges)
    if not crv:
        inViewMessage(msg="curve not finded", pos="midCenter", fade=1, fst=10)
        warning("curve not finded")
        return False

    cvFirstPos = pointPosition(crv.cv[0], w=1)
    cvLastPos = pointPosition(crv.cv[-1], w=1)
    pos0 = verts[0].getPosition("world")
    pos1 = verts[-1].getPosition("world")

    if (pos0 - cvFirstPos).length() > (pos1 - cvFirstPos).length():
        verts.reverse()

    if not crv.minMaxValue.get() == (0.0, 1.0):
        yCrvs.rbldRange01(crv)
    # --------------- checking placement of start and end verts relative to curve ends
    stDist = min([(cvFirstPos - pos0).length(), (cvFirstPos - pos1).length()])
    endDist = min([(cvLastPos - pos0).length(), (cvLastPos - pos1).length()])

    connEdge = [e for e in verts[0].connectedEdges()][0]
    tol = connEdge.getLength() * 0.3

    # print 'dists: ', stDist, endDist, connEdge.getLength()

    if stDist > tol or endDist > tol:
        partial = True
    else:
        partial = False
    # --------------- checking placement of start and end verts relative to curve ends

    if not partial:
        pnts = curveEvenPoints(crv, len(verts))
        for i, v in enumerate(verts):
            move(v, pnts[i], a=1, ws=1)

        # =======================================================================
        # paramStep = 1.0 / (len(verts) - 1)
        # for i, v in enumerate(verts):
        #     pnt = pointPosition(crv.u[paramStep * i], w=1)
        #     move(v, pnt, a=1, ws=1)
        # =======================================================================
    else:
        distributeLoopPartial(edges, crv)

    return True


def distributeLoopPartial(edges=None, crv=None):
    """!!!!!!!!!!!!!!!! DO NOT REMOVE PRINTs OR IT WILL CRASH !!!!!!!!!!!!!!!!"""
    """ !!!!!!!!!!!!!!!! DO NOT REMOVE PRINTs OR IT WILL CRASH !!!!!!!!!!!!!!!!"""
    """ !!!!!!!!!!!!!!!! DO NOT REMOVE PRINTs OR IT WILL CRASH !!!!!!!!!!!!!!!!"""
    """ !!!!!!!!!!!!!!!! DO NOT REMOVE PRINTs OR IT WILL CRASH !!!!!!!!!!!!!!!!"""
    fromTool = False
    if not edges:
        edges = ysvUtils.SEL.edges()
    if not crv:
        crv = [crv for crv in ls(sl=1, dag=1, et=nt.NurbsCurve) if not crv.io.get()]
        if crv:
            crv = crv[0]
    if not crv:
        fromTool = True
        selectedCrvParams = ysvUtils.SEL.curveParams()
        crv = selectedCrvParams[0].node()

    if not edges or not crv:
        return

    crvFn = crv.__apimfn__()

    verts = getOrderedLoopVerts(ls(edges))
    pos0 = verts[0].getPosition("world")
    pos1 = verts[-1].getPosition("world")

    dPtr = om.MScriptUtil().asDoublePtr()

    print(" ")
    crvFn.closestPoint(
        om.MPoint(pos0[0], pos0[1], pos0[2]), dPtr, 0.01, om.MSpace.kWorld
    )
    print(" ")
    param0 = om.MScriptUtil(dPtr).asFloat()

    print(" ")
    crvFn.closestPoint(
        om.MPoint(pos1[0], pos1[1], pos1[2]), dPtr, 0.01, om.MSpace.kWorld
    )
    print(" ")
    param1 = om.MScriptUtil(dPtr).asFloat()

    print("params:", param0, param1)
    select(crv.u[param0], crv.u[param1], r=1)

    if fromTool:
        if selectedCrvParams:
            params = [
                float(param.split(".u[")[1].split("]")[0])
                for param in selectedCrvParams
            ]
            minPar = min(params)
            maxPar = max(params)
    else:
        minPar = min([param0, param1])
        maxPar = max([param0, param1])

    paramStep = (maxPar - minPar) / (len(verts) - 1)

    minParPos = pointPosition(crv.u[minPar])

    if (minParPos - pos0).length() > (minParPos - pos1).length():
        verts.reverse()

    for i, v in enumerate(verts):
        par = minPar + paramStep * i
        # print i, par
        pnt = pointPosition(crv.u[par], w=1)
        move(v, pnt, a=1, ws=1)

    hilite(edges[0].node())
    selectMode(co=1)
    selectType(pe=1)
    select(edges)


def distributeLoopWCurveTool():

    cmd = 'python("import ysvPolyOps"); \n'
    cmd += "select -r $Selection1 $edges; \n"
    cmd += 'python("ysvPolyOps.distributeLoopPartial()");\n'
    cmd += "select -r $edges;"

    ctx = scriptCtx(
        title="Attach Curve",
        totalSelectionSets=1,
        toolStart="string $edges[] = `ls -sl -fl`; hilite -r ; select -cl;",
        finalCommandScript=cmd,
        cumulativeLists=True,
        expandSelectionList=True,
        setNoSelectionPrompt="Select two curve points",
        setSelectionPrompt="Select a second curve point",
        setDoneSelectionPrompt="Never used because setAutoComplete is set",
        setAutoToggleSelection=True,
        setSelectionCount=2,
        setAutoComplete=True,
        curveParameterPoint=True,
    )

    setToolTo(ctx)

    inViewMessage(
        msg="Select 2 curve parameter points", fade=1, fst=500, pos="topCenter"
    )


def create3PointArc(pnts, res=10):
    arcNode = mc.createNode("makeThreePointCircularArc")
    mc.setAttr(arcNode + ".pt1", pnts[0][0], pnts[0][1], pnts[0][2])
    mc.setAttr(arcNode + ".pt2", pnts[1][0], pnts[1][1], pnts[1][2])
    mc.setAttr(arcNode + ".pt3", pnts[2][0], pnts[2][1], pnts[2][2])
    mc.setAttr(arcNode + ".d", 3)
    mc.setAttr(arcNode + ".s", res)

    crv = mc.createNode("nurbsCurve")
    mc.connectAttr(arcNode + ".oc", crv + ".cr")
    return arcNode, crv


def getEdgesConnects(edges):
    mesh = edges[0].node()
    edgeLoopIds = set([e.index() for e in ls(edges, fl=1)])

    edges = mesh.e[edgeLoopIds]
    compApi = edges.__apicomponent__()

    mesh = edges.node()
    meshFn = mesh.__apimfn__()
    meshDp = mesh.__apimdagpath__()

    edgeConnects = dict()
    onEndEdges = []

    eIter = om.MItMeshEdge(meshDp, compApi.object())
    while not eIter.isDone():
        i = eIter.index()

        curEdgeConnections = om.MIntArray()
        eIter.getConnectedEdges(curEdgeConnections)
        curEdgeConnections = set(curEdgeConnections)

        loopEdgeConns = edgeLoopIds & curEdgeConnections
        connNum = len(loopEdgeConns)

        if len(loopEdgeConns) > 2:
            inViewMessage(
                msg="wrong edge loop selection", fade=1, pos="midCenter", fst=10
            )
            return

        elif connNum == 1:
            onEndEdges.append(i)

        edgeConnects[str(i)] = tuple(loopEdgeConns)

        next(eIter)

    return onEndEdges, edgeConnects


def sortEdgesToLoops(edges):
    t = timerX()

    onEndEdges, edgeConnects = getEdgesConnects(edges)

    loops = []
    while onEndEdges:
        prevEdge = onEndEdges.pop()  # 191
        currLoop = [prevEdge]

        currEdge = edgeConnects[str(prevEdge)][0]
        del edgeConnects[str(prevEdge)]

        while len(edgeConnects[str(currEdge)]) > 1:
            currLoop.append(currEdge)

            e1, e2 = edgeConnects[str(currEdge)]
            del edgeConnects[str(currEdge)]

            if prevEdge == e1:
                nextEdge = e2
            elif prevEdge == e2:
                nextEdge = e1

            prevEdge = currEdge
            currEdge = nextEdge

        del edgeConnects[str(currEdge)]
        onEndEdges.remove(currEdge)

        currLoop.append(currEdge)
        loops.append(currLoop)

    if not edgeConnects:
        return loops

    while edgeConnects:
        first = int(list(edgeConnects.keys())[0])

        if not list(edgeConnects.values())[0]:
            k = list(edgeConnects.keys())[0]
            del edgeConnects[k]
            continue

        currLoop = [first]

        prevEdge = first

        currEdge = edgeConnects[str(first)][0]
        del edgeConnects[str(first)]
        while True:
            currLoop.append(currEdge)

            e1, e2 = edgeConnects[str(currEdge)]
            del edgeConnects[str(currEdge)]

            if prevEdge == e1:
                nextEdge = e2
            elif prevEdge == e2:
                nextEdge = e1

            prevEdge = currEdge
            currEdge = nextEdge

            if currEdge == first:
                break

        loops.append(currLoop)

    print("time: ", timerX() - t)
    return loops


def distributeLoops(edges=None):
    t = timerX()
    if not edges:
        edges = ls(polyListComponentConversion(te=1))
        # edges = ls(edges, fl=1)
    if not edges:
        return
    mesh = edges[0].node()

    for loopIds in sortEdgesToLoops(edges):
        loopEdges = mesh.e[loopIds]
        distributeLoop(loopEdges)

    mes = "distributing edge loops({0}edges) took: {1} sec".format(
        len(edges), timerX() - t
    )
    headsUpMessage(mes)
    # print mes

    hilite(edges[0].node())
    selectMode(co=1)
    selectType(pe=1)
    select(edges)


def alignInLine(edges=None):
    if not edges:
        edges = polyListComponentConversion(te=1)
        edges = ls(edges, fl=1)
    if not edges:
        return

    verts = getOrderedLoopVerts(edges)

    unitVec = pointPosition(verts[-1:][0], w=1) - pointPosition(verts[0], w=1)
    totalLength = unitVec.length()

    unitVec.normalize()
    eCount = len(edges)
    # step = totalLength/eCount
    step = totalLength / eCount

    for i in range(1, eCount):
        pos = dt.Vector()
        prevVertPos = pointPosition(verts[i - 1])
        pos = prevVertPos + unitVec * step

        move(pos[0], pos[1], pos[2], verts[i], a=1, ws=1)


def getHistory(mesh):
    skipThisNodes = [
        "groupId",
        "mesh",
        "groupParts",
        "transform",
        "deformTwist",
        "deformBend",
        "deformSine",
        "deformSquash",
        "deformWave",
        "deformFlare",
        "nurbsCurve",
    ]
    return [
        node for node in listHistory(mesh) if not str(nodeType(node)) in skipThisNodes
    ]


def bevel(edges=None):
    if not edges:
        edges = [sel for sel in ls(sl=1, fl=1) if type(sel) == MeshEdge]

    if edges:
        mesh = edges[0].node()
        allNodes = [node for node in getHistory(mesh)]

        bevelNodes = ls(allNodes, et=nt.PolyBevel2)
        roundNodes = [
            node
            for node in listConnections(bevelNodes)
            if type(node) == nt.RoundConstantRadius
        ]

        roundNode = None
        if roundNodes:
            roundNode = roundNodes[0]

        i = 0
        if not roundNode:
            roundNode = createNode(nt.RoundConstantRadius)
        else:
            while roundNode.radius[i].connections():
                i += 1

        select(edges[-1])
        crvSh = PyNode(polyToCurve(f=2, dg=1, ch=0)[0])
        parent(crvSh.getParent(), mesh.getParent())
        crvSh.intermediateObject.set(1)

        perpEdge = list(set(ls(edges[-1].connectedEdges(), fl=1)) - set(edges))[0]

        select(edges)
        bevelNode = PyNode(
            polyBevel(edges, o=perpEdge.getLength() / 2, oaf=0, af=0, sg=4, ws=1, ch=1)[
                0
            ]
        )
        bevelNode.smoothingAngle.set(180)

        connectAttr(crvSh.worldSpace[0], roundNode.edge[i].inputCurveA[0], f=1)
        connectAttr(crvSh.worldSpace[0], roundNode.edge[i].inputCurveB[0], f=1)
        connectAttr(roundNode.radius[i], bevelNode.offset, f=1)

        roundNode.radius[i].set(perpEdge.getLength() / 2)

        select([mesh.getParent(), roundNode])
        setToolTo("ShowManips")


def findEdgesFromCurve(obj, crv):
    if obj.getShape().__apimdagpath__().hasFn(om.MFn.kMesh):
        meshDP = obj.getShape().__apimdagpath__()
    else:
        print("wrong input attr 1 in meshEdgesFromCurve()")
        return

    crvFn = crv.getShape().__apimfn__()

    eIter = om.MItMeshEdge(meshDP)
    eIter.reset()
    # mat = obj.wm[0].get()
    edgesIds = []
    while not eIter.isDone():
        pnt0 = eIter.point(0, om.MSpace.kWorld)
        pnt1 = eIter.point(1, om.MSpace.kWorld)
        eLng = pnt0.distanceTo(pnt1)

        d0 = crvFn.distanceToPoint(pnt0, om.MSpace.kWorld)
        d1 = crvFn.distanceToPoint(pnt1, om.MSpace.kWorld)
        # print '{0}distances {1}, {2}'.format(eIter.index(), d0,d1)

        if d0 < 0.1 * eLng and d1 < 0.1 * eLng:
            edgesIds.append(eIter.index())

        next(eIter)

    return obj.getShape().e[edgesIds]


def loopCurve(edges):
    select(edges)
    polyToCurve(dg=1, f=0)
    crv = ls(sl=1, dag=1, et=nt.NurbsCurve)
    if not crv:
        headsUpMessage("wrong loop")
        return
    crv = crv[0].getParent()

    return crv


def bridgeEasy(edges=None, maxToDistr=500):
    if not edges:
        edges = ysvUtils.SEL.edges()
    if not edges:
        return
    loops = sortEdgesToLoops(edges)
    if len(loops) < 2:
        headsUpMessage("selection is wrong")
        return

    needToDistribute = True

    ids1, ids2 = loops[:2]
    mesh = edges[0].node()
    meshTr = mesh.getParent()

    if len(ids1) > len(ids2):
        bigLoop = mesh.e[ids1]
        smallLoop = mesh.e[ids2]
    elif len(ids2) > len(ids1):
        bigLoop = mesh.e[ids2]
        smallLoop = mesh.e[ids1]
    elif len(ids1) == len(ids2):
        needToDistribute = False
        smallLoop, bigLoop = mesh.e[ids1], mesh.e[ids2]

    if needToDistribute:
        crvSmall = loopCurve(smallLoop)
        crvBig = loopCurve(bigLoop)

        countToAdd = len(bigLoop) - len(smallLoop)
        select(mesh.e[smallLoop.index()])

        polySelectSp(ring=1)
        polySplitRing(ch=1, stp=2, div=countToAdd, uem=1, sma=30, fq=1)

        smallLoop = ls(findEdgesFromCurve(meshTr, crvSmall), fl=1)
        bigLoop = ls(findEdgesFromCurve(meshTr, crvBig), fl=1)

        # crvSmallLoop = yCrvs.rbldSimple(crvSmall, s=(crvSmall.getShape().length() / len(smallLoop)))
        delete(crvSmall)
        delete(crvBig)

        select(smallLoop)
        polySelectSp(ring=1)
        smallLoops = ls(sl=1, fl=1)
        if len(smallLoops) < maxToDistr:
            distributeLoops(smallLoops)
            distributeLoops(smallLoops)
        # =======================================================================
        # select(bigLoop)
        # polySelectSp(ring=1)
        # bigLoops = ls(sl=1)
        # distributeLoops(bigLoops)
        # distributeLoops(bigLoops)
        # =======================================================================

    select(smallLoop, bigLoop)
    # print 'loops selected'
    select(polyBridgeEdge())
    setToolTo("ShowManips")

    hilite(mesh)


def polyToCrv(edges=None, step=3):
    if not edges:
        edges = ls(sl=1)
    select(edges)
    crv = polyToCurve(f=2, dg=3)[0]
    # print [crv]
    crv = ls(crv, dag=1, et=nt.NurbsCurve)[0]

    length = crv.length()
    res = length / step
    rebuildCurve(
        crv, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=res, d=3, tol=0.01
    )
    if crv.f.get() == 0:
        return crv

    resCurve = yCrvs.crvDetachGentle(crv, res)
    resCurve.getParent().rename("edgesToCurve")
    return resCurve


def fixNormals(sourceMesh, targetMesh):
    trgFace = targetMesh.f[0]
    trgNorm = trgFace.getNormal("world")

    pos = trgFace.getPoint(0, "world")
    srcNorm, id = sourceMesh.getClosestNormal(pos, "world")

    if trgNorm.dot(srcNorm) < 0:
        polyNormal(targetMesh, nm=0, unm=0)


def connectBorders(verts1, verts2):
    verts1 = ls(polyListComponentConversion(verts1, tv=1))
    verts2 = ls(polyListComponentConversion(verts2, tv=1))

    verts1 = solidVertices(verts1)
    verts2 = solidVertices(verts2)

    targsStay = set()

    for v in verts1:
        vPos = v.getPosition("world")
        minDist = 1000000
        for tv in verts2:
            trgPos = tv.getPosition("world")
            lng = (trgPos - vPos).length()

            if lng < minDist:
                minDist = lng
                selTV = tv
                Pos = trgPos

        targsStay.add(selTV.index())
        # v.setPosition(Pos, 'world')
        move(v, Pos, a=1, ws=1)
        # verts1.geomChanged()
    targsRemove = set(verts2.indices()) - targsStay
    node = verts2.node()

    if targsRemove:
        return node.vtx[targsRemove]


def bridge(verts, targetVerts):

    t = mc.timerX()

    targVertsRemove = connectBorders(verts, targetVerts)
    if targVertsRemove:
        connectBorders(targVertsRemove, verts)
    print("bridge took{0} {1}".format(t - mc.timerX(), "seconds"))


def bridgeRapid(edges=None, selType="contig"):
    if not edges:
        edges = ls(sl=1, fl=1)
    if not edges:
        return
    if not len(edges) == 2:
        return

    select(edges[0])
    if selType == "contig":
        polySelectConstraint(type=0x8000, pp=4, m2a=20, m3a=60)
    elif selType == "loop":
        mEval("SelectEdgeLoopSp")
    mc.ConvertSelectionToVertices()
    verts = ls(sl=1)

    select(edges[1])
    if selType == "contig":
        polySelectConstraint(type=0x8000, pp=4, m2a=20, m3a=60)
    elif selType == "loop":
        mEval("SelectEdgeLoopSp")
    mc.ConvertSelectionToVertices()
    targetVerts = ls(sl=1)

    timer(s=1)

    targVertsRemove = connectBorders(verts, targetVerts)
    if targVertsRemove:
        connectBorders(targVertsRemove, verts)
    print("bridge took{0} {1}".format(timer(e=1), "seconds"))


# ---------------------------------------------------------------------------------
# --------------------------------Duplicatir---------------------------------
# ---------------------------------------------------------------------------------


def ExtractDuplicatirSource():
    sel = mc.ls(sl=1, dag=1, et="mesh")
    if not sel:
        return

    objsSh = sel[0]
    obj = mc.listRelatives(objsSh, p=1)[0]

    nodes = mc.listHistory()
    if not nodes:
        return
    dupNode = ""
    for n in nodes:
        if mc.nodeType(n) == "Duplicatir" or mc.nodeType(n) == "Duplicatir2D":
            dupNode = n

    if dupNode:
        sourceObj = mc.polyCube(ch=0)
        sourceMesh = mc.listRelatives(sourceObj, c=1)[0]
        mc.connectAttr(dupNode + ".inMesh", sourceMesh + ".inMesh", f=1)
        mc.DeleteHistory(sourceObj)
        mc.connectAttr(sourceMesh + ".outMesh", dupNode + ".inMesh", f=1)
        sourceObj = mc.rename(sourceObj, obj + "_duplicatirSource")
    mc.select(sourceObj, r=1)


def reSourceGeoDuplicator():
    if not len(mc.ls(sl=1, o=1)) == 2:
        print("select exactly 2 objects, one of them whithout Duplicatir!")
        return
    o1, o2 = mc.ls(sl=1, o=1)
    h1 = mc.listHistory(o1)
    h2 = mc.listHistory(o2)

    source = geoDup = ""

    for node in h1:
        if mc.nodeType(node) == "Duplicatir" or mc.nodeType(node) == "Duplicatir2D":
            source = o2
            geoDup = node

    for node in h2:
        if mc.nodeType(node) == "Duplicatir" or mc.nodeType(node) == "Duplicatir2D":
            if geoDup:
                print("something wrong")
                return
            source = o1
            geoDup = node

    mc.FreezeTransformations(source)
    bb = mc.xform(source, q=1, bb=1, ws=1)
    mc.xform(
        source,
        sp=((bb[0] + bb[3]) / 2, bb[1], bb[2]),
        rp=(((bb[0] + bb[3]) / 2, bb[1], bb[2])),
    )
    mc.move(0, 0, 0, source, rpr=1)
    mc.FreezeTransformations(source)

    shape = mc.listRelatives(source, c=1)[0]
    mc.connectAttr(shape + ".outMesh", geoDup + ".inMesh", f=1)
    # mc.disconnectAttr(shape+".outMesh", geoDup + ".inMesh")


def ConnectGeoDuplicator(is2D=0):
    nodeType = "Duplicatir"
    if is2D:
        nodeType = "Duplicatir2D"

    sel = mc.ls(sl=1, dag=1, et="mesh")
    if not sel:
        return

    objsSh = sel
    objs = mc.listRelatives(objsSh, p=1)

    for o in objs:
        mc.FreezeTransformations(o)
        bb = mc.xform(o, q=1, bb=1, ws=1)
        mc.xform(
            o,
            sp=((bb[0] + bb[3]) / 2, bb[1], bb[2]),
            rp=(((bb[0] + bb[3]) / 2, bb[1], bb[2])),
        )
        mc.move(0, 0, 0, o, rpr=1)
        mc.FreezeTransformations(o)

        dupNode = mc.createNode(nodeType)
        if not is2D:
            mc.setAttr(dupNode + ".BBSizeInZ", l=1)
            mc.setAttr(dupNode + ".BBSizeOutZ", l=1)

        mc.select(o, r=1)

        shapes = mc.listRelatives(o, c=1)
        if not shapes:
            return
        shape = shapes[0]
        connections = mc.listConnections(shape + ".inMesh", s=1, p=1)

        if connections:
            history = connections[0]
            mc.connectAttr(history, dupNode + ".inMesh", f=1)
            mc.connectAttr(dupNode + ".outMesh", shape + ".inMesh", f=1)
        else:
            mergeNode = mc.polyMergeVertex(o, d=0.001, am=1, ch=1)
            history = mc.listConnections(shape + ".inMesh", s=1, p=1)[0]
            mc.connectAttr(history, dupNode + ".inMesh", f=1)
            mc.connectAttr(dupNode + ".outMesh", shape + ".inMesh", f=1)
            mc.disconnectAttr(history, dupNode + ".inMesh")
            mc.delete(mergeNode)
        mc.select(o, r=1)
        mc.polyMergeVertex(d=0.001, am=1, ch=1)

    mc.select(sel, r=1)


def setDuplicatirLength(crv=None, mesh=None):
    crvSh = ls(sl=1, dag=1, et=nt.NurbsCurve)[0]
    crv = crvSh.getParent()

    mesh = ls(sl=1, dag=1, et=nt.Mesh)[0]
    meshTr = mesh.getParent()

    dupNode = [node for node in ls(listHistory(mesh), et="Duplicatir")]
    if dupNode:
        dupNode = dupNode[0]
        crvLen = crvSh.length()

        setAttr(dupNode + ".count", 1)
        copies = math.floor(crvLen / dupNode.BBSizeOutZ.get())

        setAttr(dupNode + ".count", copies)
        meshTr.sz.set(crvLen / dupNode.BBSizeOutZ.get())


# --------------------------------------------------------------
# -----------------------------Other----------------------------------
# ---------------------------------------------------------------
def projectsCVsToMesh(sel, mesh=None):
    startSelection = ls(sl=1)
    curves = ls(sel, dag=1, et=nt.NurbsCurve)
    cvs = [s for s in ls(sel, fl=1) if type(s) == NurbsCurveCV]

    if len(cvs) > 1 or curves:
        softSelect(e=1, sse=0)

    cvCurves = set()
    for cv in ls(cvs, fl=1):
        cvCurves.add(cv.node())
    allCurves = curves + list(cvCurves)

    if not mesh:
        for c in allCurves:
            c.updateCurve()

        initInViewObjs = ysvView.getInViewObjs()
        meshes = ls(initInViewObjs, dag=1, et=nt.Mesh, ni=1)
        currCam = ysvView.getCurrCam()

        minDist = currCam.getFarClipPlane()
        for m in meshes:
            camPos = currCam.getTranslation(space="world")
            meshPos = m.getParent().getBoundingBox(space="world").center()
            dist = (camPos - meshPos).length()
            if dist < minDist:
                minDist = dist
                mesh = m

        if mesh:
            print("fined closest mesh:", mesh)
        else:
            print("mesh not finded")
            return

    for crv in curves:
        cvs += [crv.cv]

    # makeIdentity(mesh.getParent(), a=1, t=1, r=1, s=1)
    # makeIdentity(curves, a=1, t=1, r=1, s=1)

    if mesh.displaySmoothMesh.get() == 2:
        meshFn = mesh.__apimfn__()
        plug = meshFn.findPlug("outSmoothMesh")
        plugMO = plug.asMObject()

        intersector = om.MMeshIntersector()
        matrix = mesh.__apimdagpath__().inclusiveMatrix()
        intersector.create(plugMO, matrix)

        for cv in ls(cvs, fl=1):
            pnt = om.MPoint()
            # newPos, id = mesh.getClosestPoint(cv.getPosition(space='world'), space='world')
            pos = cv.getPosition(space="world")
            clsPnt = ysvApi.closestMeshPoint(
                om.MPoint(pos.x, pos.y, pos.z), intersector
            )[0]

            select(cv)
            move(clsPnt.x, clsPnt.y, clsPnt.z, a=1, ws=1)
            # cv.setPosition(newPos, space='world')
    else:
        for cv in ls(cvs, fl=1):
            newPos, id = mesh.getClosestPoint(
                cv.getPosition(space="world"), space="world"
            )

            select(cv)
            move(newPos, a=1, ws=1)
            # cv.setPosition(newPos, space='world')

    for c in allCurves:
        c.updateCurve()
    select(startSelection)


def projectCurves():
    mesh = ls(sl=1, dag=1, et=nt.Mesh)
    if not mesh:
        return
    mesh = mesh[0]

    curves = ls(sl=1, dag=1, et=nt.NurbsCurve)
    if not curves:
        return

    prjCurvesParents = []
    prjCurves = []

    for c in curves:
        projCurves = polyProjectCurve(mesh.getParent(), c, ch=0)
        prjCurvesParents.append(projCurves[0])
        prjCurves += projCurves[0].getChildren()

        hide(c.getParent())

    parent(prjCurves, w=1)
    delete(prjCurvesParents)
    select(prjCurves)


def flattenMeshesFromUVs():
    meshes = set(ls(sl=1, dag=1, et=nt.Mesh)) - set(ls(sl=1, dag=1, et=nt.Mesh, io=1))
    meshes = list(meshes)

    for mesh in meshes:
        meshTr = mesh.getParent()
        select(meshTr)
        mc.FreezeTransformations()
        mc.CenterPivot()

        area0 = mesh.area()

        dup = duplicate(mesh)[0]
        newMesh = ls(dup, dag=1, et=nt.Mesh)[0]

        positions = []
        for v in newMesh.vtx:
            x, y = v.getUV()
            positions.append((x, y, 0))

        newMesh.setPoints(positions)
        newMeshTr = newMesh.getParent()
        blendName = newMeshTr.shortName()
        select(newMeshTr)
        mc.CenterPivot()
        area1 = newMesh.area()

        r = area0 / area1
        r = math.sqrt(r)
        print(r)
        scale(newMeshTr, r, r, r)
        select(newMeshTr, meshTr)
        align(atl=1, x="mid", y="min", z="mid")
        eval('blendShapeDeleteTarget "blendShape -origin world"')
        blSh = ls(listHistory(), et=nt.BlendShape)[0]
        select(blSh, add=1)

        setAttr(blSh.name() + "." + blendName, 1)


def smtMesh(mesh):
    divLevel = mesh.smoothLevel.get()
    if divLevel > 0:
        displaySmoothness(mesh, po=1)
        if divLevel > 4:
            polySmooth(
                mesh,
                mth=0,
                sdt=2,
                ovb=2,
                ofb=3,
                ofc=0,
                ost=1,
                ocr=0,
                dv=4,
                bnr=1,
                c=1,
                kb=1,
                ksb=1,
                khe=0,
                kt=1,
                kmb=1,
                suv=1,
                peh=0,
                sl=1,
                dpe=1,
                ps=0.1,
                ro=1,
                ch=1,
            )
            polySmooth(
                mesh,
                mth=0,
                sdt=2,
                ovb=2,
                ofb=3,
                ofc=0,
                ost=1,
                ocr=0,
                dv=divLevel - 4,
                bnr=1,
                c=1,
                kb=1,
                ksb=1,
                khe=0,
                kt=1,
                kmb=1,
                suv=1,
                peh=0,
                sl=1,
                dpe=1,
                ps=0.1,
                ro=1,
                ch=1,
            )
        else:
            polySmooth(
                mesh,
                mth=0,
                sdt=2,
                ovb=2,
                ofb=3,
                ofc=0,
                ost=1,
                ocr=0,
                dv=divLevel,
                bnr=1,
                c=1,
                kb=1,
                ksb=1,
                khe=0,
                kt=1,
                kmb=1,
                suv=1,
                peh=0,
                sl=1,
                dpe=1,
                ps=0.1,
                ro=1,
                ch=1,
            )


def multiSoftModFaces():
    nodes = []

    faces = ysvUtils.SEL.faces()
    edges = ysvUtils.SEL.edges()

    if faces:
        mesh = faces[0].node()

        for f in faces:

            cntr = sum(f.getPoints("world")) / f.numVertices()
            node, softModTr = softMod(f, fm=0, fr=35.17, fom=1, fc=cntr)

            nodes.append(softModTr)

            fId = f.index()
            dupFaceMesh = duplicate(mesh)[0].getShape()
            select(dupFaceMesh.f[fId])
            mc.InvertSelection()
            delete()
            delete(dupFaceMesh, ch=1)
            polyExtrudeFacet(dupFaceMesh, tk=1)

            dupMeshTr = dupFaceMesh.getParent()
            select(dupMeshTr)
            move(dupMeshTr.scalePivot, cntr, a=1, ws=1)
            move(dupMeshTr.rotatePivot, cntr, a=1, ws=1)

            scale(dupFaceMesh, 1.2, 1.2, 1.2, r=1, os=1)

            # parent(softModTr, dupFaceMesh)

            mc.SelectTool()
            print("softMod tr:", softModTr)
            print("dupMesh tr:", dupMeshTr)
            select(dupMeshTr, softModTr, r=1)
            parentConstraint(mo=1, w=1)
            scaleConstraint(mo=1, w=1)
    elif edges:
        mesh = edges[0].node()

        pnts = ls(polyListComponentConversion(tv=1), fl=1)
        pnts = [pointPosition(pnt, w=1) for pnt in pnts]

        cntr = sum(pnts) / len(pnts)
        node, softModTr = softMod(edges, fm=0, fr=35.17, fom=1, fc=cntr)
        nodes.append(softModTr)

    select(nodes)
    setToolTo("ShowManips")


def remeshOptionsUI():
    pass


def remesh(res=20):
    t = timerX()

    srcMesh = ls(sl=1, dag=1, et=nt.Mesh, ni=1)[0]

    try:
        mc.particleFill(rs=res, mxx=1, mxy=1, mxz=1, mnx=0, mny=0, mnz=0, pd=2)
    except:
        pass

    particleSh = ls(sl=1, dag=1, s=1)[0]
    solverNode = particleSh.startFrame.listConnections()[0]

    particleSh.meshMethod.set(3)
    particleSh.blobbyRadiusScale.set(2.5)

    particleSh.maxTriangleResolution.set(20)
    particleSh.velocityPerVertex.set(0)
    particleSh.meshSmoothingIterations.set(10)

    trgMesh = createNode(nt.Mesh)

    particleSh.outMesh.connect(trgMesh.i, f=1)

    select(trgMesh.getParent())
    # hyperShade(a='lambert1')
    ysvUtils.whitePhong()

    hide(particleSh.getParent(), srcMesh.getParent())

    transferAttributes(srcMesh, trgMesh, pos=1, nml=0, uvs=0, col=0, spa=0, sm=0)

    smthNode = polySmooth(
        trgMesh,
        mth=0,
        sdt=0,
        ovb=1,
        ofb=3,
        ofc=0,
        ost=1,
        ocr=0,
        dv=2,
        bnr=1,
        c=1,
        kb=1,
        ksb=1,
        khe=0,
        kt=1,
        kmb=1,
        suv=1,
        peh=0,
        sl=1,
        dpe=1,
        ps=0.1,
        ro=1,
        ch=1,
    )

    transferAttributes(srcMesh, trgMesh, pos=1, nml=0, uvs=0, col=0, spa=0, sm=0)

    try:
        remeshHistory_gr = PyNode("remeshHistory_gr")
    except:
        remeshHistory_gr = createNode(nt.Transform, name="remeshHistory_gr")

    parent(srcMesh.getParent(), remeshHistory_gr)
    parent(particleSh.getParent(), remeshHistory_gr)
    parent(solverNode, remeshHistory_gr)
    solverNode.hide()
    select(trgMesh.getParent())

    # ===========================================================================
    # srcMeshTr = srcMesh.getParent()
    # particleTr = particleSh.getParent()
    #
    # particleSh.intermediateObject.set(1)
    # srcMesh.intermediateObject.set(1)
    #
    # parent(particleSh, trgMesh.getParent(), r=1, s=1)
    # parent(srcMesh, trgMesh.getParent(), r=1, s=1)
    #
    # delete(srcMeshTr, particleTr)
    # ===========================================================================
    # print 'source: ', srcMesh
    # print 'target: ', trgMesh
    select(smthNode)
    setToolTo("ShowManips")
    print("time: ", timerX() - t)


def cutCurveCtx():
    # ===========================================================================
    # nt.Camera.getCenterOfInterestPoint(space='world')
    # nt.Camera.getWorldCenterOfInterest()
    #
    # nt.Camera.getEyePoint(space='world')
    # nt.Camera.viewDirection(space='world')
    # ===========================================================================
    obj = ls(sl=1, o=1)[0]

    currCam = PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
    camMatr = currCam.getMatrix(ws=1)

    objMatr = obj.getMatrix(ws=1)
    # viewDir = currCam


# --------------------               MY NODES


def polyFillet(withCurves=False):
    # mEval('handleScriptEditorAction clearHistory')
    if not pluginInfo("polyFillet.py", q=1, l=1):
        loadPlugin("polyFillet.py")

    meshes = ls(sl=1, dag=1, et=nt.Mesh)
    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve)

    if not meshes:
        meshes = ls(lv=1, et=nt.Mesh)
    if not meshes or not crvs:
        warning("select mesh(with proper mats) and curve(s)")
        return

    mesh = meshes[0]

    try:
        node = createNode("polyFillet")
    except:
        error("cannot create node")

    meshFn = mesh.__apimfn__()
    shadersAr = om.MObjectArray()
    matIds = om.MIntArray()
    meshFn.getConnectedShaders(0, shadersAr, matIds)
    node.matIds.set(list(matIds), type="Int32Array")

    for i, crv in enumerate(crvs):
        crv.worldSpace[0].connect(node.edges[i].inCurve, f=1)

        node.edges[i].midOffsets[0].midCurvePos.set(0.0)
        node.edges[i].midOffsets[1].midCurvePos.set(1.0)
        if withCurves:
            genCrv1 = createNode(nt.NurbsCurve)
            genCrv2 = createNode(nt.NurbsCurve)
            node.outCurves[i].a.connect(genCrv1.create, f=1)
            node.outCurves[i].b.connect(genCrv2.create, f=1)
            # genCrv1.dispEP.set(1)
            # genCrv2.dispEP.set(1)

    mesh.o.connect(node.inMesh, f=1)

    genCornMesh = createNode(nt.Mesh)
    node.cornerMesh.connect(genCornMesh.inMesh, f=1)
    polyMergeVertex(genCornMesh, d=0.01, am=1, ch=1)
    select(genCornMesh)
    hyperShade(assign="lambert1")

    select(genCornMesh, node)
    setToolTo("ShowManips")


def polyLoft():
    curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    meshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)

    isFromEdges = False
    if not curves:
        polyEdges = ysvUtils.SEL.edges()
        curves = []
        loops = sortEdgesToLoops(polyEdges)
        for loop in loops[:2]:
            select(polyEdges[0].node().e[loop])

            polyToCurve(f=0, dg=3)
            crv = ls(sl=1, dag=1, et=nt.NurbsCurve)
            if crv:
                crv = crv[0]
                curves.append(crv.getParent())

                crv.dispCV.set(1)
                center = pointPosition(crv.cv[0], w=1)
                xform(crv.getParent(), rp=center, sp=center, ws=1, a=1)

    if not meshes:
        meshes = ls(lv=1)

    if len(curves) < 2:
        return

    print("meshes:", meshes)
    print("curves:", curves)

    lngs = [c.length() for c in curves]
    avLng = reduce(operator.add, lngs) / len(lngs)

    stepVal = avLng / 8

    if not pluginInfo("polyLoft.py", q=1, l=1):
        loadPlugin("polyLoft.py", qt=1)

    try:
        node = createNode("polyLoft")
    except:
        error("cannot create node polyLoft")

    node.step.set(stepVal)
    node.divisionStep.set(stepVal)

    for i, crv in enumerate(curves):
        crv.ws[0].connect(node.inCurves[i], f=1)

    if meshes:
        inMesh = meshes[0]
        makeIdentity(inMesh.getParent(), a=1, r=1, s=1, t=1)

        if inMesh.displaySmoothMesh.get() == 2:
            inMesh.outSmoothMesh.connect(node.inMesh, f=1)
        else:
            inMesh.outMesh.connect(node.inMesh, f=1)

    mesh = createNode(nt.Mesh)
    select(mesh)
    hyperShade(assign="lambert1")

    node.outMesh.connect(mesh.inMesh, f=1)
    node.dv.lock(1)

    select(mesh, node)
    setToolTo("ShowManips")


def curvedCopies(deleteStrip=True):
    if not pluginInfo("CurvedCopies.py", q=1, l=1):
        try:
            loadPlugin("CurvedCopies.py")
        except:
            inViewMessage(msg="Fail on plugin load", fade=1, fst=500, pos="midCenter")
            return

    liveMesh = ls(lv=1, dag=1, et=nt.Mesh, ni=1)
    if not liveMesh:
        inViewMessage(msg="No live mesh, make one", fade=1, fst=500, pos="midCenter")
        return

    meshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)
    if len(meshes) >= 4:
        srcDup, srcDupS, srcDupE, srcDupMid = meshes[:4]
    elif len(meshes) == 3:
        srcDup, srcDupS, srcDupE = meshes
    elif len(meshes) == 2:
        srcDup, srcDupS = meshes
    elif len(meshes) == 1:
        srcDup = meshes[0]
    elif len(meshes) == 0:
        inViewMessage(
            msg="Select 1-4 meshes and curve", fade=1, fst=500, pos="midCenter"
        )
        return

    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    if not crvs:
        inViewMessage(
            msg="Select 1-4 meshes and one curve", fade=1, fst=500, pos="midCenter"
        )
        return

    objs = [liveMesh[0].getParent()]
    objs += [crv.getParent() for crv in crvs]
    objs += [mesh.getParent() for mesh in meshes]
    makeIdentity(crvs + [liveMesh[0].getParent()], a=1, r=1, s=1, t=1)

    for crv in crvs:
        try:
            node = createNode("curvedCopies")
        except:
            node = None

        if not node:
            inViewMessage(msg="CurvedCopies node is not created", fade=1, fst=500)
            return

        if not objExists("stripMeshes"):
            stripGroup = createNode(nt.Transform, n="stripMeshes")
        else:
            stripGroup = PyNode("stripMeshes")

        crv.worldSpace[0].connect(node.inCurve, f=1)
        if liveMesh:
            liveMesh[0].outMesh.connect(node.inMesh, f=1)

        outDupMesh = createNode(nt.Mesh)
        outDupMesh.getParent().rename("outDupMesh")
        hyperShade(assign="lambert1")
        outStripMesh = createNode(nt.Mesh)
        outStripMesh.getParent().rename("outStripMesh")
        hyperShade(assign="lambert1")
        outFlatStripMesh = createNode(nt.Mesh)
        outFlatStripMesh.getParent().rename("outFlatStripMesh")
        hyperShade(assign="lambert1")

        srcDup.outMesh.connect(node.inDupMesh, f=1)

        try:
            srcDupS.outMesh.connect(node.inSDupMesh, f=1)
        except:
            pass

        try:
            srcDupE.outMesh.connect(node.inEDupMesh, f=1)
        except:
            pass

        try:
            srcDupMid.outMesh.connect(node.inMDupMesh, f=1)
        except:
            pass

        node.outDupMesh.connect(outDupMesh.inMesh, f=1)
        node.outMesh.connect(outStripMesh.inMesh, f=1)
        node.outFlatMesh.connect(outFlatStripMesh.inMesh, f=1)

        select(outDupMesh, outFlatStripMesh)
        mc.CreateWrap()

        wrapNode = outDupMesh.inMesh.inputs()[0]

        oldWrapBase = wrapNode.basePoints[0].inputs()

        node.outFlatMesh.connect(wrapNode.basePoints[0], f=1)
        node.outMesh.connect(wrapNode.driverPoints[0], f=1)

        hide(outFlatStripMesh.getParent())

        if deleteStrip:
            delete(oldWrapBase, outStripMesh.getParent())
        else:
            delete(oldWrapBase)

        parent(outFlatStripMesh.getParent(), stripGroup)

        select(outDupMesh.getParent())


def wrapperStrip(flatStrip=False, createCurves=False):
    if not pluginInfo("wrapperStrip.py", q=1, l=1):
        try:
            loadPlugin("wrapperStrip.py")
        except:
            inViewMessage(msg="Fail on plugin load", fade=1, fst=500, pos="midCenter")
            return

    mesh = ls(sl=1, et=nt.Mesh, dag=1, ni=1)
    if mesh:
        mesh = mesh[0]

    if not mesh:
        liveMesh = ls(lv=1, dag=1, et=nt.Mesh, ni=1)
        if not liveMesh:
            inViewMessage(
                msg="No live or selected mesh", fade=1, fst=500, pos="midCenter"
            )
            return
        else:
            mesh = liveMesh[0]

    if not mesh:
        inViewMessage(msg="No live or selected mesh", fade=1, fst=500, pos="midCenter")

    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    if not crvs:
        inViewMessage(msg="Select mesh and curve", fade=1, fst=500, pos="midCenter")
        return

    makeIdentity(crvs + [mesh.getParent()], a=1, r=1, s=1, t=1)

    nodes = []
    stripMeshes = []
    flatStripMeshes = []
    for crv in crvs:
        try:
            node = createNode("wrapperStrip")
        except:
            node = None

        if not node:
            inViewMessage(msg="wrapperStrip node is not created", fade=1, fst=500)
            return

        if not objExists("stripMeshes"):
            stripGroup = createNode(nt.Transform, n="stripMeshes")
        else:
            stripGroup = PyNode("stripMeshes")

        crv.worldSpace[0].connect(node.inCurve, f=1)

        try:
            mesh.outMesh.connect(node.inMesh, f=1)
        except:
            inViewMessage(
                msg="Failed connect to mesh", fade=1, fst=500, pos="midCenter"
            )

        outStripMesh = createNode(nt.Mesh)
        outStripMesh.getParent().rename("outStripMesh")
        node.outMesh.connect(outStripMesh.inMesh, f=1)
        hyperShade(assign="lambert1")

        node.noMidEdge.set(True)

        if flatStrip:
            outFlatStripMesh = createNode(nt.Mesh)
            outFlatStripMesh.getParent().rename("outFlatStripMesh")

            node.outFlatMesh.connect(outFlatStripMesh.inMesh, f=1)
            hyperShade(assign="lambert1")

            flatStripMeshes.append(outFlatStripMesh)
            parent(outFlatStripMesh.getParent(), stripGroup)

        if createCurves:
            crvA = createNode(nt.NurbsCurve)
            crvB = createNode(nt.NurbsCurve)
            node.outCurveA.connect(crvA.create, f=1)
            node.outCurveB.connect(crvB.create, f=1)
            crvA.dispCV.set(1)
            crvB.dispCV.set(1)

        nodes.append(node)
        node.dv.lock(1)
        stripMeshes.append(outStripMesh)

    select(stripMeshes, nodes)
    setToolTo("ShowManips")
    return nodes, stripMeshes, flatStripMeshes


def wrapperStripForMASH(crv, meshes, liveMesh):
    if not crv or not meshes or not liveMesh:
        return

    if not pluginInfo("wrapperStrip.py", q=1, l=1):
        try:
            loadPlugin("wrapperStrip.py")
        except:
            inViewMessage(msg="Fail on plugin load", fade=1, fst=500, pos="midCenter")
            return

    mesh = meshes[0]

    makeIdentity([crv, mesh.getParent()], a=1, r=1, s=1, t=1)

    try:
        node = createNode("wrapperStrip")
    except:
        inViewMessage(msg="wrapperStrip node is not created", fade=1, fst=500)
        return

    if not objExists("stripMeshes"):
        stripGroup = createNode(nt.Transform, n="stripMeshes")
    else:
        stripGroup = PyNode("stripMeshes")

    crv.worldSpace[0].connect(node.inCurve, f=1)

    try:
        liveMesh.outMesh.connect(node.inMesh, f=1)
    except:
        inViewMessage(msg="Failed connect to mesh", fade=1, fst=500, pos="midCenter")
        print("Failed connect to live Mesh")

    mesh.boundingBoxSizeZ.connect(node.inRepMeshMiddleLength, f=1)

    node.dv.lock(1)

    setToolTo("ShowManips")
    return node


def polyStrips(flatStrips=False, createCurves=False):
    wrapperStrip(flatStrip=flatStrips, createCurves=createCurves)


def deformAlongCurve2(deleteStrip=True):
    if not pluginInfo("CurvedCopies.py", q=1, l=1):
        try:
            loadPlugin("CurvedCopies.py")
        except:
            inViewMessage(msg="Fail on plugin load", fade=1, fst=500, pos="midCenter")
            return

    meshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)
    if len(meshes) >= 4:
        srcDup, srcDupS, srcDupE, srcDupMid = meshes[:4]
    elif len(meshes) == 3:
        srcDup, srcDupS, srcDupE = meshes
    elif len(meshes) == 2:
        srcDup, srcDupS = meshes
    elif len(meshes) == 1:
        srcDup = meshes[0]
    elif len(meshes) == 0:
        inViewMessage(
            msg="Select 1-4 meshes and curve", fade=1, fst=500, pos="midCenter"
        )
        return

    crvs = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    if not crvs:
        inViewMessage(
            msg="Select 1-4 meshes and one curve", fade=1, fst=500, pos="midCenter"
        )
        return

    objs = [crv.getParent() for crv in crvs]
    objs += [mesh.getParent() for mesh in meshes]
    # makeIdentity(objs, a=1, r=1, s=1, t=1)
    makeIdentity(crvs, a=1, r=1, s=1, t=1)

    crvCopyNodes = []
    for crv in crvs:
        try:
            node = createNode("curvedCopies")
        except:
            node = None

        if not node:
            inViewMessage(msg="CurvedCopies node is not created", fade=1, fst=500)
            return

        crvCopyNodes.append(node)

        crv.worldSpace[0].connect(node.inCurve, f=1)

        outDupMesh = createNode(nt.Mesh)
        outDupMesh.getParent().rename("outDupMesh")
        hyperShade(assign="lambert1")

        srcDup.outMesh.connect(node.inDupMesh, f=1)

        try:
            srcDupS.outMesh.connect(node.inSDupMesh, f=1)
        except:
            pass

        try:
            srcDupE.outMesh.connect(node.inEDupMesh, f=1)
        except:
            pass

        try:
            srcDupMid.outMesh.connect(node.inMDupMesh, f=1)
        except:
            pass

        node.outDupMesh.connect(outDupMesh.inMesh, f=1)

        motionPathNode = pathAnimation(
            outDupMesh,
            c=crv,
            fm=1,
            f=1,
            fa="z",
            ua="y",
            wut="vector",
            wu=[0, 1, 0],
            iu=0,
            b=0,
            stu=1,
            etu=2,
        )
        motionPathNode = PyNode(motionPathNode)

        ins = motionPathNode.uValue.inputs(p=1, c=1)[0]
        disconnectAttr(ins[1], ins[0])
        motionPathNode.uValue.set(0)

        select(outDupMesh.getParent())

        print("selected: ", ls(sl=1))
        res = mEval(
            "flow -divisions 2 2 30 -objectCentered 0 -localCompute 1 -localDivisions 2 2 2;"
        )

        flowNode = PyNode(res[0])
        ffdNode = PyNode(res[1])
        ffdLatticeNode = PyNode(res[2])
        ffdBaseNode = PyNode(res[3])

        ffdNode.outsideLattice.set(1)

        hide(ffdLatticeNode, ffdBaseNode)
        select(outDupMesh.getParent())

        try:
            hide(crv.getChildren())
        except:
            pass
    select(crvCopyNodes)
    setToolTo("ShowManips")


def deformAlongCurve():
    meshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)
    curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)

    if not meshes:
        return
    if not curves:
        return

    resMeshes = []
    crvCopyNodes = []
    for crv in curves:
        mesh = meshes[0]
        # crv = curves[0]

        dupNode = createNode("curvedCopies")
        crvCopyNodes.append(dupNode)

        crv.worldSpace.connect(dupNode.inCurve, f=1)
        mesh.outMesh.connect(dupNode.inDupMesh, f=1)

        outDupsMesh = createNode(nt.Mesh)
        dupNode.outDupMesh.connect(outDupsMesh.inMesh, f=1)

        resMeshes.append(outDupsMesh.getParent())

        motionPathNode = pathAnimation(
            outDupsMesh,
            c=crv,
            fm=1,
            f=1,
            fa="z",
            ua="y",
            wut="vector",
            wu=[0, 1, 0],
            iu=0,
            b=0,
            stu=1,
            etu=2,
        )
        motionPathNode = PyNode(motionPathNode)

        ins = motionPathNode.uValue.inputs(p=1, c=1)[0]
        disconnectAttr(ins[1], ins[0])
        motionPathNode.uValue.set(0)

        select(outDupsMesh)
        hyperShade(assign="lambert1")

        select(outDupsMesh.getParent())
        res = mEval(
            "flow -divisions 2 2 30 -objectCentered 0 -localCompute 1 -localDivisions 2 2 2;"
        )

        flowNode = PyNode(res[0])
        ffdNode = PyNode(res[1])
        ffdLatticeNode = PyNode(res[2])
        ffdBaseNode = PyNode(res[3])

        ffdNode.outsideLattice.set(1)

        hide(ffdLatticeNode, ffdBaseNode)
        select(outDupsMesh.getParent())

        try:
            hide(crv.getChildren())
        except:
            pass
    select(crvCopyNodes)
    setToolTo("ShowManips")


def polyDistribute(crvSh=None, edges=None):
    curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    edges = ysvUtils.SEL.edges()
    mesh = edges[0].node()

    if not curves:
        return
    crvSh = curves[0]

    try:
        select(edges)
        crvTr, polyEdgeToCurveNode = polyToCurve(f=0, dg=1)
    except:
        error("polyToCurveFailed in ysvPolyOps.polyDistribute(), script stopped")
        return

    if not pluginInfo("polyDistribute.py", q=1, l=1):
        loadPlugin("polyDistribute.py", qt=1)

    try:
        node = createNode("polyDistribute")
    except:
        error("cannot create node polyDistribute")

    makeIdentity(mesh.getParent(), a=1, r=1, s=1, t=1)
    makeIdentity(crvSh.getParent(), a=1, r=1, s=1, t=1)

    minPar, maxPar = crvSh.minMaxValue.get()
    node.startParam.set(minPar)
    node.endParam.set(maxPar)

    polyEdgeCrvNode = PyNode(polyEdgeToCurveNode)
    polyEdgeCrvNode.ics.connect(node.ics, f=1)

    polyEdgeCrvNode.outputcurve.disconnect()
    delete(crvTr)

    mesh.o.connect(node.inMesh, f=1)
    mesh.wm[0].connect(node.im, f=1)
    crvSh.ws[0].connect(node.inc, f=1)

    resMesh = createNode(nt.Mesh, p=mesh.getParent())
    mesh.intermediateObject.set(1)

    hyperShade(a="lambert1")

    node.outMesh.connect(resMesh.i, f=1)
    select(resMesh, node)
    setToolTo("ShowManips")


def connectEdgeLoops():
    edges = ls(sl=1)

    node = edges[0].node()
    meshTr = node.getParent()
    eLoops = sortEdgesToLoops(edges)

    v1 = getOrderedLoopVerts(node.e[eLoops[0]])
    v2 = getOrderedLoopVerts(node.e[eLoops[1]])

    v1Lng = len(v1)
    v2Lng = len(v2)
    lng = min(v1Lng, v2Lng)

    dist1, dist2 = 0, 0

    # if v2Lng>lng:

    for i in range(lng):
        dist1 += (pointPosition(v1[i]) - pointPosition(v2[i])).length()
        dist2 += (pointPosition(v1[i]) - pointPosition(v2[lng - i - 1])).length()

    print(dist1, dist2)

    if dist1 > dist2:
        v1.reverse()

    verts1 = [v.index() for v in v1]
    verts2 = [v.index() for v in v2]

    for i in range(lng):
        # print verts1[i], verts2[i]
        delete(meshTr, ch=1)
        mesh = ls(meshTr, dag=1, et=nt.Mesh, ni=1)[0]
        select(cl=1)
        selectMode(co=1)
        selectType(pv=1)
        hilite(mesh)
        select(mesh.vtx[verts1[i]], mesh.vtx[verts2[i]])
        try:
            mc.ConnectComponents()
        except:
            pass


def mashNetwork(networkName="MASH#", objs=[]):
    # get the number of selected objects
    if not objs:
        sel = ls(sl=1)
    else:
        sel = objs

    numSelObjs = len(sel)

    # create the waiter
    waiter = createNode(nt.MASH_Waiter, n="MASH")
    addAttr(waiter, longName="instancerMessage", at="message")
    # set the presets folder
    presetsFolderOpVar = optionVar(q="mPFL")
    waiter.filename.set(presetsFolderOpVar, type="string")
    # create a Distribute node
    nodeName = waiter.name() + "_Distribute"
    distNode = createNode(nt.MASH_Distribute, n=nodeName)
    distNode.amplitudeX.set(0)

    # for convenience we match the Map Direction to the initial linear distribution
    distNode.mapDirection.set(4)

    mashPythonNode = createNode(nt.MASH_Python, name=waiter.name() + "_Python")
    mashPythonNode.pyScript.set("")

    # connect the Distribute node to the pythonNode

    distNode.positionOutPP.connect(mashPythonNode.positionInPP, f=1)
    distNode.scaleOutPP.connect(mashPythonNode.scaleInPP, f=1)
    distNode.rotationOutPP.connect(mashPythonNode.rotationInPP, f=1)
    distNode.idOutPP.connect(mashPythonNode.idInPP, f=1)
    distNode.visibilityOutPP.connect(mashPythonNode.visibilityInPP, f=1)

    mashPythonNode.scaleOutPP.connect(waiter.inScalePP, f=1)
    mashPythonNode.rotationOutPP.connect(waiter.inRotationPP, f=1)
    mashPythonNode.positionOutPP.connect(waiter.inPositionPP, f=1)
    mashPythonNode.idOutPP.connect(waiter.inIdPP, f=1)
    mashPythonNode.visibilityOutPP.connect(waiter.inVisibilityPP, f=1)

    distNode.waiterMessage.connect(waiter.waiterMessage, f=1)

    # ----------------REPRO
    reproName = waiter.name() + "_Repro"
    instancer = createNode(nt.MASH_Repro, name=reproName, ss=1)

    repro_mesh_shape = createNode(nt.Mesh, n=instancer.name() + "MeshShape")
    repro_mesh = repro_mesh_shape.getParent()
    addAttr(repro_mesh, ln="mashOutFilter", at="bool")
    instancer.outMesh.connect(repro_mesh_shape.inMesh, f=1)
    repro_mesh_shape.worldInverseMatrix[0].connect(instancer.meshMatrix)
    repro_mesh_shape.message.connect(instancer.meshMessage)

    # connect the Waiter to the Instancer or Repro node
    waiter.multiInstancer[0].connect(instancer.inputPoints, f=1)

    # add a message attribute to the instancer
    addAttr(instancer, longName="instancerMessage", at="message")
    # connect message attributes to the instancer so we can find it later if needed
    waiter.instancerMessage.connect(instancer.instancerMessage, f=1)

    # if the user added more then one object to the network, set the number of points to reflect that
    if numSelObjs > 1:
        distNode.pointCount.set(numSelObjs)

        # add the selected objects to the instancer or Repro
    for trans in sel:
        # connect the meshes to the Repro node with this hilarious Python
        # print 'all mash nodes: ', ls(et=nt.MASH_Waiter)
        mash_repro_utils.connect_mesh_group(instancer.name(), trans.name())
        # print 'all mash nodes: ', ls(et=nt.MASH_Waiter)

    # update the Repro interface
    mash_repro_aetemplate.refresh_all_aetemplates(force=True)

    # finally select the Waiter
    select(waiter)

    return waiter, instancer, distNode, mashPythonNode, repro_mesh_shape


def mashNetworkSimple(networkName="MASH#", objs=[]):
    # get the number of selected objects
    if not objs:
        sel = ls(sl=1)
    else:
        sel = objs

    numSelObjs = len(sel)

    # create the waiter
    waiter = createNode(nt.MASH_Waiter, n="MASH")
    addAttr(waiter, longName="instancerMessage", at="message")
    # set the presets folder
    presetsFolderOpVar = optionVar(q="mPFL")
    waiter.filename.set(presetsFolderOpVar, type="string")
    # create a Distribute node

    # ----------------REPRO
    reproName = waiter.name() + "_Repro"
    instancer = createNode(nt.MASH_Repro, name=reproName, ss=1)

    repro_mesh_shape = createNode(nt.Mesh, n=instancer.name() + "MeshShape")
    repro_mesh = repro_mesh_shape.getParent()
    addAttr(repro_mesh, ln="mashOutFilter", at="bool")
    instancer.outMesh.connect(repro_mesh_shape.inMesh, f=1)
    repro_mesh_shape.worldInverseMatrix[0].connect(instancer.meshMatrix)
    repro_mesh_shape.message.connect(instancer.meshMessage)

    # connect the Waiter to the Instancer or Repro node
    waiter.multiInstancer[0].connect(instancer.inputPoints, f=1)

    # add a message attribute to the instancer
    addAttr(instancer, longName="instancerMessage", at="message")
    # connect message attributes to the instancer so we can find it later if needed
    waiter.instancerMessage.connect(instancer.instancerMessage, f=1)

    # if the user added more then one object to the network, set the number of points to reflect that
    for trans in sel:
        # connect the meshes to the Repro node with this hilarious Python
        # print 'all mash nodes: ', ls(et=nt.MASH_Waiter)
        mash_repro_utils.connect_mesh_group(instancer.name(), trans.name())
        # print 'all mash nodes: ', ls(et=nt.MASH_Waiter)

    # update the Repro interface
    mash_repro_aetemplate.refresh_all_aetemplates(force=True)

    # finally select the Waiter
    select(waiter)

    return waiter, instancer, repro_mesh_shape


def mashCurveSetup():
    def warningMess():
        inViewMessage(
            msg="Select mesh and curve and make live mesh",
            fade=1,
            fst=500,
            pos="midCenter",
        )

    curves = ls(sl=1, dag=1, et=nt.NurbsCurve, ni=1)
    meshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1)
    try:
        liveMesh = ls(lv=1, dag=1, et=nt.Mesh, ni=1)[0]
    except:
        warningMess()

    if meshes:
        meshesTr = [mesh.getParent() for mesh in meshes]

    if not curves or not meshes or not liveMesh:
        warningMess()
        return

    startMesh, middleMesh, insertionMesh, endMesh = None, None, None, None

    if len(meshes) == 1:
        middleMesh = meshes[0]
    elif len(meshes) == 2:
        startMesh, middleMesh = meshes[:2]
    elif len(meshes) == 3:
        startMesh, middleMesh, endMesh = meshes[:3]
    elif len(meshes) >= 4:
        startMesh, middleMesh, insertionMesh, endMesh = meshes[:4]

    for crv in curves:
        waiter, instancer, repro_mesh_shape = mashNetworkSimple("MASH#", meshesTr)
        wrapperStripNode = wrapperStripForMASH(crv, meshes, liveMesh)

        try:
            startMesh.boundingBoxSizeZ.connect(
                wrapperStripNode.inRepMeshStartLength, f=1
            )
        except:
            pass

        try:
            middleMesh.boundingBoxSizeZ.connect(
                wrapperStripNode.inRepMeshMiddleLength, f=1
            )
        except:
            pass

        try:
            insertionMesh.boundingBoxSizeZ.connect(
                wrapperStripNode.inRepMeshInsertionLength, f=1
            )
        except:
            pass

        try:
            endMesh.boundingBoxSizeZ.connect(wrapperStripNode.inRepMeshEndLength, f=1)
        except:
            pass

        wrapperStripNode.posPP.connect(waiter.inPositionPP, f=1)
        wrapperStripNode.scPP.connect(waiter.inScalePP, f=1)
        wrapperStripNode.idsPP.connect(waiter.inIdPP, f=1)
        wrapperStripNode.visibilityPP.connect(waiter.inVisibilityPP, f=1)
        # wrapperStripNode.mashAmplitude.connect(waiter.amplitudeZ, f=1)
