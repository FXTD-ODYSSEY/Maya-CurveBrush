# Maya-CurveBrush

Tweak NURBS Curve Brush 

This repo is for learning the Maya Context Tool.

[Blog Post](https://blog.l0v0.com/posts/cacaf61d.html)

[en_US](./README.md) | [zh_CN](./README_zh.md)


## Installation 

I using a module installer method to install VertexColorPainter plugin, which you could check [here](https://github.com/robertjoosten/maya-module-installer)   
All you need to do is pretty simple, follow the step below.

1. run `git clone git@github.com:FXTD-ODYSSEY/Maya-CurveBrush.git` clone repo to disk
2. run `cd Maya-CurveBrush` jump to the repo working directory
3. run `git submodule update --init` update submodule
4. drag the `CurveBrush.mel` to your running Maya viewport.

then Maya will generate a `CurveBrush` Shelf.

![image.png](https://pic.rmb.bdstatic.com/bjh/fb71bf67a116e2c0cda241d8e046349f.jpeg)

## Usage

The first two Shelf Button is [ysv Curve Tool](https://www.highend3d.com/maya/script/curve-paint-and-tweak-tool-for-maya#google_vignette) (I make it work in Py2 Py3)  
om1 is OpenMaya 1.0 base on Qt paint solution [Reference](https://github.com/wiremas/spore)  
om2 is OpenMaya 2.0 base on Viewport 2.0 paint solution  
cpp is Maya C++ API base on  Viewport 2.0 paint solution  

## Usage Video


