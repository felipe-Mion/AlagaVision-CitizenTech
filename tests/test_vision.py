import numpy as np
import pytest
from src.simulator import scene
from src.vision import measure,classify,Configuration

@pytest.mark.parametrize('cm',[0,5,18,39,42,55,69,72,84,95,100])
@pytest.mark.parametrize('condition',['padrao','pouca_luz','chuva','reflexos'])
def test_erro_inferior_a_4cm(cm,condition):
    d=measure(scene(cm,condition,105))
    assert d.level_cm is not None
    assert abs(d.level_cm-cm)<=4.0,(cm,condition,d.level_cm)

@pytest.mark.parametrize('cm,expected',[(0,'NORMAL'),(39.99,'NORMAL'),(40,'ATENCAO'),(69.99,'ATENCAO'),(70,'CRITICO'),(100,'CRITICO')])
def test_limites(cm,expected):assert classify(cm)==expected

def test_roi_invalida():
    with pytest.raises(ValueError):measure(np.zeros((100,100,3),dtype=np.uint8),Configuration())

def test_frame_invalido():
    with pytest.raises(ValueError):measure(np.zeros((100,100),dtype=np.uint8))


def test_sem_cor_nao_significa_nivel_zero():
    blank=np.zeros((500,800,3),dtype=np.uint8)
    d=measure(blank)
    assert d.level_cm is None
    assert d.status=='SEM LEITURA'


def test_perfil_cafe_escuro():
    """Copo escuro sintético simples, superfície detectada com ROI configurada."""
    import cv2
    f=np.full((300,200,3),205,dtype=np.uint8)
    cv2.rectangle(f,(45,180),(155,279),(35,36,42),-1)
    cfg=Configuration(roi=(55,80,145,280),max_cm=8,caution_cm=2.0,critical_cm=5.5,liquid_profile='cafe')
    d=measure(f,cfg)
    assert d.level_cm is not None and abs(d.level_cm-4.0)<0.2
    assert d.status=='ATENCAO'


def test_perfil_cafe_sem_liquido_escuro():
    f=np.full((300,200,3),205,dtype=np.uint8)
    d=measure(f,Configuration(roi=(55,80,145,280),liquid_profile='cafe'))
    assert d.status=='SEM LEITURA'


@pytest.mark.parametrize('photo,roi,expected_range', [
 ('cafe_01.png',(270,705,378,1134),(0.7,1.9)),
 ('cafe_02.png',(205,804,393,1290),(2.0,3.2)),
 ('cafe_03.png',(342,762,518,1183),(5.2,6.8)),
])
def test_cafe_fotos_de_ensaio(photo,roi,expected_range):
    """Teste exploratório de sanidade nas 3 fotos fornecidas, não validação de precisão."""
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    path=root/'data'/'fotos_cafe'/photo
    if not path.exists():
        pytest.skip('Fotos reais opcionais omitidas por privacidade')
    import cv2
    img=cv2.imread(str(path))
    cfg=Configuration(roi=roi,max_cm=8,caution_cm=2.0,critical_cm=5.5,liquid_profile='cafe')
    d=measure(img,cfg)
    assert d.level_cm is not None and expected_range[0] <= d.level_cm <= expected_range[1]
    assert d.status=={'cafe_01.png':'NORMAL','cafe_02.png':'ATENCAO','cafe_03.png':'CRITICO'}[photo]
