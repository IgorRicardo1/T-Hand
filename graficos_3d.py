from ursina import EditorCamera, Entity, Ursina, camera, color, destroy, time
from logica_jogo import Jogo


class VisualBloco(Entity):
    CORES = {
        "I": color.cyan,
        "O": color.yellow,
        "T": color.violet,
        "S": color.green,
        "Z": color.red,
        "J": color.blue,
        "L": color.orange,
        "PAREDE": color.dark_gray,
    }

    def __init__(self, x, y, tipo="PAREDE"):
        super().__init__(
            model="cube",
            color=self.CORES.get(tipo, color.white),
            texture="white_cube",
            position=(x, -y, 0),
        )


class VisualGrid:
    def __init__(self, largura=10, altura=20):
        self.largura = largura
        self.altura = altura
        self.paredes = []
        self.blocos_dinamicos = []

        self._criar_arena()
        self._configurar_camera()

    def _criar_arena(self):

        for y in range(self.altura + 1):
            self.paredes.append(VisualBloco(-1, y, "PAREDE"))
            self.paredes.append(VisualBloco(self.largura, y, "PAREDE"))

        for x in range(self.largura):
            self.paredes.append(VisualBloco(x, self.altura, "PAREDE"))

    def _configurar_camera(self):
        centro_x = (self.largura - 1) / 2
        centro_y = -(self.altura - 1) / 2
        self.editor_camera = EditorCamera(position=(centro_x, centro_y, 0))
        camera.z = -58

    def atualizar(self, jogo):

        for bloco in self.blocos_dinamicos:
            destroy(bloco)
        self.blocos_dinamicos.clear()

        for y in range(jogo.grid.altura):
            for x in range(jogo.grid.largura):
                letra = jogo.grid.celulas[y][x]
                if letra is not None:
                    self.blocos_dinamicos.append(VisualBloco(x, y, letra))

        for cubo in jogo.peca_atual.cubos:
            x_real = jogo.peca_atual.origem[0] + cubo.x
            y_real = jogo.peca_atual.origem[1] + cubo.y
            if 0 <= y_real < jogo.grid.altura and 0 <= x_real < jogo.grid.largura:
                self.blocos_dinamicos.append(
                    VisualBloco(x_real, y_real, jogo.peca_atual.letra)
                )


if __name__ == "__main__":
    app = Ursina()

    jogo = Jogo()
    arena = VisualGrid(jogo.grid.largura, jogo.grid.altura)

    def update():
        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    app.run()
