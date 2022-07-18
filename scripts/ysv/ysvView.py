import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from maya.mel import eval as mEval
import maya.cmds as mc
from pymel.core import *
import pymel.core.uitypes as ui
import pymel.core.nodetypes as nt
import pymel.core.datatypes as dt
import pymel.mayautils as pu

import math

from  PySide.QtGui import QCursor

def getMods():
    mods = getModifiers()

    Ctrl, Alt, Shift, Wnd = 0, 0, 0, 0
    if (mods & 1) > 0: Shift = 1
    if (mods & 4) > 0: Ctrl = 1
    if (mods & 8) > 0: Alt = 1
    if (mods & 16): Wnd = 1

    return Ctrl, Alt, Shift

def selectFromScreen():
    select(cl=1)
    try:
        activeView = omui.M3dView.active3dView()
        om.MGlobal.selectFromScreen(0,0,activeView.portWidth(),activeView.portHeight(),om.MGlobal.kReplaceList)
    except:
        inViewMessage(msg='Failed to select from screen(in ysvUtils.py)', fade=1, fst=500, pos='midCenter')

def getInViewObjs():
    sel = ls(sl=1)
    select(cl=1)

    selectMode(o=1)
    hilite(ls(hl=1), u=1)

    try:
        activeView = omui.M3dView.active3dView()
        om.MGlobal.selectFromScreen(0,0,activeView.portWidth(),activeView.portHeight(),om.MGlobal.kReplaceList)
    except:
        inViewMessage(msg='Failed to select from screen', fade=1, fst=500, pos='midCenter')    

    result = ls(sl=1)
    select(sel)
    return result

def viewToWorld(xScreen, yScreen):
    pnt, vec = om.MPoint(), om.MVector()

    try: omui.M3dView().active3dView().viewToWorld(
        int(xScreen), int(yScreen), pnt, vec)
    except: pass

    return dt.Point(pnt), dt.Vector(vec)

def worldToView(pnt):
    mPnt  =  om.MPoint(pnt)

    xUtil = om.MScriptUtil()
    yUtil = om.MScriptUtil()

    xPtr = xUtil.asShortPtr()
    yPtr = yUtil.asShortPtr()

    view = omui.M3dView().active3dView()
    try:
        view.worldToView(mPnt, xPtr , yPtr)

        x = om.MScriptUtil(xPtr).asShort()
        y = om.MScriptUtil(yPtr).asShort()
        return x, y
    except:
        pass

def objScreenSize(obj):
    bbMin, bbMax = obj.boundingBox()

    vMin = worldToView(bbMin)
    vMax = worldToView(bbMax)

    screenSize = (dt.Point(vMax) - dt.Point(vMin)).length()
    return int(screenSize)


def getEulerRotationQuaternion(normal, upvector):
    '''
    returns the x,y,z degree angle rotation corresponding to a direction vector
    input: upvector (MVector) & normal (MVector)
    '''
    upvector = om.MVector (upvector[0], upvector[1], upvector[2])
    normalvector = om.MVector(normal[0], normal[1], normal[2])
    quat = om.MQuaternion(upvector, normalvector)
    quatAsEuler = quat.asEulerRotation()

    return math.degrees(quatAsEuler.x), math.degrees(quatAsEuler.y), math.degrees(quatAsEuler.z)

def getCurrCam():
    try:return PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
    except:return None


def meshIntersect(meshFn, inPos, inDir):
    # inMesh object
    pos = om.MFloatPoint(inPos[0], inPos[1], inPos[2])
    rayDir = om.MFloatVector(inDir[0], inDir[1], inDir[2])

    hitPnt = om.MFloatPoint()  # intersection
    hitFace = om.MScriptUtil()
    hitTri = om.MScriptUtil()
    hitFace.createFromInt(0)
    hitTri.createFromInt(0)

    hFacePtr = hitFace.asIntPtr()
    hTriPtr = hitTri.asIntPtr()

    farclip = getCurrCam().getFarClipPlane()
    # print 'getting intersection ', 
    try:
        state = meshFn.closestIntersection(pos,  # RaySource,
                                           rayDir,  # rayDirection
                                           None,  # faceIds
                                           None,  # triIds
                                           True,  # idsSorted
                                           om.MSpace.kWorld,  # space
                                           farclip,  # maxParam
                                           True,  # testBothDirections
                                           None,  # accelParams
                                           hitPnt,  # hitPoint
                                           None,  # hitRayParam      
                                           hFacePtr,  # hitFace
                                           hTriPtr,  # hitTriangle
                                           None,  # hitBary1
                                           None)  # hitBary2
        return state, hitPnt  # , hitFace.getInt(hFacePtr), hitTri.getInt(hTriPtr)
    except:
        pass
        #print 'ERROR: hit failed'
        # raise


