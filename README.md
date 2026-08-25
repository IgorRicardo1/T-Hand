T-Hand

Tetris 3D controlado por rastreamento de mãos via webcam. As pecas descem em um fosso tridimensional e o jogador usa gestos para mover e rotacionar.

Tecnologias

 Python
 Ursina Engine (motor 3D)
 MediaPipe (rastreamento de mãs)

Controles

 Duas mãos fechadas: move a peca 
 Pinca com a mao direita: rotaciona a peca horizontal
 Pinca com a mao esquerda: rotaciona a peca vertical

Estrutura

    tracker.py

HandTracker - Inicializa a webcam e o MediaPipe. Processa cada frame e identifica os gestos das maos.
Resultado_gesto - Armazena o resultado dos gestos detectados em um frame (punhos fechados, pinca esquerda, pinca direita).

    logica_jogo.py

Cubo_unico - Representa um unico cubo dentro de uma peca. Guarda sua posicao relativa (x, y, z).
Grid - Matriz tridimensional do campo de jogo. Controla colisoes, empilhamento e limpeza de camadas completas.
Pecas_possiveis - Define os formatos disponiveis das pecas 3D e suas rotacoes.

    graficos_3d.py

Visual_do_bloco - Representacao grafica de um cubo na tela usando Ursina (cor, posicao, textura).
Visual_do_Grid - Desenha a arena 3D (paredes, chao, iluminacao) e sincroniza a visualizacao com a logica do jogo.

main.py

Ponto de entrada. Instancia todas as classes, conecta os gestos da webcam a logica do jogo e roda o loop principal do Ursina.
