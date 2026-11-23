"""
Funcoes complementares para compressao ECG sem perdas:
- predicao de ordem 2 reversivel
- mapeamento signed -> unsigned (zigzag)
- estimativa exata do comprimento Golomb-Rice
- codificacao/descodificacao Golomb-Rice em bitstream

Uso: importar estas funcoes no teu main.py.
"""
import numpy as np


def predict_order2(signal):
    """Devolve residuos e guarda x[0], x[1] nos dois primeiros lugares."""
    x = np.asarray(signal, dtype=np.int64).ravel()
    if len(x) < 2:
        raise ValueError("O sinal precisa de pelo menos 2 amostras.")

    e = np.empty(len(x), dtype=np.int64)
    e[:2] = x[:2]
    for n in range(2, len(x)):
        pred = 2 * x[n - 1] - x[n - 2]
        e[n] = x[n] - pred
    return e


def reconstruct_order2(residuals):
    """Reconstrói exatamente o sinal a partir dos resíduos da função acima."""
    e = np.asarray(residuals, dtype=np.int64).ravel()
    if len(e) < 2:
        raise ValueError("São necessários pelo menos 2 resíduos.")

    x = np.empty(len(e), dtype=np.int64)
    x[:2] = e[:2]
    for n in range(2, len(e)):
        x[n] = e[n] + 2 * x[n - 1] - x[n - 2]
    return x


def signed_to_unsigned_array(values):
    """Zigzag: 0, -1, +1, -2, +2, ... -> 0, 1, 2, 3, 4, ..."""
    e = np.asarray(values, dtype=np.int64)
    return np.where(e >= 0, 2 * e, -2 * e - 1).astype(np.uint64)


def unsigned_to_signed_array(values):
    u = np.asarray(values, dtype=np.uint64)
    out = np.empty(u.shape, dtype=np.int64)
    even = (u & 1) == 0
    out[even] = (u[even] // 2).astype(np.int64)
    out[~even] = -((u[~even] // 2) + 1).astype(np.int64)
    return out


def rice_length_bits(unsigned_values, k):
    """Número exato de bits Rice, sem cabeçalho nem padding de byte."""
    if k < 0:
        raise ValueError("k tem de ser >= 0")
    u = np.asarray(unsigned_values, dtype=np.uint64)
    q = u >> k
    return int(np.sum(q, dtype=np.uint64)) + len(u) * (1 + k)


class _BitWriter:
    def __init__(self):
        self.data = bytearray()
        self.buffer = 0
        self.nbits_in_buffer = 0
        self.total_bits = 0

    def write_bit(self, bit):
        self.buffer = (self.buffer << 1) | int(bit)
        self.nbits_in_buffer += 1
        self.total_bits += 1
        if self.nbits_in_buffer == 8:
            self.data.append(self.buffer)
            self.buffer = 0
            self.nbits_in_buffer = 0

    def write_bits(self, value, n):
        for shift in range(n - 1, -1, -1):
            self.write_bit((value >> shift) & 1)

    def finish(self):
        if self.nbits_in_buffer:
            self.data.append(self.buffer << (8 - self.nbits_in_buffer))
            self.buffer = 0
            self.nbits_in_buffer = 0
        return bytes(self.data), self.total_bits


class _BitReader:
    def __init__(self, data, nbits):
        self.data = data
        self.nbits = nbits
        self.pos = 0

    def read_bit(self):
        if self.pos >= self.nbits:
            raise ValueError("Fim inesperado do bitstream.")
        byte = self.data[self.pos // 8]
        bit = (byte >> (7 - (self.pos % 8))) & 1
        self.pos += 1
        return bit

    def read_bits(self, n):
        value = 0
        for _ in range(n):
            value = (value << 1) | self.read_bit()
        return value


def rice_encode(unsigned_values, k):
    """Codifica array de inteiros >=0. Devolve (bytes, numero_de_bits)."""
    if k < 0:
        raise ValueError("k tem de ser >= 0")
    writer = _BitWriter()
    for value in np.asarray(unsigned_values, dtype=np.uint64).ravel():
        u = int(value)
        q = u >> k
        r = u & ((1 << k) - 1) if k else 0
        for _ in range(q):
            writer.write_bit(1)
        writer.write_bit(0)
        writer.write_bits(r, k)
    return writer.finish()


def rice_decode(data, nbits, n_symbols, k):
    """Descodifica exatamente n_symbols; nbits exclui padding final."""
    if k < 0:
        raise ValueError("k tem de ser >= 0")
    reader = _BitReader(data, nbits)
    values = np.empty(n_symbols, dtype=np.uint64)

    for i in range(n_symbols):
        q = 0
        while reader.read_bit() == 1:
            q += 1
        r = reader.read_bits(k)
        values[i] = (q << k) | r

    if reader.pos != nbits:
        raise ValueError(
            f"Bitstream tem {nbits - reader.pos} bits extra; "
            "verifica n_symbols e nbits."
        )
    return values


def encode_order2_rice(signal, k):
    """Pipeline completo: sinal -> resíduos ordem 2 -> zigzag -> Rice."""
    residuals = predict_order2(signal)
    unsigned = signed_to_unsigned_array(residuals)
    data, nbits = rice_encode(unsigned, k)
    return data, nbits, len(residuals)


def decode_order2_rice(data, nbits, n_samples, k):
    """Pipeline inverso, com reconstrução exata."""
    unsigned = rice_decode(data, nbits, n_samples, k)
    residuals = unsigned_to_signed_array(unsigned)
    return reconstruct_order2(residuals)


def choose_rice_k_dev(dev_records, lead, k_values=range(13)):
    """
    Escolhe k no desenvolvimento.
    dev_records: lista de tuplos (derivacao0, derivacao1).
    Devolve (melhor_k, tabela {k: bits_totais}).
    """
    residuals = np.concatenate([
        predict_order2(record[lead]) for record in dev_records
    ])
    unsigned = signed_to_unsigned_array(residuals)
    scores = {
        int(k): rice_length_bits(unsigned, int(k))
        for k in k_values
    }
    best_k = min(scores, key=scores.get)
    return best_k, scores


def huffman_encode_lossless(values):
    """Huffman usando huffmancodec.py com símbolo EOF para descodificação segura.

    Devolve (bytes_comprimidos, codec). O tamanho do codebook não está
    incluído em len(bytes_comprimidos); contabiliza-o separadamente na avaliação.
    """
    from collections import Counter
    from huffmancodec import HuffmanCodec, _EOF

    symbols = [int(v) for v in np.asarray(values).ravel()]
    if not symbols:
        raise ValueError("Não é possível codificar uma sequência vazia.")

    frequencies = Counter(symbols)
    frequencies[_EOF] = 1  # marcador de fim: corrige a ausência de EOF no from_data
    codec = HuffmanCodec.from_frequencies(frequencies, eof=_EOF)
    encoded = codec.encode(symbols)
    return encoded, codec


def huffman_decode_lossless(encoded, codec):
    """Descodifica os bytes gerados por huffman_encode_lossless."""
    return np.asarray(codec.decode(encoded), dtype=np.int64)
