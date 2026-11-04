from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

import math
import urllib.request
import cv2

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.framework.formats import landmark_pb2

URL_MODELO = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
CAMINHO_MODELO = Path(__file__).with_name("hand_landmarker.task")


LIMIAR_PINCA = 0.35          # Proporção (distância polegar-indicador / tamanho da mão) para ativar pinça
LIMIAR_PUNHO = 1.00          # Tolerância para considerar dedo dobrado (< 1.0 mais rígido, > 1.0 mais permissivo)
PASSO_TIMESTAMP_MS = 33      # Incremento em ms por frame (~30 FPS)

LM_PULSO = 0
LM_POLEGAR_PONTA = 4
LM_INDICADOR_PONTA = 8
LM_CENTRO_PALMA = 9
PARES_DEDOS_PUNHO = ((8, 6), (12, 10), (16, 14), (20, 18))  # (ponta, articulacao_intermediaria)

class TipoGesto(StrEnum):
    NENHUM = "NENHUM"
    PUNHOS_FECHADOS = "PUNHOS_FECHADOS"
    PINCA_DIREITA = "PINCA_DIREITA"
    PINCA_ESQUERDA = "PINCA_ESQUERDA"

class LeituraGesto(NamedTuple):
    gesto: TipoGesto = TipoGesto.NENHUM
    posicao_x: float | None = None


class HandTracker:
    def __init__(self, camera_index=0):
        if not CAMINHO_MODELO.exists():
            urllib.request.urlretrieve(URL_MODELO, CAMINHO_MODELO)

        self.cap = cv2.VideoCapture(camera_index)
        self.timestamp = 0
        self._pinca_anterior = {"Left": False, "Right": False}
        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(CAMINHO_MODELO)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)

    
    def _distancia(self, p1, p2) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y)
    
    def _eh_pinca(self, mao, tamanho_mao: float) -> bool:
        dist_pinca = self._distancia(mao[LM_POLEGAR_PONTA], mao[LM_INDICADOR_PONTA])
        return dist_pinca < (tamanho_mao * LIMIAR_PINCA)
    
    def _eh_punho_fechado(self, mao) -> bool:
        pulso = mao[LM_PULSO]
        return all(
            self._distancia(mao[ponta], pulso) < (self._distancia(mao[artic], pulso) * LIMIAR_PUNHO)
            for ponta, artic in PARES_DEDOS_PUNHO
        )
    
    def detectar_gesto(self, resultado_mp) -> LeituraGesto:
        if not resultado_mp.hand_landmarks:
            self._pinca_anterior["Left"] = False
            self._pinca_anterior["Right"] = False
            return LeituraGesto()
        
        maos_fechadas_x = []
        pinca_atual = {"Left": False, "Right": False}
        
        for mao, info_mao in zip(resultado_mp.hand_landmarks, resultado_mp.handedness):
            lado = info_mao[0].category_name
            tamanho_mao = self._distancia(mao[LM_PULSO], mao[LM_CENTRO_PALMA])

            # Punho fecho tem prioridade sobre a pinça
            if self._eh_punho_fechado(mao):
                maos_fechadas_x.append(mao[LM_CENTRO_PALMA].x)
            elif self._eh_pinca(mao, tamanho_mao):
                pinca_atual[lado] = True

        disparou_esq = pinca_atual["Left"] and not self._pinca_anterior["Left"]
        disparou_dir = pinca_atual["Right"] and not self._pinca_anterior["Right"]
        self._pinca_anterior = pinca_atual

        if len(maos_fechadas_x) == 2:
            posicao_x_media = sum(maos_fechadas_x) / 2.0
            return LeituraGesto(TipoGesto.PUNHOS_FECHADOS, posicao_x_media)

        if disparou_dir:
            return LeituraGesto(TipoGesto.PINCA_DIREITA, None)

        if disparou_esq:
            return LeituraGesto(TipoGesto.PINCA_ESQUERDA, None)

        return LeituraGesto()

    def ler_frame(self) -> tuple[cv2.typing.MatLike | None, LeituraGesto]:
        sucesso, frame = self.cap.read()

        if not sucesso:
            return None, LeituraGesto()

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagem_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self.timestamp += PASSO_TIMESTAMP_MS
        resultado_mp = self.detector.detect_for_video(imagem_mp, self.timestamp)

        for mao in resultado_mp.hand_landmarks:
            proto_mao = landmark_pb2.NormalizedLandmarkList()
            proto_mao.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=p.x, y=p.y, z=p.z)
                for p in mao
            ])
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                proto_mao,
                mp.solutions.hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style(),
            )

        return frame, self.detectar_gesto(resultado_mp)

    def fechar(self):
        self.cap.release()
        self.detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    tracker = HandTracker()

    while True:
        frame, (gesto, pos_x) = tracker.ler_frame()
        if frame is None:
            break

        print(f"Gesto: {gesto}" + (f" | X: {pos_x:.2f}" if pos_x is not None else ""))

        cv2.imshow("T-Hand", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    tracker.fechar()
