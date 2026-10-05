# T-Hand

Tetris com visual 3D controlado por rastreamento de mãos via webcam. As peças descem por um campo e o jogador usa gestos para mover e rotacionar.


## Tecnologias

 - Python;
 - Ursina Engine (motor 3D);
 - MediaPipe (rastreamento de mãos).

## Controles

 - Duas mãos fechadas: move a peça para a esquerda ou para a direita;
 - Pinça com a mão direita: rotaciona a peça no sentido horário;
 - Pinça com a mão esquerda: rotaciona a peça no sentido anti-horário.

## Estrutura

➔```tracker.py```

- HandTracker - Inicializa a webcam e o MediaPipe. Processa cada frame e identifica os gestos das mãos;
- ResultadoGesto - Armazena o resultado dos gestos detectados em um frame (punhos fechados, pinça esquerda, pinça direita).

➔```logica_jogo.py```

Não depende do Ursina, o que permite testar a lógica isoladamente.

- CuboUnico - Representa um único cubo dentro de uma peça. Guarda sua posição relativa (x, y);
- PecasPossiveis - Define os formatos disponíveis das peças (os 7 tetrominós clássicos: I, O, T, S, Z, J, L);
- Peca - Uma peça em jogo: formato, posição no campo e rotação (90° no plano). Sabe se mover e rotacionar;
- Grid - Matriz 2D do campo de jogo contendo apenas as células já fixadas. Controla colisões, fixação de peças e limpeza de linhas completas;
- Jogo - Orquestra a partida. Guarda o Grid, a peça atual e a próxima peça, controla a queda, a pontuação e o fim de jogo.

Ao encostar no fundo ou em outra peça, a peça atual é gravada no Grid (seus cubos viram células da matriz e ela deixa de existir como objeto) e a próxima peça assume seu lugar. Assim, sempre existe exatamente uma peça em movimento.

➔```graficos_3d.py```

- VisualBloco - Representação gráfica de um cubo na tela usando Ursina (cor, posição, textura);
- VisualGrid - Desenha a arena 3D (paredes, chão, iluminação) e sincroniza a visualização com a lógica do jogo (células do Grid e peça atual).

➔```main.py```

- Ponto de entrada. Instancia todas as classes, conecta os gestos da webcam à lógica do jogo e roda o loop principal do Ursina.
