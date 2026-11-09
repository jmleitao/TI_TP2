'''
Dividir os registos do Dataset (168 registos ECG, ficheiros .dat) em:
- 50% ficheiros de desenvolvimento
- 50% ficheiros de teste

A divisão é aleatória e feita POR FICHEIRO (registo): cada registo pertence
a um e só um dos conjuntos. Usa semente fixa para ser reproduzível.

Uso:
    python divisao.py                      # só escreve as listas
    python divisao.py --copiar             # também copia os ficheiros para
                                           # Dataset_split/desenvolvimento e /teste
    python divisao.py --semente 7 --dataset ../Dataset --saida .
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

# ------------------------------------------------------------------- main
def main():
    base = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--dataset', default=base.parent / 'Dataset')
    ap.add_argument('--saida', default=base)
    ap.add_argument('--semente', type=int, default=SEMENTE_DEFAULT)
    ap.add_argument('--copiar', action='store_true',
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


if __name__ == '__main__':
    main()