"""Experiências de compressão sem perdas para o Dataset ECG.

- divisão reproduzível por registo (desenvolvimento/teste)
- análise de entropia no conjunto de desenvolvimento
- Huffman por registo (codebook construído e transmitido por bloco)
- predição de ordem 2 + Huffman
- predição de ordem 2 + Golomb-Rice (k escolhido só em desenvolvimento)

Nota: para Huffman, o codebook é calculado por registo e o seu tamanho
serializado é contabilizado como overhead aproximado. Isto é um Huffman
adaptativo por bloco, não um codebook global treinado apenas no desenvolvimento.
"""
import argparse
import pickle
import random
import shutil
import time
from pathlib import Path

import numpy as np

from golomb_rice import (
    predict_order2,
    reconstruct_order2,
    signed_to_unsigned_array,
    rice_length_bits,
    encode_order2_rice,
    decode_order2_rice,
    choose_rice_k_dev,
    huffman_encode_lossless,
    huffman_decode_lossless,
)

SEMENTE_DEFAULT = 42


# ------------------------------------------------------------------ divisão
def listar_registos(pasta_dataset):
    registos = sorted(p.stem for p in Path(pasta_dataset).glob("*.dat"))
    if not registos:
        raise FileNotFoundError(f"Nenhum .dat encontrado em {pasta_dataset}")
    return registos

def dividir(registos, semente=SEMENTE_DEFAULT):
    rng = random.Random(semente)
    baralhados = list(registos)
    rng.shuffle(baralhados)
    n_dev = (len(baralhados) + 1) // 2
    dev = sorted(baralhados[:n_dev])
    teste = sorted(baralhados[n_dev:])
    assert not (set(dev) & set(teste))
    assert set(dev) | set(teste) == set(registos)
    return dev, teste

def escrever_lista(nomes, caminho):
    Path(caminho).write_text("\n".join(nomes) + "\n", encoding="utf-8")

def copiar_registos(nomes, pasta_dataset, pasta_destino):
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    for nome in nomes:
        for f in Path(pasta_dataset).glob(nome + ".*"):
            shutil.copy2(f, pasta_destino / f.name)

def divisao(args):
    pasta_dataset = Path(args.dataset)
    dev, teste = dividir(listar_registos(pasta_dataset), args.semente)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    escrever_lista(dev, saida / "desenvolvimento.txt")
    escrever_lista(teste, saida / "teste.txt")
    if args.copiar:
        raiz = saida / "Dataset_split"
        copiar_registos(dev, pasta_dataset, raiz / "desenvolvimento")
        copiar_registos(teste, pasta_dataset, raiz / "teste")
    print(f"Total: {len(dev) + len(teste)} | desenvolvimento: {len(dev)} | "
          f"teste: {len(teste)} | semente: {args.semente}")
    return pasta_dataset, dev, teste

# --------------------------------------------------------------- leitura ECG
def ler_registo(caminho):
    """Lê um .dat WFDB formato 212 com duas derivações intercaladas."""
    caminho = Path(caminho)
    hea = caminho.with_suffix(".hea").read_text(encoding="utf-8").splitlines()
    formato = hea[1].split()[1]
    if not formato.startswith("212"):
        raise ValueError(f"{caminho}: formato {formato}, esperado 212")

    b = np.fromfile(caminho, dtype=np.uint8).astype(np.int32)
    b = b[: len(b) // 3 * 3].reshape(-1, 3)
    a0 = b[:, 0] | ((b[:, 1] & 0x0F) << 8)
    a1 = b[:, 2] | ((b[:, 1] & 0xF0) << 4)
    a0 = np.where(a0 >= 2048, a0 - 4096, a0).astype(np.int16)
    a1 = np.where(a1 >= 2048, a1 - 4096, a1).astype(np.int16)
    return a0, a1

def carregar_registos(pasta_dataset, nomes):
    return [ler_registo(Path(pasta_dataset) / (nome + ".dat")) for nome in nomes]

# --------------------------------------------------------------- entropia
def entropia(fonte):
    fonte = np.asarray(fonte).ravel()
    if len(fonte) == 0:
        return 0.0
    _, counts = np.unique(fonte, return_counts=True)
    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p)))

