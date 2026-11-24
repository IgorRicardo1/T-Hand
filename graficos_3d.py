import math
import random
import cv2
from panda3d.core import Texture as PandaTexture
from ursina import (
    DirectionalLight,
    EditorCamera,
    Entity,
    Text,
    Texture,
    Ursina,
    Vec2,
    Vec3,
    camera,
    color,
    curve,
    destroy,
    lerp,
    time,
    window,
)
from audio_synth import MotorAudioSynthwave
from efeitos_visuais import (
    SHADER_BLOCO_PBR,
    SHADER_FUNDO_CYBER,
    CampoEstelar3D,
    GerenciadorPostProcess,
    gerar_painel_glass_ui,
    gerar_textura_bloco_cristal,
    gerar_textura_flare,
)
from logica_jogo import Jogo


class VisualBloco(Entity):
    TEXTURA_CRISTAL = None

    CORES = {
        "I": color.rgb32(0, 238, 255),
        "O": color.rgb32(255, 220, 20),
        "T": color.rgb32(195, 75, 255),
        "S": color.rgb32(40, 245, 115),
        "Z": color.rgb32(255, 55, 95),
        "J": color.rgb32(55, 125, 255),
        "L": color.rgb32(255, 145, 25),
        "PAREDE": color.rgb32(42, 48, 62),
        "MOLDURA": color.rgb32(68, 78, 98),
    }

    def __init__(self, x, y, tipo="PAREDE", z=0, escala=0.96, parent_entity=None):
        if VisualBloco.TEXTURA_CRISTAL is None:
            VisualBloco.TEXTURA_CRISTAL = gerar_textura_bloco_cristal(256)

        kwargs = {}
        if parent_entity is not None:
            kwargs["parent"] = parent_entity

        super().__init__(
            model="cube",
            color=self.CORES.get(tipo, color.white),
            texture=VisualBloco.TEXTURA_CRISTAL,
            position=(x, -y, z),
            scale=escala,
            shader=SHADER_BLOCO_PBR,
            **kwargs,
        )


