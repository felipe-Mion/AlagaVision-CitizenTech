"""Gera o relatório acadêmico PDF a partir das métricas locais.

Uso:
    python scripts/gerar_relatorio.py --integrantes "Seu Nome (RM 12345); Colega (RM 45678)"
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Image, Table,
    TableStyle, PageBreak, HRFlowable, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'relatorio' / 'AlagaVision_Relatorio_GS.pdf'
FONT_PAIRS = [
    ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'),
    ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
    ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
]
selected = next(((reg, bold) for reg, bold in FONT_PAIRS if Path(reg).exists() and Path(bold).exists()), None)
if selected:
    pdfmetrics.registerFont(TTFont('DV', selected[0]))
    pdfmetrics.registerFont(TTFont('DV-Bold', selected[1]))
else:
    # Último recurso: fontes internas (sem garantia para todos os símbolos Unicode).
    from reportlab.pdfbase.pdfmetrics import Font
    pdfmetrics.registerFont(Font('DV', 'Helvetica', 'WinAnsiEncoding'))
    pdfmetrics.registerFont(Font('DV-Bold', 'Helvetica-Bold', 'WinAnsiEncoding'))

NAVY = colors.HexColor('#14243A')
TEAL = colors.HexColor('#027C91')
BLUE = colors.HexColor('#056CB3')
PALE = colors.HexColor('#E8F5F7')
LIGHT = colors.HexColor('#EDF2F7')
GREY = colors.HexColor('#536579')
RED = colors.HexColor('#B33131')
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 48
WIDTH = PAGE_W - LEFT - RIGHT

sty = {
    'eyebrow': ParagraphStyle('eyebrow',fontName='DV-Bold',fontSize=9,leading=14,textColor=TEAL,spaceAfter=11),
    'hero': ParagraphStyle('hero',fontName='DV-Bold',fontSize=28,leading=34,textColor=NAVY,spaceAfter=11),
    'subtitle': ParagraphStyle('subtitle',fontName='DV',fontSize=12.4,leading=18,textColor=GREY,spaceAfter=16),
    'h1': ParagraphStyle('h1',fontName='DV-Bold',fontSize=17,leading=23,textColor=NAVY,spaceBefore=7,spaceAfter=11),
    'h2': ParagraphStyle('h2',fontName='DV-Bold',fontSize=11,leading=17,textColor=TEAL,spaceBefore=10,spaceAfter=5),
    'body': ParagraphStyle('body',fontName='DV',fontSize=9.3,leading=15.1,textColor=NAVY,spaceAfter=8),
    'small': ParagraphStyle('small',fontName='DV',fontSize=8.1,leading=12.5,textColor=GREY,spaceAfter=7),
    'metric': ParagraphStyle('metric',fontName='DV-Bold',fontSize=17.2,leading=22,textColor=NAVY,alignment=TA_CENTER),
    'metricname': ParagraphStyle('metricname',fontName='DV',fontSize=8,leading=12,textColor=GREY,alignment=TA_CENTER),
    'quote': ParagraphStyle('quote',fontName='DV-Bold',fontSize=10.5,leading=17,textColor=BLUE,spaceAfter=10),
    'tablehead': ParagraphStyle('tablehead',fontName='DV-Bold',fontSize=8.5,leading=12,textColor=colors.white),
    'table': ParagraphStyle('table',fontName='DV',fontSize=8.1,leading=12,textColor=NAVY),
}


def para(t, style='body'):
    return Paragraph(t, sty[style])


def art(path, maxw=WIDTH, maxh=250):
    import PIL.Image
    fp = ROOT / path
    with PIL.Image.open(fp) as im:
        w,h = im.size
    z=min(maxw/w,maxh/h)
    return Image(str(fp),width=w*z,height=h*z)


def sheet(rows, widths, headers=True, extra=None):
    cells=[[para(escape(str(v)), 'tablehead' if headers and ri==0 else 'table') for v in line] for ri,line in enumerate(rows)]
    tbl=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1 if headers else 0)
    setting=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
             ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
             ('LINEBELOW',(0,-1),(-1,-1),.3,colors.HexColor('#CED8DF'))]
    if headers:setting.append(('BACKGROUND',(0,0),(-1,0),NAVY))
    if extra:setting.extend(extra)
    tbl.setStyle(TableStyle(setting))
    return tbl


def build_footer(c,doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0,0,PAGE_W,11,fill=1,stroke=0)
    c.setStrokeColor(colors.HexColor('#E3E8EF'))
    c.line(LEFT,35,PAGE_W-RIGHT,35)
    c.setFont('DV',8)
    c.setFillColor(GREY)
    c.drawString(LEFT,21,'ALAGAVISION  /  GLOBAL SOLUTION 2026.2  /  FIAP')
    c.drawRightString(PAGE_W-RIGHT,21,f'{doc.page}')
    c.restoreState()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--integrantes',default='Felipe Mion de Andrade (RM 553715)',help='Nomes e RMs separados por ponto e vírgula')
    ap.add_argument('--output',default=str(OUT))
    args=ap.parse_args()
    m=json.loads((ROOT/'resultados/metricas.json').read_text(encoding='utf-8'))
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    doc=BaseDocTemplate(str(output),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=43,bottomMargin=50,
                        title='AlagaVision - Relatório Técnico Global Solution',author='Felipe Mion de Andrade - RM 553715',subject='Cognitive Computing, Computer Vision And IoT Systems')
    frame=Frame(LEFT,50,WIDTH,PAGE_H-50-43,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='pages',frames=[frame],onPage=build_footer))
    S=[]

    # PAGE 1 - CAPA
    S += [Spacer(1,26),para('GLOBAL SOLUTION 2026.2  ·  CITIZENTECH','eyebrow'),
          para('AlagaVision','hero'),
          para('Visão computacional para monitoramento didático de nível de água e classificação de alertas','subtitle'),
          HRFlowable(width='100%',thickness=1.2,color=TEAL,spaceAfter=21),
          art('resultados/exemplo_critico.png',WIDTH,288),Spacer(1,22),
          para('DISCIPLINA','eyebrow'),
          para('Cognitive Computing, Computer Vision and IoT Systems  ·  Prof. Arnaldo Jr','body'),
          para('<b>Integrantes:</b> '+escape(args.integrantes),'body'),
          Spacer(1,12),para('Documento técnico • Métricas sintéticas e teste fotográfico exploratório • Novembro de 2026','small'),
          PageBreak()]

    # PAGE 2 - PROBLEMA
    S += [para('01  |  Problema e proposta de valor','h1'),
          para('Pontos de acúmulo de água em ruas, instalações e espaços comunitários podem carecer de monitoramento acessível. A proposta AlagaVision investiga uma maneira de transformar vídeo de uma câmera fixa em uma leitura aproximada da altura da água em um recipiente ou canal calibrado, com sinalização visual do estado.','body'),
          para('Público beneficiado e resultado esperado','h2'),
          para('Moradores, responsáveis por instalações comunitárias e equipes de manutenção são beneficiários potenciais <b>após</b> estudos de campo. O resultado do protótipo é uma leitura em centímetros, classificação de estado e registro por quadro. Ele não prevê alagamentos nem substitui profissionais de resposta a emergências.','body'),
          para('Alinhamento com a Global Solution','h2'),
          sheet([['ODS','Contribuição conceitual'],
                 ['ODS 11 - Cidades sustentáveis','Apoio à observação de locais vulneráveis a acúmulo de água'],
                 ['ODS 9 - Indústria e infraestrutura','Uso de visão computacional em infraestrutura de baixo custo'],
                 ['ODS 13 - Ação climática','Demonstração de informação visual para apoio à resiliência']],
                [153,WIDTH-153]),
          Spacer(1,17),
          para('Questão orientadora','h2'),
          para('É possível estimar o nível de um líquido em imagens calibradas, tanto em vídeo sintético com água azul quanto em fotografias de um copo com café escuro, sem webcam conectada ao computador?','quote'),
          para('Escopo verificável','h2'),
          para('O trabalho apresenta código Python, vídeos e fotos, gabarito sintético, gráficos, testes automatizados e três fotografias reais de um copo com café. As fotografias são ensaio exploratório; não houve teste em enchente real nem vídeo real de iPhone aferido com padrão independente.','body'),
          PageBreak()]

    # PAGE 3 - METHODOLOGY
    S += [para('02  |  Arquitetura e métodos','h1'),
          para('Pipeline de visão computacional','h2'),
          sheet([['Etapa','Operação e justificativa'],
                 ['1. Aquisição','VideoCapture lê MP4/MOV; imdecode lê JPG/PNG; não exige webcam.'],
                 ['2. Calibração','ROI manual delimita interior do recipiente; topo=altura máxima e base=zero.'],
                 ['3. Cor','BGR→HSV; azul por matiz, café escuro por luminância baixa (canal V).'],
                 ['4. Segmentação','inRange isola cor azul ou pixels com V ≤ 115 (perfil café).'],
                 ['5. Morfologia','Abertura remove pequenas manchas; fechamento repara lacunas da máscara.'],
                 ['6. Superfície','Primeira sequência de 5 linhas com ≥53% de máscara na ROI.'],
                 ['7. Saída','Estimativa em cm, estado NORMAL/ATENÇÃO/CRÍTICO e sobreposição do resultado.']],
                [121,WIDTH-121]),
          Spacer(1,16),
          para('Conversão geométrica de pixels para centímetros','h2'),
          para('<b>altura_estimada (cm) = [ (y_base − y_superficie) / (y_base − y_topo) ] × altura_maxima_cm</b>','quote'),
          para('Considera-se projeção frontal aproximada e escala linear; cada foto requer ROI calibrada individualmente se o enquadramento mudar. O copo afunilado e translúcido, a régua segura à mão, a espuma e a perspectiva introduzem incerteza.','body'),
          para('Estados do protótipo','h2'),
          sheet([['Estado','Regra na escala simulada de 0 a 100 cm'],
                 ['NORMAL','nível < 40 cm'],
                 ['ATENÇÃO','40 cm ≤ nível < 70 cm'],
                 ['CRÍTICO','nível ≥ 70 cm'],
                 ['SEM LEITURA','Não há máscara consistente; não equivale a nível de água zero.']],
                [121,WIDTH-121]),
          Spacer(1,10),
          para('Os limites foram definidos exclusivamente para a demonstração, e não representam critérios hidrológicos oficiais. Na calibração de 20 cm, são escalados para 8 e 14 cm.','small'),
          PageBreak()]

    # PAGE 4 - eval
    S += [para('03  |  Protocolo de avaliação','h1'),
          para('Base de dados e controles','h2'),
          para('Foi produzido um conjunto <b>sintético</b> de 92 imagens (23 níveis × 4 condições) e um vídeo de 180 quadros, com régua vertical, superfície azul e pequenas perturbações visuais. O gabarito registra altura e condição. A geração utiliza sementes definidas no código para reprodução dos testes.','body'),
          sheet([['Condição','Quantidade','Mudança inserida no gerador'],
                 ['Padrão','23','Cena iluminada com água azul e pequenas ondulações'],
                 ['Pouca luz','23','Escurecimento global'],
                 ['Chuva','23','Traços simulando chuva e ruído aleatório'],
                 ['Reflexos','23','Manchas luminosas na superfície']],
                [119,76,WIDTH-195]),
          Spacer(1,16),
          para('Métricas calculadas','h2'),
          para('<b>MAE</b> = média do módulo do erro de nível em centímetros. <b>RMSE</b> = raiz da média dos quadrados dos erros (penaliza erros elevados). <b>Acurácia de classe</b> = proporção de imagens com classificação correta. <b>Matriz de confusão</b> = distribuição entre classes reais e previstas.','body'),
          para('Conjunto e validade','h2'),
          para('Os indicadores MAE/RMSE/acurácia foram obtidos exclusivamente em imagens simuladas. As três fotos reais com café não têm medições físicas independentes usadas como gabarito; portanto, <b>não são incluídas nessas métricas</b>. Os três testes de fotografia são opcionais em um clone sem os originais privados. Não houve coleta em situação de alagamento.','body'),
          Spacer(1,15),
          para('Evidência visual: exemplo de estado de atenção','h2'),
          art('resultados/exemplo_atencao.png',maxw=WIDTH,maxh=208),
          PageBreak()]

    # PAGE 5 - results
    S += [para('04  |  Resultados quantitativos','h1'),
          sheet([['Indicador','Valor obtido (base sintética)'],
                 ['Amostras avaliadas',str(m['amostras'])],
                 ['MAE',f"{m['mae_cm']:.3f} cm"],
                 ['RMSE',f"{m['rmse_cm']:.3f} cm"],
                 ['Erro máximo',f"{m['erro_max_cm']:.2f} cm"],
                 ['Acurácia dos estados',f"{m['acuracia_classe']*100:.2f}% (91/92)"],
                 ['Testes automatizados','58 aprovados (incluindo perfil café)']],
                [WIDTH*.51,WIDTH*.49]),
          Spacer(1,14),
          para('Nível de referência × nível estimado','h2'),
          art('resultados/comparacao_niveis.png',maxw=WIDTH,maxh=185),
          Spacer(1,12),
          para('Matriz de confusão (classe de referência × classe prevista)','h2'),
          art('resultados/matriz_confusao.png',maxw=WIDTH,maxh=155),
          PageBreak()]

    # PAGE 6
    S += [para('05  |  Análise crítica','h1'),
          para('Interpretação dos achados','h2'),
          para('As leituras sintéticas ficaram próximas do gabarito e o sistema identificou os três estados do vídeo de demonstração. Houve <b>um erro de classe</b>: na amostra de reflexos com nível real de 40,00 cm, a estimação foi de 39,87 cm e gerou estado NORMAL em vez de ATENÇÃO. A diferença pequena na medida provocou uma mudança de classe no limiar, relevante do ponto de vista de alertas.','body'),
          art('resultados/erro_por_condicao.png',maxw=WIDTH,maxh=220),
          para('Limitações e vieses','h2'),
          para('<b>(1)</b> Apenas métricas quantitativas em imagens simuladas; <b>(2)</b> água azul e faixa HSV conhecidas, que não representam água turva; <b>(3)</b> ausência de estudo de reflexos extremos, oclusões, movimento de câmera ou lente; <b>(4)</b> limites de alerta arbitrários; <b>(5)</b> sem modelo temporal nem confirmação por sensor; <b>(6)</b> ausência de medição física independente da altura nas fotos reais.','body'),
          para('Próximos testes necessários','h2'),
          para('Filmar uma maquete retangular com o iPhone 13, câmera fixa e régua fixada; coletar amostras por altura, luz e ângulo; calibrar perfis para diferentes cores; reportar MAE/RMSE em vídeos reais separados de desenvolvimento; analisar erros próximos aos limiares; incluir zona de segurança, histerese e verificação de disponibilidade da leitura.','body'),
          PageBreak()]

    # PAGE 7 - ENSAIO COM FOTOGRAFIAS REAIS
    S += [para('06  |  Ensaio exploratório com café','h1'),
          para('O aluno <b>Felipe Mion de Andrade (RM 553715)</b> forneceu três fotografias de um copo translúcido com café, em níveis crescentes, com régua posicionada ao lado. A prova de conceito testa se um perfil de baixa luminosidade (HSV-V ≤ 115) consegue distinguir líquido escuro em uma ROI central do copo. O valor máximo de 8 cm foi assumido para cada ROI e as coordenadas foram ajustadas separadamente para cada foto.','body'),
          art('resultados/comparativo_cafe_3_fotos.png',maxw=WIDTH,maxh=238),
          Spacer(1,12),
          sheet([['Foto','Leitura estimada','Estado didático'],
                 ['01 - nível baixo','1,14 cm','NORMAL'],
                 ['02 - intermediário','2,49 cm','ATENÇÃO'],
                 ['03 - quase cheio','5,97 cm','CRÍTICO']],
                [WIDTH*.38,WIDTH*.27,WIDTH*.35]),
          Spacer(1,10),
          para('Critério de classes apenas para a maquete: atenção ≥ 2,0 cm e crítico ≥ 5,5 cm. O perfil café identifica pixels escuros, não a substância química café; objetos escuros dentro da ROI podem causar falsos positivos. A espuma desloca a borda aparente do líquido, e a régua não é lida automaticamente.','small'),
          para('<b>Interpretação:</b> o programa segmentou três regiões crescentes, coerentes com a sequência visual. Como não há altura real aferida para cada fotografia, não se pode afirmar a exatidão das estimativas, calcular erro real ou generalizar para alagamentos. Trata-se de validação funcional qualitativa com dados reais.','body'),
          PageBreak()]

    # PAGE 8
    S += [para('07  |  Aplicação, demonstração e conclusão','h1'),
          para('Como executar sem webcam','h2'),
          para('Após instalar as dependências de <b>requirements.txt</b>, execute a partir da raiz do repositório:','body'),
          sheet([['Ação','Comando'],
                 ['Demonstrar vídeo','python main.py --video data/demonstracao_simulada.mp4'],
                 ['Rodar testes','python -m pytest -q'],
                 ['Testar café (Windows)','TESTAR_CAFE_WINDOWS.bat'],
                 ['Gerar dataset','python scripts/gerar_amostras.py'],
                 ['Reavaliar resultados','python scripts/avaliar.py']],
                [142,WIDTH-142]),
          Spacer(1,15),
          para('Adaptação ao iPhone 13','h2'),
          para('Para o modo azul, gravar em 1080p/30 fps (H.264/MOV), fixar câmera e usar --video, --calibrar e --max-cm. Para o modo café escuro em fotos, usar --imagem, --liquido cafe e calibrar a ROI no copo. As fotos reais ilustram a detecção, mas não comprovam desempenho de campo.','body'),
          para('Conclusão','h2'),
          para('O AlagaVision integra fotos e vídeos, segmentação HSV (cor azul ou baixa luminância), morfologia matemática, medição geométrica, classificação e avaliação. As três fotos reais demonstram aplicabilidade inicial ao café escuro, mas a precisão medida permanece limitada ao conjunto sintético. Uso em segurança pública exigiria novos dados, sensores e validação de campo.','body'),
          para('Entregáveis e arquivos','h2'),
          para('README.md, main.py, src/vision.py, src/simulator.py, scripts/gerar_amostras.py, scripts/avaliar.py, tests/test_vision.py, data/ e resultados/. O projeto está organizado para versionamento no GitHub; <b>o repositório deve ser criado e enviado pelo(s) aluno(s)</b>.','body'),
          para('Referências','h2'),
          para('FIAP. Global Solution 2026.2 - CitizenTech. Enunciado disponibilizado à turma.','small'),
          para('ARNALDO JR. Cognitive Computing, Computer Vision and IoT Systems. Critérios da Global Solution 2026.2, disponibilizados à turma.','small'),
          para('OPEN SOURCE COMPUTER VISION LIBRARY (OpenCV). Documentação técnica. https://docs.opencv.org/4.x/','small'),
          para('UNITED NATIONS. Sustainable Development Goals. https://sdgs.un.org/goals','small'),
          Spacer(1,16),
          para('Aviso: protótipo acadêmico. Não utilize para tomada de decisão de emergência, evacuação ou alerta oficial.','small')]

    doc.build(S)
    print(f'Relatório gerado: {output}')


if __name__=='__main__':
    main()
