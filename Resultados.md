# Resultados da análise de entropia (conjunto de desenvolvimento)

**Configuração:** semente 42 · 168 registos no total · 84 de desenvolvimento · 84 de teste · 430 080 amostras por derivação (12 bits/amostra sem compressão).

## Estatísticas dos dados

| | Derivação 0 | Derivação 1 |
| --- | --- | --- |
| Valor mínimo | −807 | −865 |
| Valor máximo | 963 | 1091 |
| Símbolos distintos | 1550 | 1500 |

## Entropia (bits/amostra)

| Medida | Derivação 0 | Derivação 1 |
| --- | --- | --- |
| H(X) | 8.4025 | 8.3251 |
| H(X₁,X₂)/2 (pares) | 6.5736 | 6.4487 |
| H(Xₙ \| Xₙ₋₁) | 4.8653 | 4.6686 |
| H(Xₙ \| Xₙ₋₁) com Miller-Madow | 4.9552 | 4.7395 |
| H(erro), predição de ordem 1 | 5.3621 | 5.0182 |
| H(erro), predição de ordem 2 | 5.1196 | 4.9652 |

## Observações

- A entropia de ordem 0, H(X) ≈ 8.3–8.4 bits, já é inferior aos 12 bits originais.
- A predição reduz a entropia para cerca de 5.0–5.4 bits/amostra, e a ordem 2 dá um ganho pequeno face à ordem 1.
- H(Xₙ | Xₙ₋₁) é o valor mais baixo, mas é um limite otimista: há muitos contextos possíveis para poucas amostras.
- H(X₁,X₂)/2 está provavelmente subestimada, pelo mesmo motivo (muitos pares raros).
