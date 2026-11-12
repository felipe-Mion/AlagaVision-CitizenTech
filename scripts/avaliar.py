"""Avalia a estimação somente em imagens geradas e cria evidências gráficas."""
import argparse,csv,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.vision import Configuration,measure,classify,annotate
from src.simulator import scene

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',default='data');p.add_argument('--out',default='resultados')
    a=p.parse_args();base=Path(a.dataset);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with (base/'gabarito.csv').open(encoding='utf8',newline='') as fh:entries=list(csv.DictReader(fh))
    data=[];real=[];pred=[];classes_r=[];classes_p=[];cfg=Configuration()
    for e in entries:
        f=base/'amostras'/e['arquivo'];frame=cv2.imread(str(f))
        if frame is None:raise FileNotFoundError(f)
        truth=float(e['nivel_real_cm']);d=measure(frame,cfg)
        ground_class=classify(truth,cfg)
        data.append([e['arquivo'],e['condicao'],truth,d.level_cm,round(abs(truth-(d.level_cm or 0)),2),ground_class,d.status,d.confidence])
        real.append(truth);pred.append(d.level_cm or 0);classes_r.append(ground_class);classes_p.append(d.status)
    with (out/'predicoes.csv').open('w',newline='',encoding='utf8') as fh:
        wr=csv.writer(fh);wr.writerow(['arquivo','condicao','nivel_real_cm','estimado_cm','erro_abs_cm','classe_real','classe_predita','cobertura_hsv']);wr.writerows(data)
    err=np.abs(np.array(real)-np.array(pred));mae=float(err.mean());rmse=float(np.sqrt(np.mean(err**2)))
    acc=float(np.mean(np.array(classes_r)==np.array(classes_p)))
    labels=['NORMAL','ATENCAO','CRITICO'];cmat=np.array([[sum(a==gt and b==pd for a,b in zip(classes_r,classes_p)) for pd in labels] for gt in labels],dtype=int)
    by={}
    for cond in ['padrao','pouca_luz','chuva','reflexos']:
        er=[r[4] for r in data if r[1]==cond]
        by[cond]={'n':len(er),'mae_cm':round(float(np.mean(er)),3),'erro_max_cm':round(float(max(er)),3)}
    metrics={'contexto':'APENAS dados sintéticos, sem validação em campo','amostras':len(data),'mae_cm':round(mae,3),'rmse_cm':round(rmse,3),'erro_max_cm':round(float(max(err)),3),'acuracia_classe':round(acc,4),'matriz_confusao':cmat.tolist(),'rotulos':labels,'por_condicao':by}
    (out/'metricas.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    fig,ax=plt.subplots(figsize=(7.6,4.5));ax.scatter(real,pred,alpha=.7,s=26);ax.plot([0,100],[0,100],'--',linewidth=1.5,label='Perfeito')
    ax.set(xlabel='Nível de referência (cm)',ylabel='Nível estimado (cm)',title=f'Leituras sintéticas | MAE {mae:.2f} cm')
    ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(out/'comparacao_niveis.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.6,4.5));names=list(by);bars=ax.bar(names,[by[k]['mae_cm'] for k in names])
    ax.bar_label(bars,padding=3,fmt='%.2f');ax.set(ylabel='Erro absoluto médio (cm)',title='Desempenho por condição simulada')
    ax.set_ylim(0,max(2,max(v['mae_cm'] for v in by.values())*1.7));fig.tight_layout();fig.savefig(out/'erro_por_condicao.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(5.6,4.8));ax.imshow(cmat,cmap='Blues',vmin=0)
    for i in range(3):
        for j in range(3):ax.text(j,i,str(cmat[i,j]),ha='center',va='center',fontsize=13)
    ax.set_xticks(range(3),['Normal','Atenção','Crítico']);ax.set_yticks(range(3),['Normal','Atenção','Crítico'])
    ax.set(xlabel='Classe prevista',ylabel='Classe de referência',title=f'Matriz de confusão | acurácia {acc:.1%}')
    fig.tight_layout();fig.savefig(out/'matriz_confusao.png',dpi=160);plt.close(fig)
    for cm,condition,name in [(18,'padrao','exemplo_normal.png'),(54,'chuva','exemplo_atencao.png'),(84,'reflexos','exemplo_critico.png')]:
        frame=scene(cm,condition,2026);d=measure(frame);cv2.imwrite(str(out/name),annotate(frame,d))
    print(json.dumps(metrics,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
