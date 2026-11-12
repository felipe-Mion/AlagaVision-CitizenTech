"""Produz gabarito com 92 imagens *sintéticas* e vídeo para a demonstração."""
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from src.simulator import scene,W,H

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(Path(__file__).resolve().parents[1]/'data'))
    a=p.parse_args();out=Path(a.out);(out/'amostras').mkdir(parents=True,exist_ok=True)
    levels=[0,5,10,15,20,25,30,35,39,40,45,50,55,60,65,69,70,75,80,85,90,95,100]
    conditions=['padrao','pouca_luz','chuva','reflexos'];rows=[]
    for ci,cond in enumerate(conditions):
        for i,cm in enumerate(levels):
            name=f'{cond}_{i:02d}_{int(cm):03d}cm.jpg'
            cv2.imwrite(str(out/'amostras'/name),scene(cm,cond,2026+ci*41+i),[cv2.IMWRITE_JPEG_QUALITY,89])
            rows.append([name,cm,cond])
    with (out/'gabarito.csv').open('w',newline='',encoding='utf8') as fh:
        wr=csv.writer(fh);wr.writerow(['arquivo','nivel_real_cm','condicao']);wr.writerows(rows)
    vw=cv2.VideoWriter(str(out/'demonstracao_simulada.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),12,(W,H))
    if not vw.isOpened():raise RuntimeError('Codec mp4v indisponível')
    for f in range(180):
        cm=92*f/85 if f<85 else (92 if f<108 else 92*(180-f)/72)
        cond='chuva' if f%60>=32 else 'padrao'
        vw.write(scene(max(0,min(100,cm)),cond,50+f))
    vw.release()
    print(f'Dataset sintético: {len(rows)} imagens; vídeo: {out/"demonstracao_simulada.mp4"}')
if __name__=='__main__':main()
