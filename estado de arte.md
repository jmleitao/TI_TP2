# Estado da arte: compressão sem perdas de ECG

## Contexto da fonte

A base **MIT-BIH ECG Compression Test Database** tem 168 registos curtos de 20,48 s, escolhidos para pôr desafios variados aos compressores, sobretudo aos com perdas. A literatura sem perdas é por isso feita quase toda noutras bases (MIT-BIH Arrhythmia, PTB, European ST-T), e os valores abaixo **não são diretamente comparáveis** com os vossos. Mudam o ritmo de amostragem, a resolução e a definição de razão de compressão (CR).

Em sinais biomédicos típicos, os métodos sem perdas ficam na ordem de 2:1, e a entropia da fonte impõe o limite. Uma revisão de 2019 nota que as técnicas sem perdas, muito usadas em domínios vizinhos, tiveram pouca aplicação em ECG, e os dispositivos costumam usar compressão com perdas.

## Arquitetura comum

Quase todos os codecs têm dois estágios: um preditor que remove correlação temporal (e espacial, entre canais) e um codificador estatístico dos resíduos. Os codificadores típicos são aritmético, Huffman e Golomb. É exatamente a lógica da vossa análise de entropia (predição de ordem 1 e 2).

## Famílias de métodos

**1. Compressores de uso geral (gzip, bzip2, LZMA, PPMd).** São usados como *baseline*. Não estão otimizados para sinais em *streaming*, por isso servem de referência. Um trabalho com transformações *block-sorting* para ECG mostrou que contextos curtos são melhores e que o método supera bzip2, gzip e Shorten.

**2. Codecs de áudio sem perdas (FLAC, MPEG-4 ALS, APE, TTA, ALAC).** Foram comparados com LZMA, Deflate, PPMd, bzip2 e gzip noutros sinais de forma de onda. Para vocês, o mais relevante é que o **formato WFDB já suporta FLAC** (formatos 508, 516 e 524, com 8, 16 ou 24 bits por amostra), com o limite de oito sinais por ficheiro e a mesma frequência de amostragem em todos. O formato 516 é, portanto, um *baseline* simples e comparável. O MPEG-4 ALS usa o erro de predição de cada canal e subtrai-lhe uma combinação linear dos erros de um canal de referência, e já foi aplicado a sinais biomédicos.

**3. Predição linear (fixa ou adaptativa) com Golomb-Rice ou Huffman.** É a família dominante.

- Predição linear adaptativa com Golomb-Rice adaptativo ao conteúdo e empacotamento em tempo real atingiu 2,83× (V1) e 2,77× (V2) em 48 registos da MIT-BIH.
- Um sistema de duplo modo (preditor de ordem 1 mais um preditor com *template* e de ordem 3, com modelação de erro por contexto) atingiu CR de 2,975 a 3,040 na MIT-BIH.
- Uma predição adaptativa baseada no erro, com Golomb-Rice modificado, deu CR médio de 3,16, 3,75 e 3,52 nas bases PTB, European ST-T e MIT-BIH. As conclusões concordam com trabalhos anteriores em que a ordem 2 é adequada, o que bate com o que mediram.
- Há também soluções muito simples, como preditor de ordem zero com codificação RAKE, que passam de 2,67, e um preditor de declive linear com empacotamento de 16 bits fixos, que dá 2,25 na MIT-BIH. Este último trabalho refere que também testou a base de compressão de 168 registos, mas não vi o valor obtido.

**4. Preditores não lineares (redes neuronais).** Um preditor MLP seguido de codificadores entrópicos melhorou cerca de 11% a eficiência face a preditores lineares. Nesse estudo, a melhor combinação foi MLP com Huffman, e o aritmético precisou de mais bits por amostra do que o Huffman.

