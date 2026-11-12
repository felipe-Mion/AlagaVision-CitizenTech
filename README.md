# AlagaVision | CitizenTech (FIAP Global Solution 2026.2)

**Protótipo didático de visão computacional que estima o nível de água em vídeos ou fotografias de uma área calibrada e classifica o risco visual.** O objetivo é explorar monitoramento de pontos de alagamento com recursos acessíveis. A solução **não é um sistema de Defesa Civil**, não prevê enchentes, não está certificada e não substitui avisos oficiais.

> **Não precisa de webcam.** Funciona diretamente com o MP4 demonstrativo incluído, com **fotos JPG/PNG** e também com vídeos do **iPhone 13** (MOV/H.264 ou MP4). O modo padrão detecta água **azul** e o modo opcional `--liquido cafe` detecta **líquidos escuros** em uma ROI calibrada. Em vídeos, a câmera deve permanecer fixa.

## Integrantes

| Nome | RM |
| --- | --- |
| **Felipe Mion de Andrade** | **553715** |

> Integrante informado: Felipe Mion de Andrade (RM 553715).

## 1. O problema e o cidadão beneficiado

Pontos sujeitos a alagamentos podem ser difíceis de monitorar continuamente. O protótipo apresenta um método de baixo custo para estimar visualmente a altura de água em uma **régua/recipiente de referência**. O público-alvo conceitual são moradores, gestores de espaços comunitários e equipes de manutenção, que poderiam dispor de medidas adicionais de apoio à observação **após validação em campo**.

**Tema CitizenTech**: tecnologia acessível para uma necessidade cotidiana. **ODS alinhados**: ODS 11 (cidades sustentáveis), ODS 9 (infraestrutura/inovação), ODS 13 (adaptação climática).

## 2. Evidências incluídas

- **Três fotos reais com café** enviadas pelo aluno (`data/fotos_cafe`) e resultados anotados (`resultados/comparativo_cafe_3_fotos.png`). As medidas são exploratórias e não possuem gabarito físico independente.
- **92 imagens sintéticas** com valores de referência conhecidos, em quatro condições simuladas: padrão, pouca luz, chuva e reflexos (`data/amostras`, `data/gabarito.csv`).
- **Vídeo demonstrativo sintético** com progressão e redução da lâmina de água (`data/demonstracao_simulada.mp4`).
- **Vídeo já processado** com nível, linha detectada e estado (`resultados/video_processado.mp4`).
- **Leituras por quadro**, gabarito, predições, quatro gráficos/exemplos e métricas (`resultados/`).
- **Relatório técnico** pronto para personalização (`relatorio/AlagaVision_Relatorio_GS.pdf`).

### Desempenho no conjunto sintético (não validado em ambiente real)

| Indicador | Resultado |
| --- | ---: |
| Imagens avaliadas | **92** |
| Erro absoluto médio - MAE | **0,389 cm** |
| Raiz do erro quadrático médio - RMSE | **0,573 cm** |
| Erro máximo absoluto | **2,29 cm** |
| Acurácia de estado (Normal / Atenção / Crítico) | **98,91% (91/92)** |
| Testes automatizados (incluindo perfil café) | **58 aprovados** |

Valores gerados pelo avaliador sobre imagens **totalmente sintéticas**, com os mesmos elementos visuais e cores projetados para o algoritmo. **Não é válido extrapolar** a precisão para a água real, câmeras diferentes ou condições meteorológicas reais. Em uma imagem exatamente no limiar de **40 cm**, o sistema estimou **39,87 cm** e classificou `NORMAL` em vez de `ATENCAO`, o que ilustra a necessidade de margem de segurança e testes adicionais.

## 3. Tecnologias e pipeline

**Python 3.10+**, OpenCV, NumPy, Matplotlib, Pytest, ReportLab e Pillow (para gerar o PDF). Não é utilizado modelo de ML ou serviço externo.

1. OpenCV lê quadros de vídeo (`VideoCapture`) ou uma fotografia (`imdecode`).
2. O usuário calibra a região de interesse (ROI) que corresponde à escala física (`--calibrar`, `--max-cm`).
3. Converte BGR em HSV (`cvtColor`).
4. Por padrão, aplica uma máscara para tons azuis (`inRange`); em `--liquido cafe` seleciona pixels escuros com brilho HSV V ≤ 115. Isso não identifica café semanticamente, apenas regiões escuras dentro da ROI.
5. Remove ruído por abertura/fechamento morfológico (`morphologyEx`).
6. Calcula a proporção de pixels selecionados em cada linha da ROI. A superfície é a primeira linha com pelo menos **53%** de cobertura, sustentada por **5** linhas consecutivas.
7. Converte a coordenada da superfície em centímetros, assumindo câmera fixa e escala linear. Exemplo: `nivel_cm = (y2 - y_superficie) / (y2 - y1) * altura_maxima_cm`.
8. Classifica em **NORMAL** (`< 40 cm`), **ATENÇÃO** (`>= 40 cm`) e **CRÍTICO** (`>= 70 cm`); são **limiares de demonstração**, não valores oficiais ou universais.
9. Sobrepõe a linha e o status à imagem, exportando JPG/PNG para foto ou MP4 para vídeo, além de CSV. Quando não há segmentação consistente, informa **SEM LEITURA** (não supõe nível zero).

