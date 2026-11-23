# Trabalho Prático 2 - CODEC

## Descrição

Desenvolvimento de um CODEC para compressão sem perdas de sinais ECG, explorando diferentes métodos de codificação e técnicas de predição.

## Arranque

Para executar o programa:

```bash
python main.py
```

Para executar o programa e copiar os ficheiros do dataset para as pastas de desenvolvimento e teste:

```bash
python main.py --copiar
```

Para definir uma semente específica para a divisão dos dados:

```bash
python main.py --copiar --semente 7
```

A opção `--copiar` copia os ficheiros para:

```text
Dataset_split/
├── desenvolvimento/
└── teste/
```

A opção `--semente` permite definir a semente utilizada na divisão dos registos, garantindo a reprodutibilidade das experiências.

## Métodos de compressão

Os métodos atualmente implementados são:

- Huffman aplicado diretamente ao sinal;
- Predição de ordem 2 seguida de Huffman;
- Predição de ordem 2 seguida de Golomb-Rice.

## Análise experimental

São calculadas estatísticas e entropias dos sinais ECG, sendo os métodos comparados através de:

- Bits por amostra;
- Compression Ratio (CR);
- Tempo de codificação;
- Tempo de descodificação;
- Reconstrução exata do sinal original.

O parâmetro \(k\) do codificador Golomb-Rice é selecionado experimentalmente com os dados de desenvolvimento.

## Organização dos ficheiros

```text
projeto/
├── main.py
├── huffmancodec.py
├── ecg_rice.py
├── resultados.md
├── README.md
├── Dataset/
└── Dataset_split/
    ├── desenvolvimento/
    └── teste/
```

## Resultados

Os resultados das experiências encontram-se documentados em [resultados.md](resultados.md).

**Estado atual:** experiências e seleção de parâmetros realizadas exclusivamente com o conjunto de desenvolvimento. O conjunto de teste fica reservado para a avaliação final.