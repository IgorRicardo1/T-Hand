# T-Hand (Overdrive 3D Edition)

Tetris com visual 3D avançado controlado por rastreamento de mãos via webcam. Inclui shaders GLSL customizados, pós-processamento HDR Bloom, 3 temas visuais em tempo real, trilha sonora Synthwave procedural em estéreo (Korobeiniki) e efeitos de partículas.

## Como executar

### 1. Instalar o Python (3.12 ou superior)

Verifique no terminal se o Python já está instalado:

```powershell
python --version
```

Caso não tenha o Python (ou a versão seja inferior à 3.12), instale de uma das formas abaixo:
- **Pelo instalador oficial**: baixe em https://www.python.org/downloads/ e, na primeira tela da instalação no Windows, **marque a opção `"Add python.exe to PATH"`** antes de clicar em *Install Now*.
- **Pelo terminal do Windows (winget)**: rode `winget install Python.Python.3.12`.

Depois de instalar, feche e abra o terminal novamente para o comando `python` ser reconhecido.

### 2. Configurar o ambiente virtual e dependências

Na raiz do projeto, crie um ambiente virtual com `python -m venv .venv`, ative-o (no Windows: `.\.venv\Scripts\Activate.ps1`) e instale as dependências com `pip install -r requirements.txt`. Se o PowerShell bloquear a ativação, rode antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

O MediaPipe já instala o OpenCV, então não precisa instalar o `opencv-python` separado (os dois dão conflito). O modelo `hand_landmarker.task` já acompanha o projeto para execução offline.

### 3. Executar e testar

Com o ambiente virtual ativado:
- **Jogo completo (3D + Webcam + Áudio)**: `python main.py`
- Versão 3D com teclado: `python graficos_3d.py`
- Lógica pelo terminal: `python logica_jogo.py`
- Rastreamento AR da webcam isolado: `python tracker.py` (ESC fecha a janela).

## Controles

### Gestos na Webcam
 - **Duas mãos fechadas**: arrasta a peça para a esquerda/direita ou para baixo;
 - **Puxão rápido para baixo (punhos fechados)**: *Hard Drop* (queda instantânea);
 - **Pinça com a mão direita**: rotaciona a peça no sentido horário;
 - **Pinça com a mão esquerda**: rotaciona a peça no sentido anti-horário;
 - **Pinça dupla (as duas mãos ao mesmo tempo)**: guarda/troca a peça na Reserva (*Hold*).

### Atalhos de Teclado
 - `A` / `D` ou Setas: mover horizontalmente | `S` / Seta Baixo: descer suave;
 - `W` / Seta Cima: girar horário | `Q`: girar anti-horário;
 - `Espaço`: *Hard Drop* | `C` ou `Shift`: Reserva (*Hold*);
 - `T`: alternar entre os 3 temas 3D (`CYBER NEON`, `STUDIO GLASS`, `SOLAR VAPORWAVE`);
 - `M`: ativar/mutar música Synthwave | `G`: ativar/desativar peça fantasma;
 - `P`: pausar | `R`: reiniciar | `ESC`: sair.

## Estrutura

- `main.py` — Ponto de entrada; integra os gestos em tempo real da thread da webcam com a lógica e a cena 3D.
- `logica_jogo.py` — Regras oficiais (*7-Bag Randomizer*, fila das 3 próximas peças, *Hold*, *Wall Kick*, *Combos*, *Back-to-Back Tetris* e *Perfect Clear*).
- `graficos_3d.py` — Arena 3D, vitrines holográficas giratórias, interpolação a 60+ FPS, explosões e HUD.
- `efeitos_visuais.py` — Shaders GLSL (`SHADER_BLOCO_PBR` e `SHADER_FUNDO_CYBER`), pós-processamento GPU HDR Bloom (`CommonFilters`), texturas procedurais via Pillow e campo estelar 3D.
- `audio_synth.py` — Sintetizador estéreo 44.1 kHz (`NumPy` + `pygame.mixer`) que gera a trilha Synthwave *Korobeiniki* e 16 canais de SFX em memória.
- `tracker.py` — Captura assíncrona em thread dedicada com MediaPipe e HUD de Realidade Aumentada em OpenCV.
