import cv2
import mediapipe.python.solutions.hands as mp_hands
from ursina import *
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape
import math
import random


app = Ursina()

# ============================================================
# MUNDO FÍSICO
# ============================================================
mundo_fisico = BulletWorld()
mundo_fisico.setGravity(Vec3(0, -9.81, 0))


# ============================================================
# CENÁRIO (Chão + Paredes)
# ============================================================
def criar_estatico(nome, shape, pos, escala_visual, cor):
    """Cria um corpo rígido estático (sem massa) com visual atrelado."""
    node = BulletRigidBodyNode(nome)
    node.addShape(shape)
    node.setFriction(1.0)
    np_node = scene.attachNewNode(node)
    np_node.setPos(pos)
    mundo_fisico.attachRigidBody(node)

    visual = Entity(model='cube', texture='white_cube', scale=escala_visual, color=cor)
    visual.reparent_to(np_node)
    return np_node

# Chão (BulletBoxShape usa metade das dimensões reais)
criar_estatico('Chao', BulletBoxShape(Vec3(5, 0.5, 0.5)), Vec3(0, -4, 0), (10, 1, 1), color.gray)

# Paredes laterais
shape_parede = BulletBoxShape(Vec3(0.25, 10, 0.5))
criar_estatico('ParedeEsq', shape_parede, Vec3(-5.25, 6, 0), (0.5, 20, 1), color.dark_gray)
criar_estatico('ParedeDir', shape_parede, Vec3(5.25, 6, 0), (0.5, 20, 1), color.dark_gray)


# ============================================================
# MÃO VIRTUAL + MEDIAPIPE
# ============================================================
mao_virtual = Entity(visible=False)
pontos_mao = [Entity(model='sphere', color=color.red, scale=0.2, z=-1) for _ in range(21)]

cap = cv2.VideoCapture(0)
maos = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)


# ============================================================
# PEÇAS
# ============================================================
pecas_fisicas = []
cores_pecas = [color.azure, color.yellow, color.lime, color.magenta, color.orange, color.cyan]

def criar_peca(x, y, cor):
    """Cria uma peça com corpo rígido dinâmico, travada no plano 2D."""
    shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
    node = BulletRigidBodyNode('Peca')
    node.setMass(1.0)
    node.setFriction(0.8)
    node.setRestitution(0.05)
    node.setLinearDamping(0.1)
    node.setAngularDamping(0.3)
    node.setLinearFactor(Vec3(1, 1, 0))
    node.setAngularFactor(Vec3(0, 0, 1))
    node.addShape(shape)

    np_peca = scene.attachNewNode(node)
    np_peca.setPos(x, y, 0)
    mundo_fisico.attachRigidBody(node)

    visual = Entity(model='cube', texture='white_cube', color=cor)
    visual.reparent_to(np_peca)

    np_peca.setPythonTag('visual', visual)
    np_peca.setPythonTag('cor_original', cor)

    return np_peca

peca1 = criar_peca(-2, 3, color.azure)
peca2 = criar_peca(2, 6, color.yellow)
pecas_fisicas.extend([peca1, peca2])


# ============================================================
# ESTADO DO JOGO
# ============================================================
peca_segurada = None
pinca_ativa = False  # Flag com histerese


# ============================================================
# LOOP PRINCIPAL
# ============================================================
def update():
    global peca_segurada, pinca_ativa

    # Avança a física com substeps para maior estabilidade
    mundo_fisico.doPhysics(time.dt, 5, 1.0 / 180.0)

    sucesso, frame = cap.read()
    if not sucesso:
        return

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = maos.process(frame_rgb)

    # Se não detectou mão, esconde os pontos e sai
    if not resultados.multi_hand_landmarks:
        for ponto in pontos_mao:
            ponto.enabled = False
        return

    mao = resultados.multi_hand_landmarks[0]

    # Atualiza os 21 landmarks visuais
    for i, marco in enumerate(mao.landmark):
        pontos_mao[i].x = (marco.x - 0.5) * 20
        pontos_mao[i].y = -(marco.y - 0.5) * 15
        pontos_mao[i].enabled = True

    # Posição do centro da palma (landmark 9)
    mao_virtual.x = pontos_mao[9].x
    mao_virtual.y = pontos_mao[9].y

    # Detecção de pinça com histerese (evita flickering)
    dist_pinca = (
        (mao.landmark[4].x - mao.landmark[8].x) ** 2
        + (mao.landmark[4].y - mao.landmark[8].y) ** 2
    ) ** 0.5

    if not pinca_ativa and dist_pinca < 0.04:
        pinca_ativa = True
    elif pinca_ativa and dist_pinca > 0.07:
        pinca_ativa = False

    # Ângulo do pulso (entre landmark 0 e 9)
    dx = pontos_mao[9].x - pontos_mao[0].x
    dy = pontos_mao[9].y - pontos_mao[0].y
    angulo = -math.degrees(math.atan2(dy, dx))

    # --- LÓGICA DE AGARRAR / SOLTAR ---
    if pinca_ativa:

        if not peca_segurada:
    
            # Procura a peça mais próxima dentro do alcance
            menor_dist = float('inf')
            mais_proxima = None
    
            for np_peca in pecas_fisicas:
                dist = (
                    (mao_virtual.x - np_peca.getX()) ** 2
                    + (mao_virtual.y - np_peca.getY()) ** 2
                ) ** 0.5
    
                if dist < 2 and dist < menor_dist:
                    menor_dist = dist
                    mais_proxima = np_peca

            if mais_proxima:
                peca_segurada = mais_proxima
                peca_segurada.node().setKinematic(True)
                visual = peca_segurada.getPythonTag('visual')
    
                if visual:
                    visual.color = color.orange
    
        else:
            # Arrasta e rotaciona a peça segurada
            peca_segurada.setPos(mao_virtual.x, mao_virtual.y, 0)
            peca_segurada.setHpr(0, 0, angulo - 90)
    
    else:

        if peca_segurada:
            # Devolve a peça ao controle da física
            peca_segurada.node().setKinematic(False)
            peca_segurada.node().setActive(True)
            
            # Restaura a cor original
            visual = peca_segurada.getPythonTag('visual')
            cor_original = peca_segurada.getPythonTag('cor_original')
            if visual and cor_original:
                visual.color = cor_original

            peca_segurada = None


def input(key):
    """Spawna uma nova peça ao pressionar ESPAÇO."""
    if key == 'space':
        cor = random.choice(cores_pecas)
        nova = criar_peca(random.uniform(-3, 3), 8, cor)
        pecas_fisicas.append(nova)


# ============================================================
# CÂMERA E ILUMINAÇÃO
# ============================================================
camera.position = (0, 3, -25)
camera.rotation_x = 10

luz = DirectionalLight(shadows=True)
luz.look_at(Vec3(1, -1, 1))
AmbientLight(color=color.rgba(10, 10, 10, 0.1))

# HUD
Text(text='ESPACO = Nova Peca', position=(-0.85, 0.45), scale=1.5, color=color.white)

app.run()
