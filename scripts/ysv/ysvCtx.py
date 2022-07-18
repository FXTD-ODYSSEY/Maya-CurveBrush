'''2:18:07 06 jan 2015'''

import maya.OpenMaya as om
import maya.OpenMayaUI as omui

import maya.cmds as mc

from pymel.core import *
import pymel.core.nodetypes as nt
import pymel.core.datatypes as dt
from maya.mel import eval as mEval

import math
import sys
import itertools as it
import operator

import ysvUtils
import ysvTransforms
import ysvApiWrapers as ysvApi
from  ysvView import getInViewObjs
import ysvView 
import ysvMath

from ysvApiWrapers import dataTypes as apiDt
from ysvApiWrapers import mIter 
from ysvApiWrapers import mIterRv

class cursorType():
    default = "default"
    hand = "hand"
    crossHair = "crossHair"
    dolly = "dolly"
    track = "track"
    tumble = "tumble"

def getMods():
    mods = getModifiers()

    Ctrl, Alt, Shift, Wnd = 0, 0, 0, 0
    if (mods & 1) > 0: Shift = 1
    if (mods & 4) > 0: Ctrl = 1
    if (mods & 8) > 0: Alt = 1
    if (mods & 16): Wnd = 1
    
    return Ctrl, Alt, Shift
    