def closestHitToMeshes(meshFns, inPos, inDir):
    meshHits = []
    for meshFn in meshFns:
        state, hit = meshIntersect(meshFn, inPos, inDir)
        if state:
            dist = (dt.Point(hit) - inPos).length()
            meshHits.append([dist, dt.Point(hit)])

    if meshHits:    
        return min(meshHits, key = lambda x: x[0])[1]   
    else:
        return False

def closestMeshFromHit(meshes, inPos, inDir):
    try:
        meshHits = []

        if not meshes:return
        for mesh in meshes:
            meshFn = mesh.__apimfn__()
            state, hit = meshIntersect(meshFn, inPos, inDir)
            if state:
                dist = (dt.Point(hit) - inPos).length()
                meshHits.append([dist, mesh])

        if meshHits:    
            return min(meshHits, key = lambda x: x[0])[1]   
        else:
            return False
    except:
        pass
        #print 'closestMeshFromHitFailed'

def meshIntersectInfo(mesh, clickPos, clickDir, farclip=100000.0):
    pos = om.MFloatPoint(clickPos[0], clickPos[1], clickPos[2])
    rayDir = om.MFloatVector(clickDir[0], clickDir[1], clickDir[2])    

    hitFPnt = om.MFloatPoint() 
    hitFace = om.MScriptUtil()
    hitTri = om.MScriptUtil()

    hitFace.createFromInt(0)
    hitTri.createFromInt(0)

    hitFaceptr = hitFace.asIntPtr()
    hitTriptr = hitTri.asIntPtr()

    fnMesh = mesh.__apimfn__()

    hit = fnMesh.closestIntersection(pos,
                                     rayDir,
                                     None,
                                     None,
                                     True,
                                     om.MSpace.kWorld,
                                     farclip,
                                     True,
                                     None,
                                     hitFPnt,
                                     None,
                                     hitFaceptr,
                                     hitTriptr,
                                     None,
                                     None)
    if (hit):
        try:
            pnt = dt.Point(hitFPnt)
            normal, id = mesh.getClosestNormal(pnt, 'world')
            faceId = hitFace.getInt(hitFaceptr)
            return pnt, normal, faceId#, hitTri.getInt(hitTriptr)
        except: 
            return False
    else:
        return False


def closestHitToMeshesInfo(meshes, inPos, inDir):
    meshHits = []

    for mesh in meshes:
        hit = meshIntersectInfo(mesh, inPos, inDir)
        if hit:
            dist = (dt.Point(hit[0]) - inPos).length()
            meshHits.append([dist, hit, mesh])

    if meshHits:    
        hitInfo = min(meshHits, key = lambda x: x[0])
        resDistance,  resultHitInfo, mesh = hitInfo
        return dt.Point(resultHitInfo[0]), resultHitInfo[1], resultHitInfo[2], mesh
    else:
        return False

def toggleSmoothness():
    meshes = ls(sl=1, dag=1, et=nt.Mesh)+ls(hl=1, dag=1, et=nt.Mesh)
    meshes = [mesh for mesh in meshes if not mesh.io.get()]


    curves = ls(sl=1, dag=1, et=nt.NurbsCurve)+ls(hl=1, dag=1, et=nt.NurbsCurve)
    curves = [crv for crv in curves if not crv.io.get()]

    #surfs = ls(sl=1, dag=1, et=nt.NurbsSurface)+ls(hl=1, dag=1, et=nt.NurbsSurface)
    #surfs = [srf for srf in surfs if not surfs.io.get()]

    for mesh in meshes:
        if mesh.displaySmoothMesh.get()==0:
            mesh.displaySmoothMesh.set(2)
        else:
            mesh.displaySmoothMesh.set(0)

        mesh.osdVertBoundary.set(2)

    for crv in curves:
        if displaySmoothness(crv, q=1, pw=1)[0]<=8:
            displaySmoothness(crv, pw=16)
        else:
            displaySmoothness(crv, pw=8)

def toggleDoubleSided():
    hil = ls(hl=1)
    sel = ls(sl=1, o=1)
    sel+=hil
    for obj in sel:
        shape = obj.getShape()
        if shape:
            value = shape.doubleSided.get() 
            shape.doubleSided.set(1-value)    