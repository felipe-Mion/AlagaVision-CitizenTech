"""Nível de água em régua calibrada por visão computacional clássica; apenas protótipo."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np

@dataclass(frozen=True)
class Configuration:
    roi: tuple[int,int,int,int] = (330,120,470,426)
    max_cm: float = 100.0
    hsv_lower: tuple[int,int,int] = (89,48,30)
    hsv_upper: tuple[int,int,int] = (125,255,255)
    liquid_profile: str = 'azul'  # 'azul': cor HSV; 'cafe': liquido escuro (baixa luminosidade)
    coffee_value_max: int = 115  # HSV V 0-255, ajustável quando a iluminação varia
    row_min_coverage: float = .53
    minimum_consistent_rows: int = 5
    caution_cm: float = 40.0
    critical_cm: float = 70.0

@dataclass(frozen=True)
class Detection:
    level_cm: Optional[float]
    confidence: float
    status: str
    waterline_y: Optional[int]
    mask: np.ndarray

def classify(level_cm: Optional[float], cfg: Configuration = Configuration()) -> str:
    if level_cm is None: return 'SEM LEITURA'
    if level_cm >= cfg.critical_cm: return 'CRITICO'
    if level_cm >= cfg.caution_cm: return 'ATENCAO'
    return 'NORMAL'

def measure(frame: np.ndarray, cfg: Configuration = Configuration()) -> Detection:
    """ROI -> HSV -> limiar de cor -> morfologia -> nível de superfície."""
    if frame is None or frame.ndim!=3 or frame.shape[2]!=3:
        raise ValueError('Frame inválido: esperado BGR 3 canais')
    x1,y1,x2,y2=cfg.roi;h,w=frame.shape[:2]
    if not (0<=x1<x2<=w and 0<=y1<y2<=h):
        raise ValueError('ROI fora da imagem')
    hsv=cv2.cvtColor(frame[y1:y2,x1:x2], cv2.COLOR_BGR2HSV)
    if cfg.liquid_profile == 'azul':
        mask=cv2.inRange(hsv,np.uint8(cfg.hsv_lower),np.uint8(cfg.hsv_upper))
    elif cfg.liquid_profile == 'cafe':
        if not 0 <= cfg.coffee_value_max <= 255:
            raise ValueError('Limite de luminosidade do café deve estar entre 0 e 255')
        # Café forte nas fotos de teste aparece muito escuro. Não é detecção
        # semântica de café: superfícies igualmente escuras podem gerar falso positivo.
        # O usuário deve restringir a ROI à parte INTERNA do copo.
        mask=cv2.inRange(hsv,np.array((0,0,0),dtype=np.uint8),
                        np.array((179,255,cfg.coffee_value_max),dtype=np.uint8))
    else:
        raise ValueError(f'Perfil de líquido desconhecido: {cfg.liquid_profile}')
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel,iterations=2)
    ratio=np.count_nonzero(mask,axis=1)/float(x2-x1)
    hits=ratio>=cfg.row_min_coverage
    window=cfg.minimum_consistent_rows
    indexes=np.flatnonzero(np.convolve(hits.astype(np.uint8),np.ones(window,dtype=np.uint8),'valid')==window)
    if len(indexes)==0:
        # Falha segura: ausência de cor não é evidência de nível zero.
        return Detection(None,0.0,'SEM LEITURA',None,mask)
    yy=int(indexes[0]);coverage=float(np.mean(ratio[yy:min(yy+20,len(ratio))]))
    cm=float(np.clip((y2-(y1+yy))/(y2-y1)*cfg.max_cm,0,cfg.max_cm))
    return Detection(round(cm,2),round(coverage,3),classify(cm,cfg),y1+yy,mask)

def annotate(frame: np.ndarray, detection: Detection, cfg: Configuration=Configuration(), frame_id: int|None=None)->np.ndarray:
    out=frame.copy();x1,y1,x2,y2=cfg.roi
    colors={'NORMAL':(75,205,83),'ATENCAO':(10,193,239),'CRITICO':(50,54,236),'SEM LEITURA':(180,180,180)}
    color=colors[detection.status]
    cv2.rectangle(out,(x1,y1),(x2,y2),(252,229,165),2)
    if detection.waterline_y is not None and detection.waterline_y<y2:
        cv2.line(out,(x1,detection.waterline_y),(x2,detection.waterline_y),color,3,cv2.LINE_AA)
    cv2.rectangle(out,(0,0),(out.shape[1],77),(20,29,42),-1)
    cv2.putText(out,'ALAGAVISION  |  CITIZENTECH',(19,29),cv2.FONT_HERSHEY_SIMPLEX,.73,(242,246,248),2,cv2.LINE_AA)
    profile_label = 'CAFE (ESCURO)' if cfg.liquid_profile == 'cafe' else 'AZUL'
    cv2.putText(out,f'PERFIL: {profile_label}',(max(19,out.shape[1]-220),57),cv2.FONT_HERSHEY_SIMPLEX,.43,(210,222,229),1,cv2.LINE_AA)
    level='--' if detection.level_cm is None else f'{detection.level_cm:.1f} cm'
    cv2.putText(out,f'NIVEL {level}   STATUS: {detection.status}',(19,58),cv2.FONT_HERSHEY_SIMPLEX,.67,color,2,cv2.LINE_AA)
    if frame_id is not None:
        cv2.putText(out,f'FRAME {frame_id}',(out.shape[1]-143,27),cv2.FONT_HERSHEY_SIMPLEX,.47,(205,219,228),1,cv2.LINE_AA)
    cv2.rectangle(out,(0,out.shape[0]-27),(out.shape[1],out.shape[0]),(20,29,42),-1)
    cv2.putText(out,'PROTOTIPO DIDATICO - NAO SUBSTITUI ALERTAS OFICIAIS',(14,out.shape[0]-9),cv2.FONT_HERSHEY_SIMPLEX,.44,(229,238,243),1,cv2.LINE_AA)
    return out