Os valores 40 e 70 cm correspondem à escala simulada padrão de 100 cm. Com `--max-cm 20`, o aplicativo **escala os limiares automaticamente** para 8 e 14 cm. É possível sobrescrevê-los por `--atencao-cm` e `--critico-cm`. 

## 4. Instalação

**macOS (opcional):**

```bash
cd AlagaVision_CitizenTech
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows / PowerShell (recomendado):**

```powershell
cd AlagaVision_CitizenTech
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não é preciso ativar o ambiente no PowerShell. Para executar o projeto, use `.\.venv\Scripts\python.exe main.py ...`.

### Demonstração pronta (recomendada para a aula)

```bash
python main.py --video data/demonstracao_simulada.mp4
```

Abre uma janela que mostra a água subindo e descendo. Pressione `Q` para encerrar. Os valores de cada quadro são salvos em `resultados/leituras_demo.csv`.

Para salvar um novo vídeo processado e o CSV **sem abrir uma janela**:

```bash
python main.py --video data/demonstracao_simulada.mp4 \
  --no-display --output resultados/minha_execucao.mp4 --csv resultados/minha_execucao.csv
```

No Windows, coloque o comando acima **em uma única linha**, sem as barras `\` de quebra de linha.

### Analisar uma FOTO do iPhone 13 (JPG ou PNG)

Coloque uma fotografia tirada de frente na pasta `data/` (exemplo: `data/copo.jpg`). Use corante **azul** na água e posicione uma régua ao lado de um recipiente transparente de paredes retas. **O software não lê automaticamente os números da régua**: você seleciona com o mouse uma faixa vertical dentro do copo, com o topo e a base correspondendo à distância física declarada em `--max-cm`. A foto serve como medição pontual; não permite acompanhar a subida da água ao longo do tempo.

**Windows / PowerShell (funciona sem ativar o ambiente virtual):**

```powershell
.\.venv\Scripts\python.exe main.py --imagem data/copo.jpg --calibrar --max-cm 12 --output resultados/copo_analisado.jpg --csv resultados/copo_leitura.csv
```

Ajuste `12` para **a distância real em centímetros entre o topo e a base da região selecionada**. Arraste um retângulo vertical dentro do copo, ao lado da régua, cobrindo toda a faixa por onde a água pode subir (não selecione só a água atualmente visível). Pressione `Enter` e depois qualquer tecla para fechar a janela. O programa salvará a foto com o nível estimado e o status. Na primeira execução, a calibração será salva em `calibracao_iphone.json`.

Para reutilizar a mesma foto e a calibração, retire `--calibrar`. Para uma outra foto com dimensões/enquadramento diferentes, **calibre novamente**. Use `--no-display` para produzir os arquivos sem exibir a janela.

Para testar o modo de foto sem celular, execute este exemplo do conjunto de teste, com a ROI sintética padrão:

```powershell
.\.venv\Scripts\python.exe main.py --imagem data/amostras/chuva_16_070cm.jpg --no-display --output resultados/exemplo_foto.jpg
```

O iPhone normalmente usa HEIC em modo de alta eficiência; em **Ajustes → Câmera → Formatos → Mais Compatível**, novas fotos são salvas como JPEG. Se sua foto estiver em HEIC, converta-a para JPG antes de rodar o programa.

**Observação:** os estados NORMAL/ATENÇÃO/CRÍTICO são faixas relativas da escala escolhida e não correspondem a riscos reais de enchente. Em fotos reais, faça testes com régua e várias alturas antes de confiar na precisão.

### Testes e reprodutibilidade

```bash
python -m pytest -q
python scripts/gerar_amostras.py
python scripts/avaliar.py
```

A primeira linha executa 58 testes; as seguintes recriam o conjunto de imagens/vídeo **simulados**, o CSV de predições e os indicadores/gráficos do relatório. A geração é reprodutível por sementes fixas. O vídeo pode ter pequenas variações de codec/arquivo entre sistemas.


## 4A. Teste com três fotos reais de café (Windows)

**Felipe Mion de Andrade — RM 553715.** Três fotografias do iPhone 13 foram adicionadas como ensaio controlado com café escuro em um copo plástico translúcido. O perfil `--liquido cafe` usa **baixa luminosidade (HSV-V)**, não um detector treinado de líquidos. A ROI deve ficar **dentro do copo**, sem incluir bancada, régua ou fundo escuro. O mesmo algoritmo de superfície e conversão geométrica estima o nível.

**Com a pasta do projeto aberta no PowerShell**, use este comando para testar a primeira foto: 

```powershell
.\.venv\Scripts\python.exe main.py --imagem data/fotos_cafe/cafe_01.png --liquido cafe --roi 270 705 378 1134 --max-cm 8 --atencao-cm 2 --critico-cm 5.5 --output resultados/cafe_01_analisada.jpg --no-display
```

Para as três fotos, **dê duplo clique em `TESTAR_CAFE_WINDOWS.bat`** (após criar o `.venv` e instalar as dependências). As ROI numéricas foram configuradas exclusivamente para os arquivos fornecidos neste ZIP, com resolução 900×1600; fotos transferidas em resolução diferente exigem nova calibração.

| Foto de teste | Leitura exploratória | Classificação demonstrativa |
| --- | ---: | --- |
| `cafe_01.png` — pouco café | **1,14 cm** | NORMAL |
| `cafe_02.png` — intermediário | **2,49 cm** | ATENÇÃO |
| `cafe_03.png` — quase cheio | **5,97 cm** | CRÍTICO |

A faixa `ATENÇÃO ≥ 2,0 cm` e `CRÍTICO ≥ 5,5 cm` foi escolhida apenas para **mostrar as três classificações no copo**, e **não** constitui limite oficial de segurança. A altura máxima da ROI foi assumida em 8 cm para este exercício. **Não foram medidos fisicamente os três níveis exatos com referência independente.** Portanto, não se pode atribuir precisão em centímetros nem calcular erro real a partir dessas três leituras. O copo com ranhuras, a espuma, a régua segurada manualmente e a perspectiva podem causar erros.

Para a **sua próxima foto**, sem coordenadas pré-configuradas, use:

```powershell
.\.venv\Scripts\python.exe main.py --imagem data/meu_cafe.jpg --liquido cafe --calibrar --max-cm 8 --atencao-cm 2 --critico-cm 5.5 --output resultados/meu_cafe_resultado.jpg
```

Arraste uma faixa vertical dentro do copo, cuja altura corresponda à distância real informada em `--max-cm` (meça-a na régua). Não selecione somente o volume do café; inclua também a porção vazia até a marca superior. Com fotos de enquadramentos diferentes, execute `--calibrar` novamente. Se a iluminação mudar muito, pode-se ajustar `--limiar-cafe` (padrão 115; faixa de 0 a 255). Valores altos aumentam o risco de falsos positivos.

**Privacidade e reprodutibilidade para o GitHub:** os arquivos originais de `data/fotos_cafe` estão no `.gitignore` por mostrarem um ambiente doméstico; acompanham o ZIP, mas não serão incluídos automaticamente pelo Git. Sem as três fotos, o Pytest executa **55 testes e pula 3 testes opcionais**. O PDF e as imagens anotadas em `resultados/` também mostram partes do ambiente e **devem ser revisados antes de publicar o repositório**. Caso queira reproduzir os 58 testes no GitHub, publique as fotos apenas após avaliar a privacidade.

## 5. Gravar e analisar com o iPhone 13 (sem webcam)

**Preparação da gravação:**

1. No iPhone 13, em **Ajustes → Câmera → Formatos**, selecione **Mais Compatível** (codificação H.264, geralmente em contêiner `.MOV`). Grave em **1080p a 30 fps**.
2. Faça uma maquete: um recipiente transparente **retangular**, frente plana, com água colorida de azul usando corante alimentício. Use fundo claro/neutro e iluminação constante. Coloque ao lado uma régua física com a graduação de `0 a 20 cm` visível e fixe o iPhone em um apoio.
3. Enquadre de frente e deixe a câmera **imóvel**. Grave a água sendo adicionada e depois retirada; evite rosto ou dados pessoais.
4. Transfira o vídeo para o Mac pelo **AirDrop** ou cabo, ou para o Windows via cabo/iCloud. Ponha o arquivo em `data/video_iphone.mov` (crie a pasta, se necessário).
5. Rode o comando abaixo. Quando a janela de calibração abrir, **arraste um retângulo somente na faixa onde a água azul aparece**, com topo na altura da marca de 20 cm e base na marca de 0 cm (dentro da face frontal do recipiente). Aperte `Enter`:

```bash
python main.py --video data/video_iphone.mov --calibrar --max-cm 20 \
  --output resultados/iphone_processado.mp4 --csv resultados/iphone_leituras.csv