def agrupar_pares(x):
    """Agrupa amostras consecutivas em símbolos de 24 bits sem colisões."""
    x = np.asarray(x, dtype=np.int64)
    x = x[: len(x) // 2 * 2]
    # Deslocamento para tornar as amostras de 12 bits não negativas.
    return ((x[0::2] + 2048) * 4096 + (x[1::2] + 2048)).astype(np.int64)

def analise_dev(registos_dev):
    print("\n========== ANÁLISE DO DESENVOLVIMENTO ==========")
    print(f"Registos: {len(registos_dev)}")
    if not registos_dev:
        return
    print(f"Amostras por derivação: {sum(len(r[0]) for r in registos_dev)}\n")

    for d in (0, 1):
        fonte = np.concatenate([r[d].astype(np.int64) for r in registos_dev])
        print(f"===== Derivação {d} =====")
        print(f"min={fonte.min()}, max={fonte.max()}, distintos={len(np.unique(fonte))}")
        print(f"H(X) = {entropia(fonte):.4f} bits/amostra")

        pares = np.concatenate([agrupar_pares(r[d]) for r in registos_dev])
        print(f"H(X1,X2)/2 = {entropia(pares) / 2:.4f} bits/amostra")

        for ordem in (1, 2):
            residuos = np.concatenate([
                np.diff(r[d].astype(np.int64), n=ordem)
                for r in registos_dev
            ])
            print(f"H(resíduo ordem {ordem}) = {entropia(residuos):.4f} bits/amostra")
        print()

# ---------------------------------------------------------- avaliação métodos
def avaliar_huffman_por_registo(registos, lead, residual_order2=False):
    """Huffman por bloco: codebook adaptado ao registo e transmitido com ele."""
    payload_bytes = 0
    model_bytes = 0
    samples = 0
    encode_time = 0.0
    decode_time = 0.0

    for registo in registos:
        sinal = np.asarray(registo[lead], dtype=np.int64)
        fonte = predict_order2(sinal) if residual_order2 else sinal

        t0 = time.perf_counter()
        encoded, codec = huffman_encode_lossless(fonte)
        encode_time += time.perf_counter() - t0

        t0 = time.perf_counter()
        decoded = huffman_decode_lossless(encoded, codec)
        if residual_order2:
            decoded = reconstruct_order2(decoded)
        decode_time += time.perf_counter() - t0

        if not np.array_equal(sinal, decoded):
            raise AssertionError("Huffman não reconstruiu o sinal exatamente")

        payload_bytes += len(encoded)
        # Serialização do codebook como estimativa do custo de transmissão.
        model_bytes += len(pickle.dumps(codec.get_code_table(), protocol=pickle.HIGHEST_PROTOCOL))
        samples += len(sinal)

    total_bits = 8 * (payload_bytes + model_bytes)
    return {
        "samples": samples,
        "payload_bytes": payload_bytes,
        "model_bytes": model_bytes,
        "total_bits": total_bits,
        "bps": total_bits / samples if samples else 0.0,
        "cr": (12 * samples / total_bits) if total_bits else 0.0,
        "encode_s": encode_time,
        "decode_s": decode_time,
    }

def avaliar_rice(registos, lead, k):
    payload_bytes = 0
    actual_bits = 0
    samples = 0
    encode_time = 0.0
    decode_time = 0.0

    for registo in registos:
        sinal = np.asarray(registo[lead], dtype=np.int64)
        t0 = time.perf_counter()
        data, nbits, n_samples = encode_order2_rice(sinal, k)
        encode_time += time.perf_counter() - t0

        t0 = time.perf_counter()
        decoded = decode_order2_rice(data, nbits, n_samples, k)
        decode_time += time.perf_counter() - t0

        if not np.array_equal(sinal, decoded):
            raise AssertionError("Rice não reconstruiu o sinal exatamente")

        payload_bytes += len(data)
        actual_bits += nbits
        samples += len(sinal)

    # O bitstream Rice inclui os dois primeiros valores através do código.
    # Acrescentar uma estimativa pequena de metadados por registo (k e N).
    metadata_bits = 32 * len(registos)
    total_bits = actual_bits + metadata_bits
    return {
        "samples": samples,
        "payload_bytes": payload_bytes,
        "model_bytes": metadata_bits // 8,
        "total_bits": total_bits,
        "bps": total_bits / samples if samples else 0.0,
        "cr": (12 * samples / total_bits) if total_bits else 0.0,
        "encode_s": encode_time,
        "decode_s": decode_time,
    }

def imprimir_resultado(nome, resultado):
    print(f"{nome:24s} | {resultado['bps']:8.4f} bits/amostra | "
          f"CR={resultado['cr']:6.3f} | "
          f"encode={resultado['encode_s']:.3f}s | "
          f"decode={resultado['decode_s']:.3f}s | "
          f"payload={resultado['payload_bytes']} B | "
          f"modelo/metadados={resultado['model_bytes']} B")

def executar_experiencias(registos_dev):
    """Executa todas as experiências apenas nos registos de desenvolvimento."""
    print("\n========== EXPERIÊNCIAS NO DESENVOLVIMENTO ==========")
    for d in (0, 1):
        print(f"\n--- Derivação {d} ---")

        imprimir_resultado(
            "Huffman por registo",
            avaliar_huffman_por_registo(registos_dev, d, residual_order2=False),
        )
        imprimir_resultado(
            "Ordem 2 + Huffman",
            avaliar_huffman_por_registo(registos_dev, d, residual_order2=True),
        )

        melhor_k, scores = choose_rice_k_dev(
            registos_dev, lead=d, k_values=range(13)
        )
        n_dev_samples = sum(len(r[d]) for r in registos_dev)
        print(f"k Rice escolhido no desenvolvimento: {melhor_k}")
        print("Comprimento Rice no desenvolvimento (sem cabeçalho/padding):")
        for k, bits in sorted(scores.items()):
            print(f"  k={k:2d}: {bits / n_dev_samples:.4f} bits/amostra")

        imprimir_resultado(
            "Ordem 2 + Golomb-Rice",
            avaliar_rice(registos_dev, d, melhor_k),
        )

# ---------------------------------------------------------------------- main
def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(base.parent / "Dataset"))
    parser.add_argument("--saida", default=str(base))
    parser.add_argument("--semente", type=int, default=SEMENTE_DEFAULT)
    parser.add_argument("--copiar", action="store_true")
    args = parser.parse_args()

    pasta_dataset, nomes_dev, _nomes_teste = divisao(args)
    # Nesta fase, carregar e utilizar exclusivamente os registos de desenvolvimento.
    registos_dev = carregar_registos(pasta_dataset, nomes_dev)

    analise_dev(registos_dev)
    executar_experiencias(registos_dev)

if __name__ == "__main__":
    main()