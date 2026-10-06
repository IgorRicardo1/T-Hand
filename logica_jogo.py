import random


class CuboUnico:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"CuboUnico({self.x}, {self.y})"


class PecasPossiveis:
    FORMATOS = {
        "I": ((-1, 0), (0, 0), (1, 0), (2, 0)),
        "T": ((-1, 0), (0, 0), (1, 0), (0, -1)),
        "L": ((1, -1), (-1, 0), (0, 0), (1, 0)),
        "J": ((-1, -1), (-1, 0), (0, 0), (1, 0)),
        "S": ((-1, 0), (0, 0), (0, -1), (1, -1)),
        "Z": ((-1, -1), (0, -1), (0, 0), (1, 0)),
        "O": ((0, 0), (0, 1), (1, 0), (1, 1)),
    }

    @classmethod
    def sortear(cls):
        return random.choice(list(cls.FORMATOS.items()))


class Peca:
    def __init__(self, letra_e_formato):
        letra, formato = letra_e_formato
        self.letra = letra
        self.cubos = [CuboUnico(c[0], c[1]) for c in formato]
        self.origem = [4, 0]

    def mover(self, mover_x, mover_y):
        self.origem[0] += mover_x
        self.origem[1] += mover_y

    def rodar(self, horario=True):
        if self.letra == "O":
            return
        else:
            for cubos_unicos in self.cubos:
                if horario:
                    novo_x = -cubos_unicos.y
                    novo_y = cubos_unicos.x
                else:
                    novo_x = cubos_unicos.y
                    novo_y = -cubos_unicos.x
                cubos_unicos.x, cubos_unicos.y = novo_x, novo_y


class Grid:
    def __init__(self):
        pass


class Jogo:
    def __init__(self):
        pass


if __name__ == "__main__":
    """testes"""
    sorteio = PecasPossiveis.sortear()
    print(sorteio)
    peca = Peca(sorteio)
    print(peca.cubos)
    peca.rodar()
    print(peca.cubos)