```

6. Para repetir no mesmo vídeo, sem recalibrar, use o JSON salvo:

```bash
python main.py --video data/video_iphone.mov --config calibracao_iphone.json \
  --output resultados/iphone_processado.mp4
```

**Importante para alerta em escala de 20 cm:** o aplicativo converte automaticamente os patamares didáticos para `ATENÇÃO >= 8 cm` e `CRÍTICO >= 14 cm`. Você também pode ajustar com `--atencao-cm 8 --critico-cm 14` ou com outros valores adequados à sua maquete. Esses limiares são apenas demonstrativos.

**Se um `.MOV` não abrir:** alguns vídeos HEVC/H.265 não têm decoder compatível no OpenCV da máquina. Converta para H.264/MP4, por exemplo com FFmpeg:

```bash
ffmpeg -i data/video_iphone.mov -c:v libx264 -pix_fmt yuv420p -an data/video_iphone.mp4
```

O protótipo tem perfis para um **alvo azul controlado** e para **café escuro**, mas não detecta toda e qualquer água de enchente. Sua resposta real depende do enquadramento, iluminação, reflexos, cor da água, geometria da régua e parâmetros HSV. Sempre use o vídeo de demonstração para uma apresentação garantida.

## 6. Estrutura de diretórios

```text
AlagaVision_CitizenTech/
├── main.py                     # CLI: ler vídeo ou foto, calibrar ROI, anotar, exportar
├── src/
│   ├── vision.py               # segmentação, medição, estados e anotação
│   └── simulator.py            # cenas artificiais para experimentos
├── scripts/
│   ├── gerar_amostras.py       # gera 92 imagens, gabarito e vídeo sintético
│   ├── avaliar.py              # MAE, RMSE, acurácia, matriz e gráficos
│   └── gerar_relatorio.py      # criar PDF com nomes e RMs
├── tests/test_vision.py        # testes de erro, limites e falha segura
├── data/                       # gabarito, imagens e vídeo sintético
├── resultados/                 # evidências, CSV, JSON, PNG e MP4
├── relatorio/                  # relatório técnico em PDF
├── GUIA_APRESENTACAO.md        # roteiro e perguntas para apresentação
└── requirements.txt
```

## 7. Riscos, limites e evolução

- **Somente validação sintética:** imagens geradas por computador não substituem teste físico ou monitoramento real. O novo modo de foto foi testado com imagens sintéticas; não existem ainda métricas de acurácia obtidas com fotos do iPhone.
- **Geometria rígida:** câmera e escala devem permanecer imóveis, planas e sem distorção relevante. A medição é aproximada.
- **Cores especializadas:** água comum não é necessariamente azul; a técnica pode falhar em água turva ou reflexos intensos.
- **Leitura indisponível:** falha na segmentação produz `SEM LEITURA`; não significa ausência de perigo.
- **Classificação experimental:** os limiares são escolhidos por finalidade didática, não têm respaldo hidrológico.
- **Futuro:** avaliar amostras do iPhone 13 com níveis medidos por régua, comparar acurácia/erro por condição real, validar alertas com histerese, adicionar sensores físicos, monitoramento de confiabilidade e proteção de dados.

**Não use este protótipo para orientar evacuações ou decisões de segurança. Siga a Defesa Civil e alertas públicos oficiais.**

## 8. O que entregar

1. Subir estes arquivos ao GitHub (repositório criado por sua equipe; não foi publicado automaticamente).
2. Informar o link do repositório na Plataforma/Teams indicada pelo professor.
3. Gerar a versão final personalizada do PDF com seus dados: `python scripts/gerar_relatorio.py --integrantes "Felipe Mion de Andrade (RM 553715)` e conferir o arquivo em `relatorio/`.
4. Na aula, demonstrar `python main.py --video data/demonstracao_simulada.mp4` e mostrar `resultados/metricas.json`, gráficos e `resultados/predicoes.csv`.
5. Revisar os fundamentos para a arguição individual: ROI, HSV, limiar, morfologia, conversão pixel/cm, MAE, RMSE, matriz de confusão e limitações.

### Referências de escopo

- FIAP, *Global Solution 2026.2 - CitizenTech*, enunciado geral fornecido pela turma.
- Arnaldo Jr., *Cognitive Computing, Computer Vision and IoT Systems*, critérios de entrega da disciplina fornecidos pela turma.
- Exemplos de aula `cp-pdi-nave-main` e `cp-pdi-cartas-main`, usados como referência de vídeo com `cv2.VideoCapture`, não como solução copiada.
- OpenCV, documentação: https://docs.opencv.org/4.x/
- Nações Unidas, Objetivos de Desenvolvimento Sustentável: https://sdgs.un.org/goals