class baseDraggerCtx():
    def __init__(self, ctxName, curs='crossHair'):
        self.initSel = ls(sl=1)
        
        self.initInViewObjs = getInViewObjs()
        
        liveMeshes = ls(lv=1, dag=1, et=nt.Mesh, ni=1)
        if liveMeshes: self.liveMesh = liveMeshes[0]
        else: self.liveMesh = None
        
        self.ctxName = ctxName
        if draggerContext(self.ctxName, ex=1):
            deleteUI(self.ctxName)                
        
        draggerContext(ctxName, 
                            ppc = self.prePress, pc=self.onPress,
                            dragCommand=self.onDrag,
                            releaseCommand=self.onRelease,
                            finalize=self.finalize, 
                            name = ctxName,
                            cursor=curs, undoMode='step')
        
        
        self.activeView = omui.M3dView().active3dView()
        
        #print 'context with name {0} created'.format(self.ctxName)

    #-----------------------------------------------------------------------
    def noModsLMBOnPress(self):assert False, 'not implemented abstact method'
    def shiftLMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlLMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlShiftLMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftLMBOnPress(self):assert False, 'not implemented abstact method'
    
    def noModsMMBOnPres(self):assert False, 'not implemented abstact method'
    def shiftMMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlMMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlShiftMMBOnPress(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftMMBOnPress(self):assert False, 'not implemented abstact method'
    
    def noModsLMBOnDrag(self):assert False, 'not implemented abstact method'
    def shiftLMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlLMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlShiftLMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftLMBOnDrag(self):assert False, 'not implemented abstact method'
    
    def noModsMMBOnDrag(self):assert False, 'not implemented abstact method'
    def shiftMMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlMMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlShiftMMBOnDrag(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftMMBOnDrag(self):assert False, 'not implemented abstact method'
    
    def noModsLMBOnRelease(self):assert False, 'not implemented abstact method'
    def shiftLMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlLMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlShiftLMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftLMBOnRelease(self):assert False, 'not implemented abstact method'
    
    def noModsMMBOnRelease(self):assert False, 'not implemented abstact method'
    def shiftMMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlMMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlShiftMMBOnRelease(self):assert False, 'not implemented abstact method'
    def ctrlAltShiftMMBOnRelease(self):assert False, 'not implemented abstact method'
    
    
    #-----------------------------------------------------------------------
    def setCursorData(self, xScreen, yScreen):
        self.cursorScreenCoords = (xScreen, yScreen)
        self.cursorWPos, self.cursorWDir = ysvView.viewToWorld(xScreen, yScreen)    
    
    def prePress(self):
        try:
            self.currCam = PyNode(modelPanel(getPanel(wf=1), q=1, cam=1))
            self.viewDir = self.currCam.viewDirection(space='world')
            self.eyePnt = self.currCam.getEyePoint(space='world')
            self.centerOfInterest = self.currCam.getWorldCenterOfInterest()
        except:
            inViewMessage(msg='error in prePress: Set focus in 3d viewPort', fade=1, fst=300)
    
    def printInputData(self):
        print 'mouse bt: ', self.btn
        print 'modifiers: ', getMods()
    
    def onPress(self):
        xScreen, yScreen, dummy = draggerContext(self.ctxName, q=1, ap=1)
        self.setCursorData(xScreen, yScreen)
        self.startCursorScreenCoords = (self.cursorScreenCoords[0], self.cursorScreenCoords[1])
        
        self.btn = draggerContext(self.ctxName, q=1, bu=1)

        self.mods = getMods()
        cntrl, alt, shift = self.mods
        if self.btn ==1:
            if not cntrl and not alt and not shift:
                self.noModsLMBOnPress()
            
            elif shift and not cntrl and not alt:
                self.shiftLMBOnPress() 

            elif cntrl and not shift and not alt:
                self.ctrlLMBOnPress()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftLMBOnPress()

            elif cntrl and shift and alt:
                self.ctrlAltShiftLMBOnPress()
                
        elif self.btn==2:
            if not cntrl and not alt and not shift:
                self.noModsMMBOnPress()
            
            elif shift and not cntrl and not alt:
                self.shiftMMBOnPress() 
    
            elif cntrl and not shift and not alt:
                self.ctrlMMBOnPress()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftMMBOnPress()
    
            elif cntrl and shift and alt:
                self.ctrlAltShiftMMBOnPress()
        
    def onDrag(self):
        xScreen, yScreen, dummy = draggerContext(self.ctxName, q=1, dp=1)
        self.setCursorData(xScreen, yScreen)    
        
        self.cursorDeltaX = self.cursorScreenCoords[0] - self.startCursorScreenCoords[0]
        self.cursorDeltaY = self.cursorScreenCoords[1] - self.startCursorScreenCoords[1]        
        
        cntrl, alt, shift = getMods()
        if self.btn ==1:
            if not cntrl and not alt and not shift:
                self.noModsLMBOnDrag()
            
            elif shift and not cntrl and not alt:
                self.shiftLMBOnDrag() 

            elif cntrl and not shift and not alt:
                self.ctrlLMBOnDrag()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftLMBOnDrag()

            elif cntrl and shift and alt:
                self.ctrlAltShiftLMBOnDrag()
                
        elif self.btn==2:
            if not cntrl and not alt and not shift:
                self.noModsMMBOnDrag()
            
            elif shift and not cntrl and not alt:
                self.shiftMMBOnDrag()
    
            elif cntrl and not shift and not alt:
                self.ctrlMMBOnDrag()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftMMBOnDrag()
    
            elif cntrl and shift and alt:
                self.ctrlAltShiftMMBOnDrag()
                
    def onRelease(self):
        cntrl, alt, shift = getMods()
        if self.btn ==1:
            if not cntrl and not alt and not shift:
                self.noModsLMBOnRelease()
            
            elif shift and not cntrl and not alt:
                self.shiftLMBOnRelease()
        
            elif cntrl and not shift and not alt:
                self.ctrlLMBOnRelease()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftLMBOnRelease()
        
            elif cntrl and shift and alt:
                self.ctrlAltShiftLMBOnRelease()
                
        elif self.btn==2:
            if not cntrl and not alt and not shift:
                self.noModsMMBOnRelease()
            
            elif shift and not cntrl and not alt:
                self.shiftMMBOnRelease()
        
            elif cntrl and not shift and not alt:
                self.ctrlMMBOnRelease()
                
            elif cntrl and shift and not alt:
                self.ctrlShiftMMBOnRelease()
        
            elif cntrl and shift and alt:
                self.ctrlAltShiftMMBOnRelease()
    
    def onHold(self):
        pass
    
    def finalize(self):
        pass
    
    def run(self):
        if draggerContext(self.ctxName, ex=1):
            setToolTo(self.ctxName)
            
    def optionsPopupMenu(self):
        pass
    
    def planeIsect(self, planePnt, planeNormal):
        #print 'inresecting w plane'
        rayLen = 10000
        startL = dt.Point(self.cursorWPos)
        endL = startL+dt.Vector(self.cursorWDir)*rayLen
    
        return ysvMath.linePlaneIntersect(startL, endL, planePnt, planeNormal)    

        
'''
class ctx(baseDraggerCtx):
    def __init__(self, ctxName):
        baseDraggerCtx.__init__(self, ctxName)

        self.inMeshes = ls(sl=1, dag=1, et=nt.Mesh, ni=1) + ls(lv=1, dag=1, et=nt.Mesh, ni=1)

        if not self.inMeshes:
            self.inMeshes = ls(self.initInViewObjs, dag=1, et=nt.Mesh, ni=1)

        self.meshFns = [mesh.__apimfn__() for mesh in self.inMeshes]

        
    def noModsLMBOnPress(self):pass
    def shiftLMBOnPress(self):pass
    def ctrlLMBOnPress(self):pass
    def ctrlShiftLMBOnPress(self):pass
    def ctrlAltShiftLMBOnPress(self):pass
    
    def noModsMMBOnPress(self):pass
    def shiftMMBOnPress(self):pass
    def ctrlMMBOnPress(self):pass
    def ctrlShiftMMBOnPress(self):pass
    def ctrlAltShiftMMBOnPress(self):pass
    
    def noModsLMBOnDrag(self):pass
    def shiftLMBOnDrag(self):pass
    def ctrlLMBOnDrag(self):pass
    def ctrlShiftLMBOnDrag(self):pass
    def ctrlAltShiftLMBOnDrag(self):pass
    
    def noModsMMBOnDrag(self):pass
    def shiftMMBOnDrag(self):pass
    def ctrlMMBOnDrag(self):pass
    def ctrlShiftMMBOnDrag(self):pass
    def ctrlAltShiftMMBOnDrag(self):pass
    
    def noModsLMBOnRelease(self):pass
    def shiftLMBOnRelease(self):pass
    def ctrlLMBOnRelease(self):pass
    def ctrlShiftLMBOnRelease(self):pass
    def ctrlAltShiftLMBOnRelease(self):pass
    
    def noModsMMBOnRelease(self):pass
    def shiftMMBOnRelease(self):pass
    def ctrlMMBOnRelease(self):pass
    def ctrlShiftMMBOnRelease(self):pass
    def ctrlAltShiftMMBOnRelease(self):pass 

    def prePress(self): baseDraggerCtx.prePress(self)
            
    def onPress(self): baseDraggerCtx.onPress(self)
    
    def onDrag(self): baseDraggerCtx.onDrag(self)
    
    def onRelease(self): baseDraggerCtx.onRelease(self)
    
    def run(self): baseDraggerCtx.run(self)
        
    def finalize(self): baseDraggerCtx.finalize(self)
'''        
