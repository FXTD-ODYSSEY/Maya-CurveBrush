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

![image](https://user-images.githubusercontent.com/40897360/186061752-cf497009-a736-4e34-b212-4aaaca27315a.png)

## Usage

The first two Shelf Button is [ysv Curve Tool](https://www.highend3d.com/maya/script/curve-paint-and-tweak-tool-for-maya#google_vignette) (I make it work in Py2 Py3)  
om1 is OpenMaya 1.0 base on Qt paint solution [Reference](https://github.com/wiremas/spore)  
om2 is OpenMaya 2.0 base on Viewport 2.0 paint solution  
cpp is Maya C++ API base on  Viewport 2.0 paint solution  

## Usage Video

https://user-images.githubusercontent.com/40897360/186061781-e86a2b1f-4b04-4351-808d-b33a489616fd.mp4


