"""Cenas sintéticas controladas. Não representa fotografia de alagamento real."""
from __future__ import annotations
import cv2
import numpy as np
W,H=800,500
ROI=(330,120,470,426)

def scene(level_cm:float, condition:str='padrao',seed:int=0)->np.ndarray:
    if not 0<=level_cm<=100:raise ValueError('nivel fora da escala')
    if condition not in ('padrao','pouca_luz','chuva','reflexos'):raise ValueError('condicao invalida')
    rng=np.random.default_rng(seed)
    im=np.zeros((H,W,3),dtype=np.uint8)
    for y in range(H):
        t=y/H;im[y,:]=(int(70+25*t),int(77+18*t),int(89+14*t))
    for x,width,ht in ((0,130,160),(117,120,220),(620,110,175),(723,77,205)):
        cv2.rectangle(im,(x,78),(x+width,ht+190),(57,65,79),-1)
        for wx in range(x+13,x+width-8,28):
            for wy in range(103,ht+170,36):cv2.rectangle(im,(wx,wy),(wx+11,wy+16),(96,127,143),-1)
    cv2.rectangle(im,(0,410),(W,H),(65,70,74),-1)
    cv2.line(im,(0,425),(W,425),(105,108,109),3)
    for top,bottom,color in (((295,105),(505,445),(96,105,114)),((304,112),(496,438),(67,72,79)),((317,117),(484,428),(115,117,120)),((325,120),(475,426),(133,135,133))):
        cv2.rectangle(im,top,bottom,color,-1)
    for px in range(330,470,14):cv2.line(im,(px,125),(px+4,425),(125,127,128),1)
    for py in range(150,426,42):cv2.line(im,(326,py),(476,py),(124,127,126),1)
    x1,y1,x2,y2=ROI
    true_y=int(round(y2-(y2-y1)*level_cm/100))
    water=(214,132,46)
    if condition=='reflexos':water=(194,133,64)
    if condition=='pouca_luz':water=(172,96,36)
    for x in range(326,475):
        shift=int(2*np.sin(x/13+seed/5)+np.cos(x/7+seed/9))
        start=max(y1,min(y2-6,true_y+shift))
        if start<y2:cv2.line(im,(x,start),(x,y2),water,1)
    if true_y<y2-5:
        for i in range(25):
            yy=int(rng.integers(max(y1,true_y+4),y2))
            xx=int(rng.integers(329,472))
            cv2.line(im,(xx,yy),(min(475,xx+int(rng.integers(2,22))),yy),(239,169,88),1)
    cv2.rectangle(im,(504,y1-1),(552,y2+1),(219,217,200),-1)
    cv2.line(im,(510,y1),(510,y2),(36,43,55),3)
    for n in range(0,101,10):
        yy=int(round(y2-(y2-y1)*n/100))
        cv2.line(im,(509,yy),(525 if n%20 else 533,yy),(39,45,53),2)
        if n%20==0:cv2.putText(im,str(n),(535,yy+4),cv2.FONT_HERSHEY_SIMPLEX,.37,(37,43,51),1,cv2.LINE_AA)
    cv2.putText(im,'cm',(520,108),cv2.FONT_HERSHEY_SIMPLEX,.48,(240,242,240),1,cv2.LINE_AA)
    cv2.putText(im,'CANALETA',(300,458),cv2.FONT_HERSHEY_SIMPLEX,.47,(227,233,237),1,cv2.LINE_AA)
    cv2.putText(im,'CAMERA FIXA / PROTOTIPO',(22,480),cv2.FONT_HERSHEY_SIMPLEX,.49,(210,217,227),1,cv2.LINE_AA)
    if condition=='chuva':
        for _ in range(100):
            x=int(rng.integers(0,W));y=int(rng.integers(80,H-25))
            cv2.line(im,(x,y),(x-2,y+int(rng.integers(6,18))),(185,191,197),1)
        im=np.uint8(np.clip(im.astype(float)+rng.normal(0,7,size=im.shape),0,255))
    elif condition=='reflexos' and true_y<y2-5:
        for _ in range(5):
            xx=int(rng.integers(334,448));yy=int(rng.integers(max(y1,true_y+3),y2-1))
            cv2.ellipse(im,(xx,yy),(int(rng.integers(10,25)),int(rng.integers(1,4))),0,0,360,(220,226,222),-1)
    elif condition=='pouca_luz':
        im=np.uint8(np.clip(im.astype(float)*.67-7,0,255))
    return im
