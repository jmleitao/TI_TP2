'''
Dividir os ficheiros do Dataset (168 .dat):
- 50% como ficheiros de desenvolvimento
- 50% como ficheiros de teste
'''
import numpy as np
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

