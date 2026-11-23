# Resultados da análise e compressão (conjunto de desenvolvimento)

**Configuração:** semente 42 · 168 registos no total · 84 de desenvolvimento · 84 de teste · 430 080 amostras por derivação · 12 bits/amostra sem compressão.

## Estatísticas dos dados

| | Derivação 0 | Derivação 1 |
| --- | ---: | ---: |
| Valor mínimo | −807 | −865 |
| Valor máximo | 963 | 1091 |
| Símbolos distintos | 1550 | 1500 |

## Entropia (bits/amostra)

| Medida | Derivação 0 | Derivação 1 |
| --- | ---: | ---: |
| H(X) | 8.4025 | 8.3251 |
| H(X₁,X₂)/2 (pares) | 6.5736 | 6.4487 |
| H(erro), predição de ordem 1 | 5.3621 | 5.0182 |
| H(erro), predição de ordem 2 | 5.1196 | 4.9652 |

## Resultados dos métodos de compressão

### Derivação 0

| Método | Bits/amostra | Compression Ratio | Codificação (s) | Descodificação (s) |
| --- | ---: | ---: | ---: | ---: |
| Huffman por registo | 16.3298 | 0.735 | 0.553 | 1.052 |
| Ordem 2 + Huffman | 7.5106 | 1.598 | 0.281 | 1.026 |
| Ordem 2 + Golomb-Rice | **5.4155** | **2.216** | 1.268 | 1.195 |

### Derivação 1

| Método | Bits/amostra | Compression Ratio | Codificação (s) | Descodificação (s) |
| --- | ---: | ---: | ---: | ---: |
| Huffman por registo | 14.9987 | 0.800 | 0.396 | 0.866 |
| Ordem 2 + Huffman | 6.5348 | 1.836 | 0.198 | 0.776 |
| Ordem 2 + Golomb-Rice | **5.0614** | **2.371** | 1.090 | 1.012 |

### Tamanho dos dados comprimidos

| Método | Derivação | Payload (bytes) | Modelo/metadados (bytes) |
| --- | --- | ---: | ---: |
| Huffman por registo | 0 | 423251 | 454638 |
| Ordem 2 + Huffman | 0 | 272469 | 131303 |
| Ordem 2 + Golomb-Rice | 0 | 290840 | 336 |
| Huffman por registo | 1 | 409325 | 397005 |
| Ordem 2 + Huffman | 1 | 265243 | 86068 |
| Ordem 2 + Golomb-Rice | 1 | 271796 | 336 |

## Seleção do parâmetro Golomb-Rice

O parâmetro \(k\) foi escolhido exclusivamente com os dados de desenvolvimento, testando valores entre 0 e 12.

**Parâmetro selecionado: k = 3 para ambas as derivações.**

Comprimento do código em bits por amostra, sem cabeçalho nem padding:

| k | Derivação 0 | Derivação 1 |
| ---: | ---: | ---: |
| 0 | 15.3993 | 12.5702 |
| 1 | 8.9697 | 7.5520 |
| 2 | 6.2515 | 5.5433 |
| 3 | **5.4093** | **5.0551** |
| 4 | 5.5229 | 5.3446 |
| 5 | 6.1672 | 6.0776 |
| 6 | 7.0597 | 7.0191 |
| 7 | 8.0170 | 8.0026 |
| 8 | 9.0015 | 9.0001 |
| 9 | 10.0000 | 10.0000 |
| 10 | 11.0000 | 11.0000 |
| 11 | 12.0000 | 12.0000 |
| 12 | 13.0000 | 13.0000 |

## Observações preliminares

- A predição de ordem 2 melhora substancialmente os resultados de Huffman em ambas as derivações.
- A combinação de predição de ordem 2 com Golomb-Rice apresenta os melhores resultados entre os métodos avaliados.
- O parâmetro ótimo de Golomb-Rice foi \(k=3\) para ambas as derivações.
- A derivação 1 apresenta uma taxa de compressão ligeiramente superior à derivação 0.
- Huffman aplicado diretamente ao sinal apresenta um compression ratio inferior a 1, indicando que, com os tamanhos contabilizados, não consegue comprimir o sinal.
- Golomb-Rice apresenta um payload superior ao de Ordem 2 + Huffman, mas um custo de modelo/metadados muito inferior.

**Nota:** Todos os resultados desta secção foram obtidos exclusivamente no conjunto de desenvolvimento. O conjunto de teste permanece reservado para a avaliação final. Os tamanhos de payload e modelo/metadados devem ser contabilizados conjuntamente para determinar o tamanho comprimido total. A reconstrução exata dos sinais deve ser verificada para todos os métodos.
