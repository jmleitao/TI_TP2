"""
Medições extra de entropia (conjunto de DESENVOLVIMENTO) usadas no relatório:
  - Tabela II : H(Xn | Xn-1), com e sem correção de Miller-Madow
  - Tabela IV : dependência entre os resíduos das duas derivações
  - Secção IV-C/E : entropia dos resíduos calculada por registo (média)

Uso (a partir da pasta Code/):  python entropia_extra.py
"""
from pathlib import Path
import numpy as np
from main import ler_registo


def entropia_empirica(simbolos, miller_madow=False):
    _, c = np.unique(simbolos, return_counts=True)
    N = c.sum()
    p = c / N
    H = -np.sum(p * np.log2(p))
    if miller_madow:                       # correção (K-1)/(2 N ln2)
        H += (len(c) - 1) / (2 * N * np.log(2))
    return float(H)


def entropia_condicional(anterior, atual, miller_madow=False):
    """H(Xn | Xn-1) = H(Xn-1, Xn) - H(Xn-1)."""
    conjunto = anterior.astype(np.int64) * 8192 + atual.astype(np.int64)
    return (entropia_empirica(conjunto, miller_madow)
            - entropia_empirica(anterior, miller_madow))


def residuo(x, ordem):
    return np.diff(x.astype(np.int64), n=ordem)


def main():
    base = Path(__file__).resolve().parent
    nomes = (base / "desenvolvimento.txt").read_text().split()
    regs = [ler_registo(base.parent / "Dataset" / f"{n}.dat") for n in nomes]
    print(f"Registos de desenvolvimento: {len(regs)}\n")

    print("== Tabela II: entropia condicional H(Xn|Xn-1) ==")
    for d in (0, 1):
        ant = np.concatenate([r[d][:-1] for r in regs])
        atu = np.concatenate([r[d][1:] for r in regs])
        print(f"Deriv. {d}: {entropia_condicional(ant, atu):.4f}  "
              f"(Miller-Madow: {entropia_condicional(ant, atu, True):.4f})")

    print("\n== Tabela IV: dependência entre derivações (resíduos) ==")
    for ordem in (1, 2):
        e0 = np.concatenate([residuo(r[0], ordem) for r in regs])
        e1 = np.concatenate([residuo(r[1], ordem) for r in regs])
        a = (e0 * e1).sum() / (e0 * e0).sum()
        glob = e1 - np.round(a * e0).astype(np.int64)
        por_reg = []
        for r in regs:
            x0, x1 = residuo(r[0], ordem), residuo(r[1], ordem)
            ar = (x0 * x1).sum() / max((x0 * x0).sum(), 1)
            por_reg.append(x1 - np.round(ar * x0).astype(np.int64))
        print(f"Ordem {ordem}: corr={np.corrcoef(e0, e1)[0, 1]:.3f} | "
              f"H(e1)={entropia_empirica(e1):.4f} | "
              f"H(e1-a*e0) global={entropia_empirica(glob):.4f} | "
              f"por registo={entropia_empirica(np.concatenate(por_reg)):.4f}")

    print("\n== Entropia dos resíduos por registo (média) ==")
    for ordem in (1, 2):
        m = [np.mean([entropia_empirica(residuo(r[d], ordem)) for r in regs]) for d in (0, 1)]
        print(f"Ordem {ordem}: deriv.0={m[0]:.4f}  deriv.1={m[1]:.4f}")


if __name__ == "__main__":
    main()