**5. Redundância entre derivações.** É importante para vocês, que têm duas. Um esquema multicanal com predição inter-canal e intra-canal atingiu 4,073 na PTB (multicanal), contra 2,809 na MIT-BIH (canal único). Há ainda trabalho dedicado a sinais de dois canais, avaliado em ECG e codificação conjunta de canais fisicamente próximos. Um algoritmo recente, QOE, tem avaliação na MIT-BIH e na PTB.

**6. Transformadas, wavelets e correlação entre batimentos.** Há codecs wavelet de compressão com perdas até sem perdas, comparados com SPIHT, e redução de correlação inter-canal por transformada para ECG multi-derivação sem perdas, com eficiência acima dos compressores de uso geral. A redundância 2D inter-batimento e intra-batimento também foi explorada em compressão sem perdas.

**7. Modelação de contexto e codificação aritmética.** A codificação aritmética adapta-se bem a probabilidades dependentes do contexto e aproxima-se do limite teórico se o modelo for bom. Há compressão neural e baseada em modelos de linguagem noutros domínios, mas **não encontrei resultados ECG sem perdas recentes com esses métodos**, e a maior parte dos trabalhos que vi vai até 2023.

## Aplicabilidade à vossa fonte

| Abordagem | Adequação | Porquê |
 | --- | --- | --- |
| gzip / bzip2 / LZMA | Só *baseline* | Dicionários e blocos têm pouco com que trabalhar em 5120 amostras por derivação |
| FLAC (WFDB 516) | *Baseline* forte | Predição linear mais Rice, já suportado pelo WFDB |
| LP fixa ou adaptativa + Golomb-Rice | **Primeira escolha** | Simples, com CR na ordem de 2,5 a 3 |
| + modelação de erro por contexto + codificação aritmética | Extensão natural | Capta estatísticas que o Rice não capta |
| Predição inter-derivação (derivação 1 a partir da 0) | **Muito promissora** | Têm exatamente 2 derivações |
| Redes neuronais / *template* por batimento | Opcional | Mais complexas, e com registos curtos pode haver pouco treino |

Uma implicação prática do vosso dataset: cada `.dat` tem só cerca de 15 KB, por isso o **custo do cabeçalho e dos parâmetros** pesa. É aqui que a divisão ajuda, porque podem treinar coeficientes e tabelas de códigos no conjunto de desenvolvimento e avaliar no de teste.

## Como isto se liga aos vossos resultados

A entropia do erro de predição, de 5,0 a 5,4 bits/amostra, equivale a um CR teórico de cerca de 2,2 a 2,4 (12 bits a dividir por esse valor). Isso fica na zona baixa dos valores da literatura (2,25 a 3,0 na MIT-BIH). É um limite para um modelo sem memória, e codecs adaptativos, com contexto ou com predição inter-derivação, podem ficar abaixo disso.

## Referências a verificar antes de citar

Confirmem autores, volumes e páginas nos originais, porque trabalhei com resumos:

- Moody, Mark, Goldberger. *Evaluation of the "TRIM" ECG data compressor*. Computers in Cardiology, 15:167–170, 1988 (artigo original da base).
- Revisão: *Lossless electrocardiogram signal compression: a review of existing methods*. Biomed. Signal Process. Control, 2019.
- Tsai e Kuo et al. IEEE Access, vol. 6, pp. 42207–42215, 2018.
- Jia et al. IEEE Access, vol. 8, pp. 101153–101162, 2020.
- Bannajak et al. Int. J. Environ. Res. Public Health, 20(3), 2753, 2023.
- Kannan e Eswaran. EURASIP J. Adv. Signal Process., 2007, 35641.
- Luo et al. IEICE Trans. Inf. Syst., E101.D(3), 791–794, 2018.
- Liebchen. *MPEG-4 ALS*. J. Acoust. Soc. Korea, 28(7), 2009.
- Documentação WFDB, *signal(5)* (formatos 212 e 508/516/524).

Se quiseres, escrevo esta secção em formato IEEE de ~1 coluna (em português ou inglês) com uma tabela de CR por método, ou preparo as referências em BibTeX.
