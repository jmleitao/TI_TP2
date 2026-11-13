'''
Dividir os registos do Dataset (168 registos ECG, ficheiros .dat) em:
- 50% ficheiros de desenvolvimento
- 50% ficheiros de teste

A divisão é aleatória e feita POR FICHEIRO (registo): cada registo pertence
a um e só um dos conjuntos. Usa semente fixa para ser reproduzível.
'''
import argparse
import random
import shutil
from pathlib import Path

import numpy as np

SEMENTE_DEFAULT = 42


# ---------------------------------------------------------------- divisão
def listar_registos(pasta_dataset):
    '''Nomes (sem extensão) de todos os registos com .dat, ordenados.'''
    registos = sorted(p.stem for p in Path(pasta_dataset).glob('*.dat'))
    if not registos:
        raise FileNotFoundError(f'Nenhum .dat encontrado em {pasta_dataset}')
    return registos

def dividir(registos, semente=SEMENTE_DEFAULT):
    '''Divide a lista em (desenvolvimento, teste), 50%/50%, aleatoriamente.
    Com número ímpar de registos, o conjunto de desenvolvimento fica com
    o registo a mais (arredondamento por excesso).'''
    rng = random.Random(semente)
    baralhados = registos.copy()
    rng.shuffle(baralhados)

    n_dev = (len(baralhados) + 1) // 2
    desenvolvimento = sorted(baralhados[:n_dev])
    teste = sorted(baralhados[n_dev:])

    # garantias: sem sobreposição e sem perdas
    assert not set(desenvolvimento) & set(teste)
    assert set(desenvolvimento) | set(teste) == set(registos)
    return desenvolvimento, teste

def escrever_lista(nomes, caminho):
    Path(caminho).write_text('\n'.join(nomes) + '\n')