class VisualGrid:
    NOMES_TEMAS = ("CYBER NEON", "STUDIO GLASS", "SOLAR VAPORWAVE")

    def __init__(self, largura=10, altura=20):
        window.title = "T-Hand: Overdrive 3D Edition"
        window.color = color.rgb32(8, 12, 24)

        self.largura = largura
        self.altura = altura
        self.tema_atual = 0

        self.audio = MotorAudioSynthwave()
        self.post_process = GerenciadorPostProcess()
        self.tex_flare = gerar_textura_flare(64)

        self.paredes = []
        self.celulas_fundo_grid = []
        self.blocos_fixos = []
        self.blocos_peca_atual = [VisualBloco(0, 0, "I") for _ in range(4)]
        self.blocos_fantasma = [VisualBloco(0, 0, "I") for _ in range(4)]
        self.feixes_laser = [
            Entity(model="cube", color=color.rgba(1, 1, 1, 0.14), unlit=True)
            for _ in range(4)
        ]

        # 3 pedestais para a fila de Próximas Peças + 1 pedestal para Reserva (Hold)
        self.pivos_proximas = [
            Entity(position=(self.largura + 4.5, -2.5 - idx * 5.8, 0))
            for idx in range(3)
        ]
        self.blocos_proximas = [[], [], []]
        self.pivô_reserva = Entity(position=(-5.5, -2.5, 0))
        self.blocos_reserva = []
        self.cubos_ambiente = []

        self.ultimo_grid = None
        self.ultimas_proximas_letras = None
        self.ultima_reserva_letra = None
        self.textura_camera = None
        self.mostrar_fantasma = True
        self.pontos_exibidos = 0.0
        self.alvo_parallax = Vec2(0, 0)
        self.parallax_atual = Vec2(0, 0)

        self._criar_hud()
        self._criar_arena()
        self.campo_estelar = CampoEstelar3D(self.tex_flare, quantidade=60)
        self._configurar_camera()
        self._configurar_iluminacao()
        self.aplicar_tema(0)

    def _criar_hud(self):
        tex_card = gerar_painel_glass_ui(520, 320, raio=34, cor_borda=(0, 230, 255))
        self.painel_hud = Entity(
            parent=camera.ui,
            model="quad",
            texture=tex_card,
            scale=(0.42, 0.27),
            position=(-0.65, 0.34, 0.02),
        )
        self.placar = Text(
            position=(-0.835, 0.445),
            scale=1.1,
            color=color.white,
        )
        self.barra_nivel_fundo = Entity(
            parent=camera.ui,
            model="quad",
            scale=(0.35, 0.015),
            position=(-0.65, 0.235, 0.01),
            color=color.rgb32(45, 55, 78),
        )
        self.barra_nivel = Entity(
            parent=camera.ui,
            model="quad",
            origin=(-0.5, 0),
            scale=(0.01, 0.015),
            position=(-0.825, 0.235, 0.0),
            color=color.rgb32(0, 245, 190),
        )

        self.legenda_controles = Text(
            text="[Espaco/Puxao] Hard Drop  [C/Pinca Dupla] Hold  [T] Tema  [M] Musica  [G] Fantasma  [P] Pausa  [R] Reset",
            position=(-0.66, -0.46),
            scale=0.82,
            color=color.rgb32(190, 210, 235),
        )

        self.borda_camera = Entity(
            parent=camera.ui,
            model="quad",
            scale=(0.376, 0.286),
            position=(0.66, 0.33, 0.02),
            color=color.rgb32(0, 220, 255),
            enabled=False,
        )
        self.painel_camera = Entity(
            parent=camera.ui,
            model="quad",
            scale=(0.36, 0.27),
            position=(0.66, 0.33, 0.01),
            enabled=False,
        )
        self.status_camera = Text(
            text="",
            position=(0.48, 0.176),
            scale=0.88,
            color=color.rgb32(180, 230, 255),
        )

    def _criar_arena(self):
        centro_x = (self.largura - 1) / 2
        centro_y = -(self.altura - 1) / 2

        self.parede_fundo = Entity(
            model="cube",
            position=(centro_x, centro_y, 3.2),
            scale=(92, 60, 0.5),
            shader=SHADER_FUNDO_CYBER,
        )

        for y in range(self.altura):
            for x in range(self.largura):
                cel = Entity(
                    model="cube",
                    color=color.rgb32(22, 30, 48),
                    position=(x, -y, 0.62),
                    scale=(0.9, 0.9, 0.08),
                    shader=SHADER_BLOCO_PBR,
                )
                self.celulas_fundo_grid.append(cel)

        for y in range(self.altura + 1):
            self.paredes.append(VisualBloco(-1, y, "PAREDE"))
            self.paredes.append(VisualBloco(self.largura, y, "PAREDE"))
        for x in range(self.largura):
            self.paredes.append(VisualBloco(x, self.altura, "PAREDE"))

        self.neon_esq = Entity(
            model="cube",
            position=(-1.56, centro_y, -0.22),
            scale=(0.18, self.altura + 1.2, 0.5),
            color=color.cyan,
            unlit=True,
        )
        self.neon_dir = Entity(
            model="cube",
            position=(self.largura + 0.56, centro_y, -0.22),
            scale=(0.18, self.altura + 1.2, 0.5),
            color=color.cyan,
            unlit=True,
        )
        self.neon_chao = Entity(
            model="cube",
            position=(centro_x, -self.altura - 0.56, -0.22),
            scale=(self.largura + 2.3, 0.18, 0.5),
            color=color.cyan,
            unlit=True,
        )

        # Moldura da Próxima Principal + Hold
        self._criar_moldura_3d(self.largura + 2, 0, 6, 6)
        self._criar_moldura_3d(-8, 0, 6, 6)

        self.titulo_proxima = Text(
            parent=self.pivos_proximas[0],
            text="FILA (NEXT)",
            position=(-1.65, 3.35, -0.6),
            scale=13,
            color=color.rgb32(0, 235, 255),
        )
        self.titulo_reserva = Text(
            parent=self.pivô_reserva,
            text="HOLD [C]",
            position=(-1.45, 3.35, -0.6),
            scale=13,
            color=color.rgb32(0, 235, 255),
        )

        posicoes_decor = [
            (-14, -3, 1.8),
            (-12, -14, 1.5),
            (-15, -19, 2.0),
            (20, -11, 1.8),
            (18, -19, 1.5),
            (22, -4, 2.0),
        ]
        tipos_decor = ["I", "T", "L", "S", "Z", "J"]
        for (dx, dy, dz), t_letra in zip(posicoes_decor, tipos_decor):
            cubo_amb = VisualBloco(dx, -dy, t_letra, z=dz, escala=1.35)
            self.cubos_ambiente.append(
                (cubo_amb, Vec3(dx, dy, dz), random.uniform(0, 6.28))
            )

    def _criar_moldura_3d(self, x_ini, y_ini, larg, alt):
        for x in range(x_ini, x_ini + larg):
            self.paredes.append(VisualBloco(x, y_ini, "MOLDURA", escala=0.84))
            self.paredes.append(VisualBloco(x, y_ini + alt - 1, "MOLDURA", escala=0.84))
        for y in range(y_ini + 1, y_ini + alt - 1):
            self.paredes.append(VisualBloco(x_ini, y, "MOLDURA", escala=0.84))
            self.paredes.append(VisualBloco(x_ini + larg - 1, y, "MOLDURA", escala=0.84))

    def alternar_tema(self):
        self.aplicar_tema((self.tema_atual + 1) % len(self.NOMES_TEMAS))

    def aplicar_tema(self, indice):
        self.tema_atual = indice
        self.parede_fundo.set_shader_input("modo_tema", indice)

        if indice == 1:
            # Studio Glass (Claro)
            window.color = color.rgb32(236, 240, 248)
            cor_celula = color.rgb32(218, 224, 236)
            cor_texto_aux = color.rgb32(35, 42, 58)
            SHADER_BLOCO_PBR.default_input["brilho_emissivo"] = 0.35
            self.campo_estelar.definir_visibilidade(False)
            self.post_process.ativar_bloom(intensidade=0.35, mintrigger=0.82)
        elif indice == 2:
            # Solar Vaporwave
            window.color = color.rgb32(22, 8, 38)
            cor_celula = color.rgb32(42, 18, 62)
            cor_texto_aux = color.rgb32(255, 190, 235)
            SHADER_BLOCO_PBR.default_input["brilho_emissivo"] = 1.05
            self.campo_estelar.definir_visibilidade(True)
            self.post_process.ativar_bloom(intensidade=0.95, mintrigger=0.58)
        else:
            # Cyber Neon (Padrao)
            window.color = color.rgb32(8, 12, 24)
            cor_celula = color.rgb32(20, 28, 46)
            cor_texto_aux = color.rgb32(165, 225, 255)
            SHADER_BLOCO_PBR.default_input["brilho_emissivo"] = 1.0
            self.campo_estelar.definir_visibilidade(True)
            self.post_process.ativar_bloom(intensidade=0.88, mintrigger=0.60)

        for cel in self.celulas_fundo_grid:
            cel.color = cor_celula
        self.legenda_controles.color = cor_texto_aux
        self.status_camera.color = cor_texto_aux
        self.titulo_proxima.color = cor_texto_aux
        self.titulo_reserva.color = cor_texto_aux

    def _configurar_camera(self):
        centro_x = (self.largura - 1) / 2
        centro_y = -(self.altura - 1) / 2
        camera.z = -58
        self.posicao_base_camera = Vec3(centro_x, centro_y, 0)
        self.rotacao_base_camera = Vec3(6, -10, 0)
        self.editor_camera = EditorCamera(
            position=self.posicao_base_camera,
            rotation=self.rotacao_base_camera,
        )
        self.editor_camera.target_z = -58

    def _configurar_iluminacao(self):
        centro_x = (self.largura - 1) / 2
        centro_y = -(self.altura - 1) / 2
        self.luz = DirectionalLight(
            position=(centro_x, centro_y, 0),
            shadow_map_resolution=Vec2(2048, 2048),
            shadows=True,
        )
        self.luz.look_at(self.luz.position + Vec3(1.5, -1.2, 1.4))

    def atualizar_camera(self, frame, gesto=None):
        altura_f, largura_f = frame.shape[:2]
        if self.textura_camera is None:
            self.textura_camera = PandaTexture()
            self.textura_camera.setup2dTexture(
                largura_f, altura_f, PandaTexture.T_unsigned_byte, PandaTexture.F_rgb
            )
            self.painel_camera.texture = Texture(self.textura_camera)
            self.painel_camera.enabled = True
            self.borda_camera.enabled = True

        if gesto is not None:
            if gesto.punhos_fechados:
                self.borda_camera.color = color.rgb32(0, 255, 130)
                self.status_camera.text = "ARRASTANDO  |  PUXAO RAPIDO = HARD DROP"
                if gesto.posicao_x is not None and gesto.posicao_y is not None:
                    self.alvo_parallax = Vec2(
                        (gesto.posicao_x - 0.5) * -8.0,
                        (gesto.posicao_y - 0.5) * 5.0,
                    )
            elif gesto.pinca_dupla:
                self.borda_camera.color = color.rgb32(255, 200, 0)
                self.status_camera.text = "PINCA DUPLA: RESERVA (HOLD)"
            elif gesto.pinca_direita or gesto.pinca_esquerda:
                self.borda_camera.color = color.rgb32(0, 230, 255)
                self.status_camera.text = "PINCA: ROTACIONANDO PECA"
            else:
                self.borda_camera.color = color.rgb32(70, 90, 125)
                self.status_camera.text = f"TEMA: {self.NOMES_TEMAS[self.tema_atual]}"
                self.alvo_parallax = Vec2(0, 0)

        self.textura_camera.setRamImage(cv2.flip(frame, 0))

    def _mostrar_evento_flutuante(self, texto_evento, estilo="OURO"):
        mapa_cores = {
            "OURO": color.rgb32(255, 205, 35),
            "CIANO": color.rgb32(0, 235, 255),
            "LARANJA": color.rgb32(255, 115, 35),
            "VERDE": color.rgb32(50, 245, 130),
        }
        aviso = Text(
            text=texto_evento,
            position=(-0.15, 0.04),
            scale=2.5,
            color=mapa_cores.get(estilo, color.orange),
        )
        aviso.animate_position((-0.15, 0.26), duration=0.9, curve=curve.out_cubic)
        aviso.animate_scale(3.1, duration=0.9, curve=curve.out_quad)
        destroy(aviso, delay=0.95)

    def _efeito_rastro_queda(self, rastros):
        for x, y_ini, y_fim, letra in rastros:
            altura_rastro = max(1, y_fim - y_ini)
            y_meio = (y_ini + y_fim) / 2.0
            cor_b = VisualBloco.CORES.get(letra, color.cyan)
            rastro = Entity(
                model="cube",
                color=color.rgba(cor_b.r, cor_b.g, cor_b.b, 0.65),
                position=(x, -y_meio, -0.18),
                scale=(0.85, altura_rastro, 0.5),
                unlit=True,
            )
            rastro.animate_scale((0.04, altura_rastro, 0.04), duration=0.3)
            rastro.animate_color(color.rgba(cor_b.r, cor_b.g, cor_b.b, 0), duration=0.3)
            destroy(rastro, delay=0.32)
        rastros.clear()

    def _efeito_impacto_pouso(self, impactos):
        for x, y, letra, forte in impactos:
            qtd = 8 if forte else 3
            cor_b = VisualBloco.CORES.get(letra, color.white)
            for _ in range(qtd):
                faisca = Entity(
                    model="quad",
                    texture=self.tex_flare,
                    color=cor_b,
                    position=(x, -y, -0.4),
                    scale=0.65 if forte else 0.4,
                    billboard=True,
                    unlit=True,
                )
                dx = x + random.uniform(-2.2, 2.2)
                dy = -y + random.uniform(0.3, 2.8)
                dz = random.uniform(-4.5, -0.8)
                faisca.animate_position((dx, dy, dz), duration=0.38, curve=curve.out_quad)
                faisca.animate_scale(0, duration=0.38)
                destroy(faisca, delay=0.4)

        if any(f for _, _, _, f in impactos):
            self.editor_camera.position = self.posicao_base_camera + Vec3(0, -0.6, 0)
            self.editor_camera.animate_position(self.posicao_base_camera, duration=0.18)
        impactos.clear()

    def _efeito_flash_linhas(self, linhas_y):
        centro_x = (self.largura - 1) / 2
        for y in linhas_y:
            barra = Entity(
                model="cube",
                color=color.white,
                position=(centro_x, -y, -0.7),
                scale=(self.largura, 0.95, 0.7),
                unlit=True,
            )
            barra.animate_scale((self.largura * 1.65, 0.04, 2.2), duration=0.4)
            destroy(barra, delay=0.42)

            onda = Entity(
                model="quad",
                texture=self.tex_flare,
                color=color.rgba32(0, 240, 255, 165),
                position=(centro_x, -y, -1.2),
                scale=(4, 1.5, 1),
                unlit=True,
            )
            onda.animate_scale((32, 7.0, 1), duration=0.45, curve=curve.out_cubic)
            onda.animate_color(color.rgba32(0, 240, 255, 0), duration=0.45)
            destroy(onda, delay=0.48)
        linhas_y.clear()

    def _explodir_cubos(self, cubos_explodindo):
        for x, y, letra in cubos_explodindo:
            bloco = VisualBloco(x, y, letra)
            destino_x = x + (x - 4.5) * 1.2 + random.uniform(-1.8, 1.8)
            destino_y = -y + random.uniform(-2.8, 4.8)
            destino_z = random.uniform(-28.0, -14.0)
            bloco.animate_position(
                (destino_x, destino_y, destino_z), duration=0.58, curve=curve.out_cubic
            )
            bloco.animate_rotation(
                (
                    random.uniform(-600, 600),
                    random.uniform(-600, 600),
                    random.uniform(-600, 600),
                ),
                duration=0.58,
            )
            bloco.animate_scale(0, duration=0.58, curve=curve.in_quad)
            destroy(bloco, delay=0.6)

            cor_b = VisualBloco.CORES.get(letra, color.white)
            for _ in range(3):
                flare = Entity(
                    model="quad",
                    texture=self.tex_flare,
                    color=cor_b,
                    position=(x, -y, -0.6),
                    scale=0.85,
                    billboard=True,
                    unlit=True,
                )
                flare.animate_position(
                    (
                        destino_x + random.uniform(-4, 4),
                        destino_y + random.uniform(-4, 4),
                        random.uniform(-34, -18),
                    ),
                    duration=0.5,
                )
                flare.animate_scale(0, duration=0.5)
                destroy(flare, delay=0.52)
        cubos_explodindo.clear()

        desvio = Vec3(random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), 0)
        self.editor_camera.position = self.posicao_base_camera + desvio
        self.editor_camera.animate_position(self.posicao_base_camera, duration=0.26)

    def _atualizar_vitrine(self, peca, pivô, lista_blocos, escala=0.86):
        for b in lista_blocos:
            destroy(b)
        lista_blocos.clear()
        if peca is None:
            return
        xs = [c.x for c in peca.cubos]
        ys = [c.y for c in peca.cubos]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        for c in peca.cubos:
            bloco = VisualBloco(
                (c.x - cx) * escala,
                (c.y - cy) * escala,
                peca.letra,
                escala=escala * 0.94,
                parent_entity=pivô,
            )
            lista_blocos.append(bloco)

    def fechar(self):
        self.audio.fechar()

    def atualizar(self, jogo):
        t = time.time()
        dt = time.dt

        # 0. Dispara efeitos sonoros estéreo polifônicos
        while jogo.sons_pendentes:
            nome_som, combo_som = jogo.sons_pendentes.pop(0)
            self.audio.tocar(nome_som, combo=combo_som)

        # 1. Campo estelar 3D + vitrines giratórias + cubos flutuantes
        self.campo_estelar.atualizar(dt, t)

        for idx, pivo in enumerate(self.pivos_proximas):
            pivo.rotation_y = math.sin(t * 1.6 + idx * 0.8) * 28
            pivo.rotation_x = math.cos(t * 1.2 + idx * 0.6) * 12
            pivo.y = (-2.5 - idx * 5.6) + math.sin(t * 2.4 + idx) * 0.20

        self.pivô_reserva.rotation_y = -math.sin(t * 1.6) * 28
        self.pivô_reserva.rotation_x = math.cos(t * 1.2) * 12
        self.pivô_reserva.y = -2.5 + math.cos(t * 2.4) * 0.20

        for cubo_amb, pos_base, fase in self.cubos_ambiente:
            cubo_amb.y = pos_base.y + math.sin(t * 1.4 + fase) * 0.65
            cubo_amb.rotation_y += dt * 22
            cubo_amb.rotation_x += dt * 14

        # 2. Cor reativa no shader de fundo e nos neons da arena
        cor_atual = VisualBloco.CORES.get(jogo.peca_atual.letra, color.cyan)
        self.parede_fundo.set_shader_input(
            "cor_acento", Vec3(cor_atual.r, cor_atual.g, cor_atual.b)
        )

        if jogo.grid.altura_pilha() >= 15 and math.sin(t * 11.0) > 0:
            cor_borda = color.rgb32(255, 35, 65)
        else:
            cor_borda = cor_atual

        self.neon_esq.color = lerp(self.neon_esq.color, cor_borda, min(1.0, dt * 8))
        self.neon_dir.color = self.neon_esq.color
        self.neon_chao.color = self.neon_esq.color

        # 3. Peça atual interpolada a 60+ FPS + Feixes de laser + Sombra Fantasma
        y_fantasma = jogo.y_de_aterrissagem() if not jogo.game_over else 0
        pulso_fantasma = 0.30 + 0.15 * (0.5 + 0.5 * math.sin(t * 6.5))

        for i, cubo in enumerate(jogo.peca_atual.cubos):
            x_alvo = jogo.peca_atual.origem[0] + cubo.x
            y_alvo = jogo.peca_atual.origem[1] + cubo.y
            pos_alvo = Vec3(x_alvo, -y_alvo, 0)

            bloco_p = self.blocos_peca_atual[i]
            bloco_p.color = cor_atual
            if (bloco_p.position - pos_alvo).length() > 3.5:
                bloco_p.position = pos_alvo
            else:
                bloco_p.position = lerp(bloco_p.position, pos_alvo, min(1.0, dt * 26))

            bloco_f = self.blocos_fantasma[i]
            feixe = self.feixes_laser[i]
            y_f = y_fantasma + cubo.y
            if (
                self.mostrar_fantasma
                and not jogo.game_over
                and y_fantasma > jogo.peca_atual.origem[1]
            ):
                bloco_f.enabled = True
                bloco_f.position = Vec3(x_alvo, -y_f, 0)
                bloco_f.color = cor_atual
                bloco_f.alpha = pulso_fantasma
                bloco_f.scale = 0.92 + 0.04 * math.sin(t * 6.5)

                dist_y = y_f - y_alvo
                if dist_y > 1:
                    feixe.enabled = True
                    feixe.color = color.rgba(cor_atual.r, cor_atual.g, cor_atual.b, 0.14)
                    feixe.position = Vec3(x_alvo, -(y_alvo + y_f) / 2, 0.25)
                    feixe.scale = Vec3(0.12, dist_y, 0.12)
                else:
                    feixe.enabled = False
            else:
                bloco_f.enabled = False
                feixe.enabled = False

        # 4. Efeitos especiais instantâneos
        if jogo.rastros_queda:
            self._efeito_rastro_queda(jogo.rastros_queda)
        if jogo.impactos_pouso:
            self._efeito_impacto_pouso(jogo.impactos_pouso)
        if jogo.linhas_flash:
            self._efeito_flash_linhas(jogo.linhas_flash)
        if jogo.cubos_explodindo:
            self._explodir_cubos(jogo.cubos_explodindo)
        while jogo.eventos_visuais:
            txt, est = jogo.eventos_visuais.pop(0)
            self._mostrar_evento_flutuante(txt, est)

        # 5. HUD com contador rolante e barra de nível
        self.pontos_exibidos = lerp(
            self.pontos_exibidos, float(jogo.pontos), min(1.0, dt * 12)
        )
        pontos_int = int(round(self.pontos_exibidos))
        progresso_nivel = (
            (jogo.linhas % 2)
            + (jogo.tempo_acumulado / max(0.01, jogo.intervalo_queda)) * 0.15
        ) / 2.0
        self.barra_nivel.scale_x = max(0.01, min(0.35, 0.35 * progresso_nivel))

        icone_som = "ON" if self.audio.musica_tocando else "MUTE"
        texto_hud = (
            f"PONTOS:  {pontos_int:06d}\n"
            f"RECORDE: {Jogo.RECORDE_SESSAO:06d}\n"
            f"LINHAS: {jogo.linhas}  |  NV: {jogo.nivel}  |  BGM: {icone_som}"
        )
        if jogo.combo > 1:
            texto_hud += f"\nCOMBO ATIVO: x{jogo.combo}!"
        if jogo.pausado:
            texto_hud += "\n>> PAUSADO [P] <<"
        elif jogo.game_over:
            texto_hud += "\n>> GAME OVER [R] <<"
        self.placar.text = texto_hud

        # 6. Atualiza fila de 3 Próximas Peças + Reserva (Hold)
        letras_fila = tuple(p.letra for p in jogo.fila_proximas)
        if letras_fila != self.ultimas_proximas_letras:
            self.ultimas_proximas_letras = letras_fila
            escalas = (0.88, 0.68, 0.56)
            for idx, (peca_f, esc_f) in enumerate(zip(jogo.fila_proximas, escalas)):
                self._atualizar_vitrine(
                    peca_f, self.pivos_proximas[idx], self.blocos_proximas[idx], esc_f
                )

        letra_res = jogo.peca_reserva.letra if jogo.peca_reserva else None
        if letra_res != self.ultima_reserva_letra:
            self.ultima_reserva_letra = letra_res
            self._atualizar_vitrine(
                jogo.peca_reserva, self.pivô_reserva, self.blocos_reserva, 0.88
            )

        # 7. Reconstrói apenas os blocos fixados quando a matriz muda
        estado_grid = tuple(tuple(linha) for linha in jogo.grid.celulas)
        if estado_grid == self.ultimo_grid:
            return
        self.ultimo_grid = estado_grid

        for bloco in self.blocos_fixos:
            destroy(bloco)
        self.blocos_fixos.clear()

        for y in range(jogo.grid.altura):
            for x in range(jogo.grid.largura):
                letra = jogo.grid.celulas[y][x]
                if letra is not None:
                    self.blocos_fixos.append(VisualBloco(x, y, letra))


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
        elif key == "space":
            jogo.queda_instantanea()
        elif key in ("c", "left shift", "right shift"):
            jogo.reservar_peca()
        elif key in ("w", "up arrow"):
            jogo.tentar_rotacionar(horario=True)
        elif key == "q":
            jogo.tentar_rotacionar(horario=False)
        elif key == "t":
            arena.alternar_tema()
        elif key == "m":
            arena.audio.alternar_musica()
        elif key == "g":
            arena.mostrar_fantasma = not arena.mostrar_fantasma
        elif key == "p":
            jogo.pausado = not jogo.pausado
        elif key == "r":
            jogo = Jogo()
        elif key == "escape":
            arena.fechar()

    def update():
        jogo.atualizar(time.dt)
        arena.atualizar(jogo)

    try:
        app.run()
    finally:
        arena.fechar()
