# Guia de apresentação - AlagaVision

**Aluno: Felipe Mion de Andrade — RM 553715**

## 1. Antes de começar a aula

- [x] Nome e RM inseridos no README e no relatório PDF.
- [ ] Coloque todos os arquivos no repositório da equipe, com acesso configurado conforme o pedido do professor.
- [ ] Instale as dependências, rode `python -m pytest -q` e confirme 58 testes aprovados.
- [ ] Rode `python main.py --video data/demonstracao_simulada.mp4` antes da aula.
- [ ] Se tiver um vídeo do iPhone 13, teste em casa a calibração, o codec e a leitura de todos os quadros.
- [ ] Deixe o `resultados/video_processado.mp4` pronto para apresentar caso haja problema com Python/ambiente.

## 2. Demonstração de 3 a 4 minutos

**0:00–0:40 | Problema:** monitoramento acessível do nível da água em um ponto conhecido. A proposta está associada a CitizenTech e ODS 11, 9 e 13.

**0:40–1:15 | Método:** quadro do vídeo -> região de interesse -> conversão BGR para HSV -> segmentação por azul ou por pixels escuros -> morfologia -> estimativa em cm -> classificação.

**1:15–2:30 | App:** no terminal do repositório, execute:

```bash
python main.py --video data/demonstracao_simulada.mp4
```

Mostre o nível subindo (NORMAL -> ATENÇÃO -> CRÍTICO), depois caindo. Diga que o vídeo é **sintético**, preparado para uma demonstração reproduzível e sem câmera.

**2:30–3:00 | Fotos do café:** mostre `resultados/comparativo_cafe_3_fotos.png`. As fotos reais foram analisadas com `--liquido cafe` e deram 1,14 cm (NORMAL), 2,49 cm (ATENÇÃO) e 5,97 cm (CRÍTICO) com limites didáticos de 2 e 5,5 cm. Sem medição física de referência, não afirme precisão real.

**3:00–3:30 | Resultados:** abra `resultados/comparacao_niveis.png`, `resultados/matriz_confusao.png` e `resultados/metricas.json`. Informe: 92 casos simulados, MAE 0,389 cm, RMSE 0,573 cm, acurácia de classes 98,91% (91/92).

**3:30–4:00 | Limitações:** o modo azul exige cor controlada e o modo café segmenta baixa luminosidade; ambas as versões exigem ROI calibrada. Dados sintéticos e três fotos com café **não** validam desempenho em alagamentos reais.

## 3. Perguntas técnicas prováveis

**Por que OpenCV?** Permite ler vídeo quadro a quadro e aplicar segmentação por cor sem treinar modelos. É adequado para um protótipo controlado e explicável.

**O que é ROI?** É uma região retangular da imagem onde a água e a escala estão monitoradas; exclui o restante do cenário e reduz falsos positivos.

**O que é HSV?** Representação em matiz, saturação e brilho, útil para selecionar pixels com uma faixa de cor, menos dependente do valor absoluto de cada canal BGR.

**Como mede o nível em cm?** Pela posição vertical da primeira sequência consistente de pixels da cor selecionada e pela altura real conhecida da região: `(base_y - nivel_y) / (base_y - topo_y) * altura_maxima_cm`.

**Por que abertura e fechamento morfológicos?** Abertura retira pequenas manchas isoladas; fechamento preenche pequenas falhas e reduz interrupções na máscara.

**O que significa o limiar de 53%?** Uma linha precisa ter ao menos 53% da largura da ROI azul, repetido por cinco linhas, antes de ser aceita como superfície. São hiperparâmetros empíricos da maquete.

**O que é MAE?** Média do valor absoluto do erro entre medição estimada e referência em cm. RMSE penaliza mais erros grandes.

**A acurácia de 98,91% é sobre enchentes reais?** Não. Somente sobre 92 imagens sintéticas, geradas com regras e cores similares às esperadas pelo detector. Não permite afirmar desempenho em ambiente externo.

**Por que um erro na matriz de confusão?** Em um caso real de 40 cm simulados, o algoritmo estimou 39,87 cm, abaixo do limiar exato. É uma falha de classificação de um caso limítrofe e reforça a necessidade de margens de alerta.

**O projeto precisa de câmera ligada ao PC?** Não. O OpenCV carrega MP4/MOV e analisa quadros de vídeo. Pode ser uma gravação feita com iPhone 13.

**Como evitar que não detectar água seja interpretado como seguro?** Na ausência de uma máscara consistente, o algoritmo retorna `SEM LEITURA`, não assume 0 cm.

**Como funciona o perfil café?** O café dessas fotos é quase preto. O OpenCV isola pixels com luminosidade HSV-V baixa (até 115 por padrão) dentro do copo, aplica morfologia e localiza a primeira faixa com cobertura suficiente. Não é reconhecimento de substância: objetos escuros podem confundir.

**As três fotos de café comprovam precisão real?** Não. São um teste funcional visual de níveis crescentes, sem gabarito metrológico independente. O erro médio apresentado vale apenas para dados sintéticos.

**Como o projeto avançaria?** Gravações controladas de recipientes e réguas com iPhone 13, diversidade de cenários, calibração/normalização de cor, avaliação separada de treino/teste, dados reais e, só depois de validados, sensor adicional e revisão por especialistas.

## 4. Conversão de vídeos iPhone incompatíveis

Em Ajustes -> Câmera -> Formatos -> Mais Compatível, o iPhone pode gravar H.264 em MOV. Caso o OpenCV não abra, converta para MP4/H.264:

```bash
ffmpeg -i data/video_iphone.mov -c:v libx264 -pix_fmt yuv420p -an data/video_iphone.mp4
```
