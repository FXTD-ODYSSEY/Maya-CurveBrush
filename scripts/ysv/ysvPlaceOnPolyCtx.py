import maya.cmds as mc

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import math as math
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt

import ysvPolyOps
import ysvCurvesOps
import ysvCtx 
from  ysvCtx import baseDraggerCtx
#import ysvApiWrapers
from ysvUtils import SEL
import ysvView
import ysvMath
import ysvTransforms

tmpGroupName = "meshPaintGrp";

class placeCtx(baseDraggerCtx):
    '''
    select mesh and run context. mesh will snap at all other visible meshes on screen
    nomods lmb         = pick and place object on poly(no duplication)                  ______________
    shift lmb          = scale xyz                                                      ______________
    ctrl lmb           = place on poly with duplication(duplicate w graph)              ______________
    ctrl shift lmb     = place on poly with duplication(polyDuplicateAndConnect)        ______________
    ctrl alt shift lmb = place on poly with duplication(instance)                       ______________
    
    nomods mmb         = place picked only on poly(no duplication)                      ______________
    shift mmb          = move up and down(Y Axis)                                       ______________
    ctrl mmb           = rotate around Y                                                ______________                                             
    ctrl shift mmb     = scale on Y axis                                                ______________
    ctrl alt shift mmb = place picked only on poly with snapping to face centers        ______________  
    old: ctrl alt shift mmb = scale on X and Z axis                                          ______________  
    '''
        
    def __init__(self, ctxName):
        baseDraggerCtx.__init__(self, ctxName, 'hand')
        
        sel = ls(sl=1)
        if not objExists(tmpGroupName):
            self.tmpGroup = createNode(nt.Transform, name=tmpGroupName)
            select(sel)
        else:
            self.tmpGroup = PyNode(tmpGroupName)
            
        try: 
            self.sourceMesh = ls(sl=1, dag=1, et=nt.Mesh, ni=1)[0]
            self.dup  = self.sourceMesh.getParent()
        except: 
            print 'select a mesh'
            return
        
        self.inMeshes = ls(self.initInViewObjs, dag=1, et=nt.Mesh, ni=1)
        try: self.inMeshes.remove(self.sourceMesh)
        except: pass
        
        self.meshFns = [mesh.__apimfn__() for mesh in self.inMeshes]
        
        select(self.sourceMesh.getParent())
        try: ysvTransforms.RestoreTMoveValues()
        except: pass
        
        self.placeOnly = False

        try: 
            print 'in Meshes: ',  self.inMeshes
        except: 
            print 'bad setup'
            
        try:
            self.currCam = PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
            self.viewDir = self.currCam.viewDirection(space='world')
            self.eyePnt = self.currCam.getEyePoint(space='world')
            self.centerOfInterest = self.currCam.getWorldCenterOfInterest()
        except:
            inViewMessage(msg='error in prePress: Set focus in 3d viewPort', fade=1, fst=300) 
            
        self.snapToFaceCenter = False
            
    def setMeshes(self):
        try: 
            self.sourceMesh = ls(sl=1, dag=1, et=nt.Mesh, ni=1)[0]
            self.dup = self.sourceMesh.getParent()
        except: 
            print 'select a mesh'
            return
        
        self.inMeshes = ls(self.initInViewObjs, dag=1, et=nt.Mesh, ni=1)
        try: self.inMeshes.remove(self.sourceMesh)
        except: pass
        
        self.meshFns = [mesh.__apimfn__() for mesh in self.inMeshes]
        
        select(self.sourceMesh.getParent())
        
        try: 
            hist = self.dup.history()
            if not ls(hist, et=nt.TransformGeometry):
                ysvTransforms.RestoreTMoveValues()
        except: pass

    def moveCopy(self, dupType=''):
        try: meshHitInfo = ysvView.closestHitToMeshesInfo(self.inMeshes, self.cursorWPos, self.cursorWDir)
        except: return
        
        if  meshHitInfo:
            projectPnt, normal, faceId, hitMesh = meshHitInfo
            if self.snapToFaceCenter:
                pnts = hitMesh.f[faceId].getPoints(space='world')
                projectPnt = sum(pnts)/len(pnts)
                
        else: 
            try:
                projectPnt = self.planeIsect(dt.Point(0, 0, 0), dt.Vector(0, 1, 0))
                normal = dt.Vector(0, 1, 0)
            except:
                return
        if not projectPnt: return
        
        
        if not self.placeOnly:
            if dupType == 'dupAndConnect':
                self.dup = polyDuplicateAndConnect(self.sourceMesh.getParent(), rc=1)[0]
            
            elif dupType == 'instance':
                self.dup = instance(self.sourceMesh.getParent())[0]
      
            else:
                self.dup = duplicate(self.sourceMesh.getParent(), rr=1, un=1, rc=1)[0]
                
            self.placeOnly = True
        else:
            pass
        
        select(self.dup)
        
        try:
            move(self.dup, projectPnt, a=1, ws=1)
            rot = ysvView.getEulerRotationQuaternion(normal, dt.Vector.yAxis)
            xform(self.dup, ro=rot)
            
            refresh(cv=1)   
        except: pass
        
        
    def selectPoly(self):
        inViewObjs = ysvView.getInViewObjs()
        meshes = ls(inViewObjs, dag=1, et=nt.Mesh, ni=1)
        if not meshes: return
        
        closestMesh = ysvView.closestMeshFromHit(meshes, self.cursorWPos, self.cursorWDir)
        
        if not closestMesh:
            select(cl=1)
            self.selectMeshFailed = True
            return
        
        self.selectMeshFailed = False
        
        select(closestMesh.getParent())
        self.setMeshes()
        
        #print 'closest mesh: ', closestMesh
        #print 'transform: ', closestMesh.getParent()
        self.placeOnly = True
        
    def parentToGrp(self):
        try: parent(self.dup, self.tmpGroup)
        except: pass
    
    #-----------------------------------------------LMB Press----------------------------------------------
    def noModsLMBOnPress(self):
        self.selectPoly()
            
    def shiftLMBOnPress(self): 
        '''scaling object while dragging mouse up and down'''
        try: self.selectPoly()
        except: pass        
        
        self.startScale = self.dup.scale.get()
        self.objScreenSize = ysvView.objScreenSize(self.dup)
        
    def ctrlLMBOnPress(self):
        self.placeOnly = False
        self.moveCopy()
        
    def ctrlShiftLMBOnPress(self):
        self.placeOnly = False
        self.moveCopy(dupType='dupAndConnect')
        
    def ctrlAltShiftLMBOnPress(self):
        self.placeOnly = False
        self.moveCopy(dupType='instance')
    #-----------------------------------------------LMB Press----------------------------------------------
    
    #-----------------------------------------------LMB Drag----------------------------------------------
    def noModsLMBOnDrag(self):
        try:
            if self.selectMeshFailed:
                self.selectPoly()
                
            else:
                self.moveCopy()
        except: pass
    
    def shiftLMBOnDrag(self):
        '''scaling object while dragging mouse up and down'''
        yStart = self.startCursorScreenCoords[1]
        yCurrent = self.cursorScreenCoords[1]
        
        screenH = omui.M3dView.active3dView().portHeight()
        yDelta = yCurrent - yStart
        
        objScale = self.startScale
        
        if yDelta >= 0:
            ratio = 1 + yDelta/(screenH - yStart)
        else: 
            ratio = (screenH - yStart + yDelta)/(screenH - yStart)
            if ratio < 0.01: ratio = 0.01
            
        scale(self.dup, ratio*objScale[0], ratio*objScale[1], ratio*objScale[2], a=1, os=1)
        refresh(cv=1)

    def ctrlLMBOnDrag(self):
        self.moveCopy()

    def ctrlShiftLMBOnDrag(self):
        self.moveCopy()

    def ctrlAltShiftLMBOnDrag(self):
        self.snapToFaceCenter = False
        self.moveCopy()
    #-----------------------------------------------LMB Drag----------------------------------------------
    
    def onLMBRelease(self):
        self.placeOnly = False
        self.parentToGrp()
        self.selectMeshFailed = True
        self.snapToFaceCenter = False
        
    #-----------------------------------------------LMB Release----------------------------------------------
    def noModsLMBOnRelease(self):
        self.onLMBRelease()
    def shiftLMBOnRelease(self):
        self.onLMBRelease()
        
    def ctrlLMBOnRelease(self):
        self.onLMBRelease()
    def ctrlShiftLMBOnRelease(self):
        self.onLMBRelease()
    def ctrlAltShiftLMBOnRelease(self):
        self.onLMBRelease()
    #-----------------------------------------------LMB Release----------------------------------------------

    #-----------------------------------------------MMB Press----------------------------------------------
    def noModsMMBOnPress(self):
        self.placeOnly = True
        
        self.moveCopy()        
    
    def shiftMMBOnPress(self):
        '''moving object on Y axis while dragging mouse up and down'''
        try: self.selectPoly()
        except: pass    
        self.totalDisplacement = 0
        
        self.objH = self.dup.getShape().boundingBox().height()
        self.prevCursorY = self.startCursorScreenCoords[1]
        
    def ctrlMMBOnPress(self):
        '''rotating around Y Axis while dragging mouse up and down'''
        try: self.selectPoly()
        except: pass        
        
        self.objH = self.dup.getShape().boundingBox().height()
        self.prevCursorY = self.startCursorScreenCoords[1]
        
    def ctrlShiftMMBOnPress(self):
        '''scaling object on Y while dragging mouse up and down'''
        try: self.selectPoly()
        except: pass        
        
        self.startScale = self.dup.scale.get()
        self.objScreenSize = ysvView.objScreenSize(self.dup)
        
    def ctrlAltShiftMMBOnPress(self):
        # old '''scaling object on XZ while dragging mouse up and down'''
        '''movig selected poly with snapping to face centers'''
        self.placeOnly = True
        self.snapToFaceCenter = True
        self.moveCopy()  
        self.snapToFaceCenter = False
        
        #self.startScale = self.dup.scale.get()
        #self.objScreenSize = ysvView.objScreenSize(self.dup)
    #-----------------------------------------------MMB Press----------------------------------------------
    
    
    
    #-----------------------------------------------MMB Drag----------------------------------------------
    def noModsMMBOnDrag(self):
        self.moveCopy()
    
    def shiftMMBOnDrag(self):
        '''moving object on Y axis while dragging mouse up and down'''
        yCurrent = self.cursorScreenCoords[1]
        yDelta = yCurrent - self.prevCursorY
        
        moveAmount = 0.001*yDelta*self.objH
        self.totalDisplacement += moveAmount
        move(self.dup, 0, moveAmount, 0, r=1, os=1, wd=1)
        #xform(piv=(0, -0.001*yDelta*self.objH, 0), r=1, os=1, wd=1)
        refresh(cv=1)
        self.prevCursorY = yCurrent
    
    def ctrlMMBOnDrag(self):
        '''rotating around Y axis while dragging mouse up and down'''
        yCurrent = self.cursorScreenCoords[1]
        yDelta = yCurrent - self.prevCursorY
        
        rotate(self.dup, 0, 0.005*yDelta*self.objH, 0, r=1, os=1)
        refresh(cv=1)
        self.prevCursorY = yCurrent

    def ctrlShiftMMBOnDrag(self):
        '''scaling object on Y while dragging mouse up and down'''
        yStart = self.startCursorScreenCoords[1]
        yCurrent = self.cursorScreenCoords[1]
        
        screenH = omui.M3dView.active3dView().portHeight()
        yDelta = yCurrent - yStart
        
        objScale = self.startScale
        
        if yDelta >= 0:
            ratio = 1 + yDelta/(screenH - yStart)
        else: 
            ratio = (screenH - yStart + yDelta)/(screenH - yStart)
            if ratio < 0.01: ratio = 0.01
            
        scale(self.dup, objScale[0], ratio*objScale[1], objScale[2], a=1, os=1)
        refresh(cv=1)
        
    def ctrlAltShiftMMBOnDrag(self):
        '''movig selected poly with snapping to face centers'''
        #old '''scaling object on XZ while dragging mouse up and down'''
        '''yStart = self.startCursorScreenCoords[1]
        yCurrent = self.cursorScreenCoords[1]
        screenH = omui.M3dView.active3dView().portHeight()
        yDelta = yCurrent - yStart
        objScale = self.startScale
        if yDelta >= 0:
            ratio = 1 + yDelta/(screenH - yStart)
        else: 
            ratio = (screenH - yStart + yDelta)/(screenH - yStart)
            if ratio < 0.01: ratio = 0.01
            
        scale(self.dup, ratio*objScale[0], objScale[1], ratio*objScale[2], a=1, os=1)'''
        self.snapToFaceCenter = True
        self.moveCopy()
        self.snapToFaceCenter = False
        refresh(cv=1)
    #-----------------------------------------------MMB Drag----------------------------------------------
    
    
    #-----------------------------------------------MMB Release----------------------------------------------
    def noModsMMBOnRelease(self):
        self.snapToFaceCenter = False
    def shiftMMBOnRelease(self):
        move(self.dup, 0, -self.totalDisplacement, 0, r=1, os=1, wd=1)
        #mc.ConvertSelectionToVertices()
        move(self.dup.getShape().vtx, 0, self.totalDisplacement, 0, r=1, os=1, wd=1)
        
    def ctrlMMBOnRelease(self): pass
    def ctrlShiftMMBOnRelease(self):pass
    def ctrlAltShiftMMBOnRelease(self):
        self.snapToFaceCenter = False
    #-----------------------------------------------MMB Release----------------------------------------------
    







