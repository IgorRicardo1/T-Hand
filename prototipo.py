import cv2
import mediapipe.python.solutions.hands as mp_hands
from ursina import *
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape
import math


# Inicializa a Engine
app = Ursina()

# 1. O MUNDO FÍSICO (Bullet)
mundo_fisico = BulletWorld()
mundo_fisico.setGravity(Vec3(0, -9.81, 0))

# 2. O CHÃO
# BulletBoxShape usa a *metade* do tamanho total nas medidas
shape_chao = BulletBoxShape(Vec3(5, 0.5, 0.5)) 
node_chao = BulletRigidBodyNode('Chao')
node_chao.addShape(shape_chao)
# Atrela o nó físico à cena
np_chao = scene.attachNewNode(node_chao)
np_chao.setPos(0, -4, 0)
mundo_fisico.attachRigidBody(node_chao)

# O visual do chão (a Entidade da Ursina acompanha a física usando reparent_to)
chao_visual = Entity(model='cube', texture='white_cube', scale=(10, 1, 1), color=color.gray)
chao_visual.reparent_to(np_chao)


# 3. NOSSA MÃO VIRTUAL E MEDIA PIPE
mao_virtual = Entity(model='sphere', color=color.green, scale=0.5, z=-1, visible=False)
pontos_mao = [Entity(model='sphere', color=color.red, scale=0.2, z=-1) for _ in range(21)]

cap = cv2.VideoCapture(0)
maos = mp_hands.Hands(max_num_hands=1)


# 4. AS PEÇAS
pecas_fisicas = []

def criar_peca(x, y, cor):
    shape_peca = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
    node_peca = BulletRigidBodyNode('Peca')
    node_peca.setMass(1.0) # Tem massa = cai com a gravidade!
    node_peca.setFriction(0.8) # Um pouco de atrito para não escorregar
    
    # TRUQUE DE MESTRE: Transformar o motor de física 3D em 2D
    node_peca.setLinearFactor(Vec3(1, 1, 0))  # Movimento apenas no X e Y
    node_peca.setAngularFactor(Vec3(0, 0, 1)) # Rotação apenas no eixo Z (Roll)
    
    node_peca.addShape(shape_peca)
    
    np_peca = scene.attachNewNode(node_peca)
    np_peca.setPos(x, y, 0)
    mundo_fisico.attachRigidBody(node_peca)
    
    visual = Entity(model='cube', texture='white_cube', color=cor)
    visual.reparent_to(np_peca)
    
    return np_peca

# Cria duas peças
peca1 = criar_peca(-2, 3, color.azure)
peca2 = criar_peca(2, 6, color.yellow)
pecas_fisicas.extend([peca1, peca2])

# Variável para saber qual peça estamos segurando no momento
peca_segurada = None

def update():
    global peca_segurada
    
    # Faz o motor de física agir a cada frame do jogo
    mundo_fisico.doPhysics(time.dt)
    
    # Lê a câmera a cada frame do jogo
    sucesso, frame = cap.read()
    if sucesso:
        frame = cv2.flip(frame, 1) 
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultados = maos.process(frame_rgb)
        
        if resultados.multi_hand_landmarks:
            mao = resultados.multi_hand_landmarks[0]
            
            for i, marco in enumerate(mao.landmark):
                pontos_mao[i].x = (marco.x - 0.5) * 20
                pontos_mao[i].y = -(marco.y - 0.5) * 15
                pontos_mao[i].enabled = True 
            
            mao_virtual.x = pontos_mao[9].x
            mao_virtual.y = pontos_mao[9].y
            
            distancia_pinca = ((mao.landmark[4].x - mao.landmark[8].x)**2 + (mao.landmark[4].y - mao.landmark[8].y)**2)**0.5
            fazendo_pinca = distancia_pinca < 0.05 
            
            # Lógica Híbrida: Tentar agarrar
            if fazendo_pinca:
                dx = pontos_mao[9].x - pontos_mao[0].x
                dy = pontos_mao[9].y - pontos_mao[0].y
                angulo = -math.degrees(math.atan2(dy, dx))
                
                if not peca_segurada:
                    for np in pecas_fisicas:
                        # Distância matemática (a Entity da Ursina e o Nó da Panda3D têm posições parecidas)
                        dist = ((mao_virtual.x - np.getX())**2 + (mao_virtual.y - np.getY())**2)**0.5
                        if dist < 2:
                            peca_segurada = np
                            # Torna a peça "Cinemática": A física de colisão age nos outros, 
                            # mas ela para de cair pela gravidade para obedecer a mão
                            peca_segurada.node().setKinematic(True)
                            break 
                else:
                    # Arrasta a peça
                    peca_segurada.setPos(mao_virtual.x, mao_virtual.y, 0)
                    # Aplica a rotação (-90 compensa para ficar em pé)
                    peca_segurada.setHpr(0, 0, angulo - 90)
                
            elif not fazendo_pinca:
                if peca_segurada:
                    # Devolve a gravidade para a peça ao soltar a mão
                    peca_segurada.node().setKinematic(False)
                    # Acorda a peça no motor de física (caso ela tenha "dormido")
                    peca_segurada.node().setActive(True)
                    peca_segurada = None
        
        else:
            for ponto in pontos_mao:
                ponto.enabled = False

# Configuração da câmera em Perspectiva (3D Real)
camera.position = (0, 3, -25)
camera.rotation_x = 10        

# Adiciona Iluminação
luz = DirectionalLight(shadows=True)
luz.look_at(Vec3(1, -1, 1))
AmbientLight(color=color.rgba(10, 10, 10, 0.1))

app.run()
