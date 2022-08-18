import os
import string
import random
import hashlib
class Seed:
    def __init__(self):
        pass
    
    # retorna string aleatória de tamanho aleatório entre [10, 100]
    def generate_random():
        random.seed(os.urandom(4))
        length = random.randint(10, 100)
        alfabeto = string.ascii_letters + string.digits + string.punctuation
        ans = ""
        for i in range(length):
            ans += random.choice(alfabeto)
        return ans

    # dada uma string retorna a SHA-1 em string binária com zeros à esquerda, sempre de tamanho 160 bits
    def hash_seed(self, seed):
        a = hashlib.sha1(seed.encode())
        b = a.hexdigest()
        ans = str(bin(int(b, 16)))[2:]
        n = len(b)*4 # b é em hexa, cada byte tem 2 hexa, cada hexa, 4 bits
        return self.completa_zeros(ans, n)

    #completa uma string binária de forma que a saída seja sempre 160 bits
    def completa_zeros(self, seed, numero_de_bits=160): #numero_de_bits=160 20bytes*8
        diff = numero_de_bits - len(seed)
        completa = '0'*diff
        return completa + seed

    #checa se uma seed resolve o desafio e se está na forma correta
    def check_seed(self, challenge, seed):
        alfabeto = string.ascii_letters + string.digits + string.punctuation
        set_alfabeto = set()
        for i in range(len(alfabeto)):
            set_alfabeto.add(alfabeto[i])
        for i in range(len(seed)): #checa se a string contém apenas caracteres permitidos de forma eficiente
            if not seed[i] in set_alfabeto:
                return False
        h = self.hash_seed(seed)
        ok = True
        for i in range(challenge):
            ok = ok and (h[i] == '0')
        return ok


if __name__ == "__main__":
    for i in range(10):
        s = Seed.generate_random()