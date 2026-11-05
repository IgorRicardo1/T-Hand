import math
import cv2

from panda3d.core import Texture as PandaTexture

from ursina import EditorCamera, Entity, Texture, Ursina, application, camera, color, destroy, time
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
        self._textura_p3d: PandaTexture | None = None
        self._criar_fundo()

        self._ultimo_estado = None

    def _criar_arena(self):
        for y in range(self.altura + 1):
            self.paredes.append(VisualBloco(-1, y, "PAREDE"))
            self.paredes.append(VisualBloco(self.largura, y, "PAREDE"))

        for x in range(self.largura):
            self.paredes.append(VisualBloco(x, self.altura, "PAREDE"))

    def _configurar_camera(self):
        centro_x = (self.largura - 1) / 2
        centro_y = -(self.altura - 1) / 2
        camera.z = -58
        self.editor_camera = EditorCamera(position=(centro_x, centro_y, 0))
        self.editor_camera.target_z = -58

    def _criar_fundo(self):
        distancia = 100
        hfov, vfov = application.base.camLens.getFov()
        largura_plano = 2 * distancia * math.tan(math.radians(hfov / 2))
        altura_plano = 2 * distancia * math.tan(math.radians(vfov / 2))

        self.fundo = Entity(
            parent=camera,
            model="quad",
            position=(0, 0, distancia),
            scale=(largura_plano, altura_plano, 1),
            unlit=True,
        )
        self.fundo.setBin("background", 0)
        self.fundo.setDepthWrite(False)

    def atualizar_fundo(self, frame):
        altura_f, largura_f = frame.shape[:2]

        if self._textura_p3d is None:
            self._textura_p3d = PandaTexture()
            self._textura_p3d.setup2dTexture(
                largura_f,
                altura_f,
                PandaTexture.T_unsigned_byte,
                PandaTexture.F_rgb,
            )
            self.fundo.texture = Texture(self._textura_p3d)

        frame_invertido = cv2.flip(frame, 0)
        self._textura_p3d.setRamImage(frame_invertido)

    def atualizar(self, jogo):
        estado_atual = (
            tuple(tuple(linha) for linha in jogo.grid.celulas),
            jogo.peca_atual.letra,
            tuple(jogo.peca_atual.origem),
            tuple((c.x, c.y) for c in jogo.peca_atual.cubos),
        )

        if estado_atual == self._ultimo_estado:
            return

        self._ultimo_estado = estado_atual

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

    def input(key):
        global jogo
        if key in ("a", "left arrow"):
            jogo.tentar_mover(-1, 0)
        elif key in ("d", "right arrow"):
            jogo.tentar_mover(1, 0)
        elif key in ("s", "down arrow"):
            jogo.tentar_mover(0, 1)
        elif key in ("w", "up arrow"):
            jogo.tentar_rotacionar(horario=True)
        elif key == "q":
            jogo.tentar_rotacionar(horario=False)
        elif key == "r":
            jogo = Jogo()

    def update():
        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    app.run()