def copiar_registos(nomes, pasta_dataset, pasta_destino):
    '''Copia todos os ficheiros de cada registo (.dat, .hea, .hea-, .xws...).'''
    pasta_destino = Path(pasta_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    for nome in nomes:
        for f in Path(pasta_dataset).glob(nome + '.*'):
            shutil.copy2(f, pasta_destino / f.name)

def divisao():
    base = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--dataset', default=base.parent / 'Dataset')
    ap.add_argument('--saida', default=base)
    ap.add_argument('--semente', type=int, default=SEMENTE_DEFAULT)
    ap.add_argument('--copiar', required=True ,action='store_true',
                    help='copiar os ficheiros para Dataset_split/')
    args = ap.parse_args()

    registos = listar_registos(args.dataset)
    dev, teste = dividir(registos, args.semente)

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    escrever_lista(dev, saida / 'desenvolvimento.txt')
    escrever_lista(teste, saida / 'teste.txt')

    if args.copiar:
        raiz = saida / 'Dataset_split'
        copiar_registos(dev, args.dataset, raiz / 'desenvolvimento')
        copiar_registos(teste, args.dataset, raiz / 'teste')

    print(f'Total: {len(registos)} | desenvolvimento: {len(dev)} | '
          f'teste: {len(teste)} | semente: {args.semente}')

    return dev, teste

# --------------------------------------------------------------- entropia
def contar(fonte, alfabeto):
    #posição de cada símbolo no alfabeto
    indices = np.searchsorted(alfabeto, fonte)       
    
    ocorrencias = np.zeros(len(alfabeto), dtype=int)

    for i in indices:
        ocorrencias[i] += 1

    return ocorrencias

def criar_alfabeto(dados):
    info = np.iinfo(dados.dtype)
    return np.arange(info.min, info.max + 1)

def entropia(fonte, alfabeto):
    #Nº de vezes que cada símbolo aparece na fonte
    ocorrencias = contar(fonte,alfabeto)

    #Probabilidade de cada símbolo
    probabilidade = ocorrencias / len(fonte)

    #Remove os 0s da probabilidade para não ter naN
    probabilidade = probabilidade[probabilidade != 0] 

    entropia = -np.sum(probabilidade * np.log2(probabilidade))

    return entropia

# ------------------------------------------------- leitura dos ficheiros .dat
def ler_registo(caminho):
    '''Lê um .dat em formato 212 (12 bits, 2 derivações intercaladas).
    Cada 3 bytes guardam 2 amostras (uma de cada derivação).
    Devolve (derivacao0, derivacao1) como int16.'''
    # confirmar no .hea: 2ª linha = "nome formato ganho resolução ..."
    hea = Path(caminho).with_suffix('.hea').read_text().splitlines()
    formato = hea[1].split()[1]
    assert formato.startswith('212'), f'{caminho}: formato {formato}, esperado 212'

    b = np.fromfile(caminho, dtype=np.uint8).astype(np.int16)
    b = b[:len(b) // 3 * 3].reshape(-1, 3)

    amostra0 = b[:, 0] | ((b[:, 1] & 0x0F) << 8)
    amostra1 = b[:, 2] | ((b[:, 1] & 0xF0) << 4)

    # complemento para 2 (12 bits com sinal)
    amostra0 = np.where(amostra0 >= 2048, amostra0 - 4096, amostra0).astype(np.int16)
    amostra1 = np.where(amostra1 >= 2048, amostra1 - 4096, amostra1).astype(np.int16)
    return amostra0, amostra1

def carregar_dev(pasta_dataset, nomes_dev):
    '''Lista de (derivacao0, derivacao1), um tuplo por registo de desenvolvimento.'''
    return [ler_registo(Path(pasta_dataset) / (n + '.dat')) for n in nomes_dev]

# ------------------------------------------------------ análise (só dev)
def residuos(x, ordem):
    '''Erro de predição: ordem 0 = sinal original, 1 = x[n]-x[n-1],
    2 = x[n]-2x[n-1]+x[n-2] (aplica np.diff 'ordem' vezes).'''
    return np.diff(x, n=ordem).astype(np.int16)

def agrupar_pares(x):
    '''Junta amostras consecutivas (x[0],x[1]), (x[2],x[3])... num só símbolo.'''
    x = x[:len(x) // 2 * 2].astype(np.int32)
    return (x[0::2] + 2048) * 4096 + (x[1::2] + 2048)

def analise(pasta_dataset, nomes_dev):
    registos = carregar_dev(pasta_dataset, nomes_dev)

    print(f'Registos de desenvolvimento: {len(registos)}')
    print(f'Amostras por derivação (total): {sum(len(r[0]) for r in registos)}\n')

    for d in (0, 1):
        print(f'===== Derivação {d} =====')

        # 1) Entropia da fonte (amostras isoladas)
        fonte = np.concatenate([r[d] for r in registos])
        alfabeto = criar_alfabeto(fonte)
        H0 = entropia(fonte, alfabeto)
        print(f'Valores: min={fonte.min()}, max={fonte.max()}, '
              f'símbolos distintos={len(np.unique(fonte))}')
        print(f'H(X) = {H0:.4f} bits/amostra  (12 bits sem compressão)')

        # 2) Agrupamento: pares de amostras consecutivas
        pares = np.concatenate([agrupar_pares(r[d]) for r in registos])
        H_pares = entropia(pares, np.unique(pares)) / 2
        print(f'Pares de amostras: H(X1,X2)/2 = {H_pares:.4f} bits/amostra')

        # 3) Predição: entropia do erro de predição (por registo, sem
        #    misturar o fim de um registo com o início do seguinte)
        for ordem in (1, 2):
            erro = np.concatenate([residuos(r[d], ordem) for r in registos])
            H_erro = entropia(erro, criar_alfabeto(erro))
            print(f'Predição de ordem {ordem}: H(erro) = {H_erro:.4f} bits/amostra')
        print()

# ------------------------------------------------------------------- main
def main():
    base = Path(__file__).resolve().parent
    dev , teste = divisao()

    # Reutiliza a mesma divisão (mesma semente) e analisa SÓ o desenvolvimento
    pasta_dataset = base.parent / 'Dataset'
    analise(pasta_dataset, dev)

if __name__ == '__main__': main()