import numpy as np

try:
    import pygame

    PYGAME_DISPONIVEL = True
except ImportError:
    PYGAME_DISPONIVEL = False


NOTAS_HZ = {
    "A2": 110.00,
    "B2": 123.47,
    "C3": 130.81,
    "D3": 146.83,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "G#3": 207.65,
    "A3": 220.00,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "G#4": 415.30,
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "F5": 698.46,
    "G5": 783.99,
    "A5": 880.00,
    "C6": 1046.50,
    "E6": 1318.51,
    "G6": 1567.98,
    "PAUSA": 0.0,
}


class MotorAudioSynthwave:
    """Motor de audio estereo 44.1kHz com trilha Synthwave (Korobeiniki) e SFX polifonicos via NumPy + Pygame."""

    TAXA = 44100

    def __init__(self):
        self.ativo = False
        self.musica_tocando = False
        self.sons = {}
        self.canal_musica = None

        if not PYGAME_DISPONIVEL:
            return

        try:
            pygame.mixer.init(frequency=self.TAXA, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(16)
            self.canal_musica = pygame.mixer.Channel(0)
            self.ativo = True
            self._gerar_todos_sfx()
            self.som_musica = self._gerar_trilha_korobeiniki()
            self.iniciar_musica()
        except Exception as e:
            print(f"Aviso de audio: {e}")
            self.ativo = False

    def _empacotar_estereo(self, esq, dir_):
        estereo = np.column_stack((esq, dir_))
        estereo = np.clip(estereo * 32767.0, -32767, 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.ascontiguousarray(estereo))

    def _sweep_estereo(self, f_ini, f_fim, duracao, vol=0.35, pan=0.0, forma="hibrida"):
        n = max(1, int(self.TAXA * duracao))
        t = np.linspace(0.0, duracao, n, endpoint=False)
        progresso = np.linspace(0.0, 1.0, n, endpoint=False)
        freqs = f_ini + (f_fim - f_ini) * progresso
        fase = 2.0 * np.pi * np.cumsum(freqs) / self.TAXA

        if forma == "saw":
            onda = 2.0 * ((fase / (2.0 * np.pi)) % 1.0) - 1.0
        elif forma == "quadrada":
            onda = np.sign(np.sin(fase)) * 0.7 + np.sin(fase) * 0.3
        else:
            onda = (
                np.sin(fase) * 0.65
                + np.sin(fase * 2.005) * 0.25
                + np.sin(fase * 3.0) * 0.10
            )

        ataque = np.minimum(1.0, np.arange(n) / max(1.0, self.TAXA * 0.004))
        decaimento = np.exp(-3.5 * progresso)
        env = ataque * decaimento * vol
        sinal = onda * env

        ganho_esq = np.sqrt(0.5 * (1.0 - pan))
        ganho_dir = np.sqrt(0.5 * (1.0 + pan))
        return sinal * ganho_esq, sinal * ganho_dir

    def _gerar_todos_sfx(self):
        # Move
        e, d = self._sweep_estereo(620, 920, 0.045, vol=0.22, forma="hibrida")
        self.sons["mover"] = self._empacotar_estereo(e, d)

        # Rotate (FM + Stereo sweep)
        e1, d1 = self._sweep_estereo(380, 960, 0.09, vol=0.28, pan=-0.3, forma="saw")
        e2, d2 = self._sweep_estereo(570, 1440, 0.09, vol=0.22, pan=0.3, forma="hibrida")
        self.sons["girar"] = self._empacotar_estereo(e1 + e2, d1 + d2)

        # Soft landing
        e, d = self._sweep_estereo(170, 48, 0.11, vol=0.45, forma="hibrida")
        self.sons["pouso"] = self._empacotar_estereo(e, d)

        # Hard Drop (Laser zap + Sub-bass impact + Noise punch)
        e1, d1 = self._sweep_estereo(1400, 70, 0.16, vol=0.38, forma="saw")
        e2, d2 = self._sweep_estereo(140, 36, 0.16, vol=0.55, forma="hibrida")
        ruido = np.random.uniform(-0.18, 0.18, len(e1)) * np.exp(
            -np.linspace(0, 8, len(e1))
        )
        self.sons["hard_drop"] = self._empacotar_estereo(
            e1 + e2 + ruido, d1 + d2 + ruido
        )

        # Hold / Swap
        a1, b1 = self._sweep_estereo(523.25, 523.25, 0.07, vol=0.28, pan=-0.4)
        a2, b2 = self._sweep_estereo(783.99, 1046.5, 0.11, vol=0.32, pan=0.4)
        self.sons["reserva"] = self._empacotar_estereo(
            np.concatenate([a1, a2]), np.concatenate([b1, b2])
        )

        # Line clear arpeggios (pitch scales with combo 1..4)
        acordes_combo = [
            ("C5", "E5", "G5", "C6"),
            ("D5", "F5", "A5", "E6"),
            ("E5", "G5", "C6", "E6"),
            ("G5", "C6", "E6", "G6"),
        ]
        for idx, notas in enumerate(acordes_combo, start=1):
            partes_e, partes_d = [], []
            for i, nome_nota in enumerate(notas):
                f = NOTAS_HZ[nome_nota]
                dur = 0.065 if i < 3 else 0.18
                pan = -0.4 + 0.27 * i
                pe, pd = self._sweep_estereo(f, f * 1.004, dur, vol=0.34, pan=pan)
                partes_e.append(pe)
                partes_d.append(pd)
            self.sons[f"linha_{idx}"] = self._empacotar_estereo(
                np.concatenate(partes_e), np.concatenate(partes_d)
            )

        # TETRIS 4-line fanfare
        fanfarra = [
            ("C5", "G5", 0.07),
            ("E5", "C6", 0.07),
            ("G5", "E6", 0.08),
            ("C6", "G6", 0.28),
        ]
        fe, fd = [], []
        for n1, n2, dur in fanfarra:
            e_a, d_a = self._sweep_estereo(
                NOTAS_HZ[n1], NOTAS_HZ[n1], dur, vol=0.32, pan=-0.35, forma="saw"
            )
            e_b, d_b = self._sweep_estereo(
                NOTAS_HZ[n2], NOTAS_HZ[n2], dur, vol=0.32, pan=0.35, forma="hibrida"
            )
            fe.append(e_a + e_b)
            fd.append(d_a + d_b)
        self.sons["tetris"] = self._empacotar_estereo(
            np.concatenate(fe), np.concatenate(fd)
        )

        # Game Over
        ge, gd = self._sweep_estereo(440, 82, 0.55, vol=0.42, forma="saw")
        self.sons["gameover"] = self._empacotar_estereo(ge, gd)

    def _gerar_trilha_korobeiniki(self):
        """Sintetiza o tema classico do Tetris (Korobeiniki) em estilo Synthwave estereo com baixo e bateria."""
        bpm = 138.0
        semicolcheia = 60.0 / bpm / 2.0  # colcheia base

        # (Nota melodia, duracao em colcheias, Nota baixo raiz)
        partitura = [
            # Parte A1
            ("E5", 2, "E3"),
            ("B4", 1, "E3"),
            ("C5", 1, "E3"),
            ("D5", 2, "E3"),
            ("C5", 1, "E3"),
            ("B4", 1, "E3"),
            ("A4", 2, "A2"),
            ("A4", 1, "A2"),
            ("C5", 1, "A2"),
            ("E5", 2, "A2"),
            ("D5", 1, "A2"),
            ("C5", 1, "A2"),
            ("B4", 3, "G#3"),
            ("C5", 1, "G#3"),
            ("D5", 2, "E3"),
            ("E5", 2, "E3"),
            ("C5", 2, "A2"),
            ("A4", 2, "A2"),
            ("A4", 4, "A2"),
            # Parte A2
            ("PAUSA", 1, "D3"),
            ("D5", 2, "D3"),
            ("F5", 1, "D3"),
            ("A5", 2, "D3"),
            ("G5", 1, "D3"),
            ("F5", 1, "D3"),
            ("E5", 3, "C3"),
            ("C5", 1, "C3"),
            ("E5", 2, "C3"),
            ("D5", 1, "C3"),
            ("C5", 1, "C3"),
            ("B4", 2, "B2"),
            ("B4", 1, "B2"),
            ("C5", 1, "E3"),
            ("D5", 2, "E3"),
            ("E5", 2, "G#3"),
            ("C5", 2, "A2"),
            ("A4", 2, "A2"),
            ("A4", 4, "A2"),
        ]

        total_colcheias = sum(d for _, d, _ in partitura)
        duracao_total = total_colcheias * semicolcheia
        total_amostras = int(self.TAXA * duracao_total)

        canal_e = np.zeros(total_amostras, dtype=np.float32)
        canal_d = np.zeros(total_amostras, dtype=np.float32)

        cursor = 0
        passo_colcheia = int(self.TAXA * semicolcheia)

        for nota_mel, colcheias, nota_baixo in partitura:
            n_amostras = min(total_amostras - cursor, int(colcheias * passo_colcheia))
            if n_amostras <= 0:
                break
            t = np.arange(n_amostras, dtype=np.float32) / self.TAXA

            # Lead Super-Saw Estéreo desafinado
            f_mel = NOTAS_HZ[nota_mel]
            if f_mel > 0:
                env_m = np.minimum(1.0, t / 0.008) * np.exp(
                    -2.4 * t / max(0.1, colcheias * semicolcheia)
                )
                vibrato = 1.0 + 0.003 * np.sin(2.0 * np.pi * 5.5 * t)
                fase1 = 2.0 * np.pi * f_mel * 0.997 * vibrato * t
                fase2 = 2.0 * np.pi * f_mel * 1.003 * vibrato * t
                saw_e = (2.0 * ((fase1 / (2.0 * np.pi)) % 1.0) - 1.0) * 0.5 + np.sin(
                    fase1
                ) * 0.5
                saw_d = (2.0 * ((fase2 / (2.0 * np.pi)) % 1.0) - 1.0) * 0.5 + np.sin(
                    fase2
                ) * 0.5
                canal_e[cursor : cursor + n_amostras] += saw_e * env_m * 0.13
                canal_d[cursor : cursor + n_amostras] += saw_d * env_m * 0.13

            # Baixo Synthwave pulsante em oitavas a cada colcheia
            f_bx = NOTAS_HZ[nota_baixo]
            for sub in range(colcheias):
                ini_b = cursor + sub * passo_colcheia
                fim_b = min(total_amostras, ini_b + passo_colcheia)
                tam_b = fim_b - ini_b
                if tam_b <= 0:
                    continue
                tb = np.arange(tam_b, dtype=np.float32) / self.TAXA
                freq_oitava = f_bx if (sub % 2 == 0) else (f_bx * 2.0)
                env_b = np.minimum(1.0, tb / 0.005) * np.exp(-7.0 * tb)
                onda_b = (
                    np.sin(2.0 * np.pi * freq_oitava * tb) * 0.7
                    + np.sign(np.sin(2.0 * np.pi * freq_oitava * tb)) * 0.3
                )
                sinal_b = onda_b * env_b * 0.15
                canal_e[ini_b:fim_b] += sinal_b
                canal_d[ini_b:fim_b] += sinal_b

            cursor += n_amostras

        # Bateria eletrônica suave (Kick nos tempos fortes + Hi-hat nos contratempos)
        for idx_c in range(total_colcheias):
            ini_c = idx_c * passo_colcheia
            if idx_c % 2 == 0:
                tam_k = min(int(self.TAXA * 0.09), total_amostras - ini_c)
                if tam_k > 0:
                    tk = np.arange(tam_k, dtype=np.float32) / self.TAXA
                    fase_k = 2.0 * np.pi * np.cumsum(135.0 * np.exp(-28.0 * tk)) / self.TAXA
                    kick = np.sin(fase_k) * np.exp(-20.0 * tk) * 0.22
                    canal_e[ini_c : ini_c + tam_k] += kick
                    canal_d[ini_c : ini_c + tam_k] += kick
            else:
                tam_h = min(int(self.TAXA * 0.035), total_amostras - ini_c)
                if tam_h > 0:
                    th = np.arange(tam_h, dtype=np.float32) / self.TAXA
                    hat = (
                        np.random.uniform(-1.0, 1.0, tam_h).astype(np.float32)
                        * np.exp(-65.0 * th)
                        * 0.05
                    )
                    canal_e[ini_c : ini_c + tam_h] += hat * 0.8
                    canal_d[ini_c : ini_c + tam_h] += hat * 1.2

        # Eco Ping-Pong estéreo (Delay de 3 colcheias)
        atraso = int(passo_colcheia * 1.5)
        if atraso < total_amostras:
            eco_e = np.roll(canal_d, atraso) * 0.26
            eco_d = np.roll(canal_e, atraso) * 0.26
            canal_e += eco_e
            canal_d += eco_d

        return self._empacotar_estereo(canal_e * 0.75, canal_d * 0.75)

    def iniciar_musica(self):
        if self.ativo and self.canal_musica is not None:
            self.canal_musica.play(self.som_musica, loops=-1)
            self.canal_musica.set_volume(0.55)
            self.musica_tocando = True

    def alternar_musica(self):
        if not self.ativo or self.canal_musica is None:
            return
        if self.musica_tocando:
            self.canal_musica.pause()
            self.musica_tocando = False
        else:
            self.canal_musica.unpause()
            self.musica_tocando = True

    def tocar(self, nome, combo=1):
        if not self.ativo:
            return
        if nome == "linha":
            indice = max(1, min(4, combo))
            nome = f"linha_{indice}"
        som = self.sons.get(nome)
        if som is not None:
            canal = pygame.mixer.find_channel(True)
            if canal is not None and canal != self.canal_musica:
                canal.play(som)

    def fechar(self):
        if self.ativo:
            pygame.mixer.quit()
            self.ativo = False
