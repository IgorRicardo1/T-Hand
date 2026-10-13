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
    def __init__(self, largura=10, altura=20):
        self.largura = largura
        self.altura = altura
        self.celulas = [[None for _ in range(largura)] for _ in range(altura)]

    def valida_posicao(self, peca):
        for cubo in peca.cubos:
            x_real = peca.origem[0] + cubo.x
            y_real = peca.origem[1] + cubo.y

            if x_real < 0 or x_real >= self.largura:
                return False

            if y_real >= self.altura:
                return False

            if y_real >= 0:
                if self.celulas[y_real][x_real] is not None:
                    return False

        return True

    def fixar_peca(self, peca):
        for cubo in peca.cubos:
            x_real = peca.origem[0] + cubo.x
            y_real = peca.origem[1] + cubo.y

            if y_real >= 0:
                self.celulas[y_real][x_real] = peca.letra

    def limpar_linha(self):
        linhas_completadas = 0

        for y in range(self.altura):
            if None not in self.celulas[y]:
                self.celulas.pop(y)
                linhas_completadas += 1
                self.celulas.insert(0, [None for _ in range(self.largura)])
        return linhas_completadas


class Jogo:
    NUMERO_PONTOS = {1: 100, 2: 300, 3: 600, 4: 1000}

    def __init__(self):
        self.pontos = 0
        self.linhas = 0
        self.grid = Grid()
        self.game_over = False
        self.nova_peca()

        self.gravidade = 1

        self.intervalo_queda = 1.0
        self.tempo_acumulado = 0.0

    def nova_peca(self):
        self.peca_atual = Peca(PecasPossiveis.sortear())
        if not self.grid.valida_posicao(self.peca_atual):
            self.game_over = True

    def atualizar(self, dt):
        if self.game_over:
            return
        self.tempo_acumulado += dt

        while self.tempo_acumulado >= self.intervalo_queda:
            self.tempo_acumulado -= self.intervalo_queda

            if not self.tentar_mover(0, self.gravidade):
                self.grid.fixar_peca(self.peca_atual)
                linhas_eliminadas = self.grid.limpar_linha()
                self.linhas += linhas_eliminadas
                self.pontos += self.NUMERO_PONTOS.get(linhas_eliminadas, 0)
                self.nova_peca()

    def tentar_rotacionar(self, horario=True):
        if self.game_over:
            return
        self.peca_atual.rodar(horario)

        if not self.grid.valida_posicao(self.peca_atual):
            self.peca_atual.rodar(not horario)

    def tentar_mover(self, dx, dy):
        if self.game_over:
            return False
        self.peca_atual.mover(dx, dy)

        if not self.grid.valida_posicao(self.peca_atual):
            self.peca_atual.mover(-dx, -dy)
            return False

        return True


def renderizar_console(jogo):
    print("\n" * 10)
    tela = [["." for _ in range(jogo.grid.largura)] for _ in range(jogo.grid.altura)]

    for y in range(jogo.grid.altura):
        for x in range(jogo.grid.largura):
            if jogo.grid.celulas[y][x] is not None:
                tela[y][x] = "#"

    for cubo in jogo.peca_atual.cubos:
        x_real = jogo.peca_atual.origem[0] + cubo.x
        y_real = jogo.peca_atual.origem[1] + cubo.y
        if 0 <= y_real < jogo.grid.altura and 0 <= x_real < jogo.grid.largura:
            tela[y_real][x_real] = "@"

    print("=" * (jogo.grid.largura * 2 + 3))
    for linha in tela:
        print("| " + " ".join(linha) + " |")
    print("=" * (jogo.grid.largura * 2 + 3))


if __name__ == "__main__":
    jogo = Jogo()

    while True:
        renderizar_console(jogo)

        print(
            "Controles: [A] Esquerda | [D] Direita | [W] Girar | [Enter] Apenas Cair | [Q] Sair"
        )
        print(f"Pontos: {jogo.pontos} | Linhas: {jogo.linhas}")
        comando = input("Digite um comando: ").strip().lower()

        if comando == "q":
            print("Saindo do teste...")
            break
        elif comando == "a":
            jogo.tentar_mover(-1, 0)
        elif comando == "d":
            jogo.tentar_mover(1, 0)
        elif comando == "w":
            jogo.tentar_rotacionar(horario=True)

        jogo.atualizar(0.5)

        if jogo.game_over:
            renderizar_console(jogo)
            print("Game Over")
            break
