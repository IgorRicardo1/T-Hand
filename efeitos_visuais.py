import math
import random
from PIL import Image, ImageDraw, ImageFilter
from direct.filter.CommonFilters import CommonFilters
from ursina import Entity, Shader, Texture, Vec2, Vec3, application, camera, color, time


def gerar_textura_bloco_cristal(tamanho=256):
    """Gera textura procedural de alta definicao com chanfro, vidro interno e reflexo diagonal via Pillow."""
    img = Image.new("RGBA", (tamanho, tamanho), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Base escura metálica da borda
    draw.rectangle([0, 0, tamanho - 1, tamanho - 1], fill=(115, 120, 132, 255))

    # Chanfro intermediário luminoso
    m1 = int(tamanho * 0.065)
    draw.rounded_rectangle(
        [m1, m1, tamanho - 1 - m1, tamanho - 1 - m1],
        radius=int(tamanho * 0.08),
        fill=(235, 240, 250, 255),
    )

    # Sulco interno escuro de contraste
    m2 = int(tamanho * 0.13)
    draw.rounded_rectangle(
        [m2, m2, tamanho - 1 - m2, tamanho - 1 - m2],
        radius=int(tamanho * 0.06),
        fill=(155, 162, 178, 255),
    )

    # Núcleo cristalino brilhante
    m3 = int(tamanho * 0.175)
    draw.rounded_rectangle(
        [m3, m3, tamanho - 1 - m3, tamanho - 1 - m3],
        radius=int(tamanho * 0.05),
        fill=(255, 255, 255, 255),
    )

    # Brilho especular diagonal suave no vidro interno
    brilho = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d_brilho = ImageDraw.Draw(brilho)
    d_brilho.polygon(
        [
            (m3, m3),
            (tamanho - m3, m3),
            (m3, int(tamanho * 0.68)),
        ],
        fill=(255, 255, 255, 95),
    )
    brilho = brilho.filter(ImageFilter.GaussianBlur(radius=tamanho * 0.04))
    img = Image.alpha_composite(img, brilho)
    return Texture(img)


def gerar_textura_flare(tamanho=64):
    """Gera sprite radial suave com Gaussian Blur para particulas luminosas e estrelas."""
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    centro = tamanho // 2
    for r in range(centro, 0, -2):
        fator = (1.0 - (r / centro)) ** 2.2
        alfa = int(255 * fator)
        draw.ellipse(
            [centro - r, centro - r, centro + r, centro + r],
            fill=(255, 255, 255, alfa),
        )
    img = img.filter(ImageFilter.GaussianBlur(radius=2.2))
    return Texture(img)


def gerar_painel_glass_ui(largura=512, altura=320, raio=32, cor_borda=(0, 230, 255)):
    """Gera card UI glassmorphic com cantos arredondados anti-aliased."""
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [4, 4, largura - 5, altura - 5],
        radius=raio,
        fill=(14, 18, 28, 215),
        outline=(*cor_borda, 235),
        width=5,
    )
    # Faixa superior sutil de reflexo no vidro
    topo = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    dt = ImageDraw.Draw(topo)
    dt.rounded_rectangle(
        [10, 10, largura - 11, int(altura * 0.36)],
        radius=max(8, raio - 6),
        fill=(255, 255, 255, 18),
    )
    img = Image.alpha_composite(img, topo)
    return Texture(img)


SHADER_BLOCO_PBR = Shader(
    language=Shader.GLSL,
    name="bloco_pbr_overdrive",
    vertex="""#version 150
uniform struct {
    vec4 position;
    vec3 color;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[1];

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
uniform vec2 texture_scale;
uniform vec2 texture_offset;

in vec4 vertex;
in vec3 normal;
in vec4 p3d_Color;
in vec2 p3d_MultiTexCoord0;

out vec2 texcoords;
out vec4 vertex_color;
out vec3 vertex_position;
out vec3 normal_vector;
out vec4 shadow_coord[1];
out vec3 vertex_world_position;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * vertex;
    vertex_position = vec3(p3d_ModelViewMatrix * vertex);
    vertex_world_position = (p3d_ModelMatrix * vertex).xyz;
    normal_vector = normalize(p3d_NormalMatrix * normal);
    shadow_coord[0] = p3d_LightSource[0].shadowViewMatrix * vec4(vertex_position, 1.0);
    texcoords = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
    vertex_color = p3d_Color;
}
""",
    fragment="""#version 150
uniform struct {
    vec4 position;
    vec3 color;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[1];

uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform vec3 camera_world_position;
uniform float shadow_bias;
uniform vec4 shadow_color;
uniform float shadow_blur;
uniform int shadow_samples;
uniform float tempo_global;
uniform float brilho_emissivo;

in vec2 texcoords;
in vec4 vertex_color;
in vec3 normal_vector;
in vec3 vertex_position;
in vec4 shadow_coord[1];
in vec3 vertex_world_position;

out vec4 fragment_color;

void main() {
    vec4 tex = texture(p3d_Texture0, texcoords);
    vec4 base = tex * p3d_ColorScale * vertex_color;

    vec3 N = normalize(normal_vector);
    vec3 V = normalize(-vertex_position);
    vec3 L = normalize(p3d_LightSource[0].position.xyz - vertex_position * p3d_LightSource[0].position.w);
    vec3 H = normalize(L + V);

    float dist_borda = min(min(texcoords.x, 1.0 - texcoords.x), min(texcoords.y, 1.0 - texcoords.y));
    float nucleo = smoothstep(0.16, 0.42, dist_borda);
    float friso_neon = smoothstep(0.08, 0.12, dist_borda) - smoothstep(0.12, 0.16, dist_borda);

    float pulso = 0.5 + 0.5 * sin(tempo_global * 3.0 + vertex_world_position.x * 0.5 + vertex_world_position.y * 0.35);

    float NdotL = clamp(dot(N, L), 0.12, 1.0);
    float especular = pow(max(dot(N, H), 0.0), 48.0) * 0.85 + pow(max(dot(N, H), 0.0), 12.0) * 0.22;
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0) * 0.48;

    vec4 sc = shadow_coord[0];
    sc.z += shadow_bias;
    float s_total = 0.0;
    float n_samples = float(shadow_samples);
    float half_blur = shadow_blur * 0.5;
    for (int x = 0; x < shadow_samples; ++x) {
        for (int y = 0; y < shadow_samples; ++y) {
            float dx = float(x) * shadow_blur / n_samples - half_blur;
            float dy = float(y) * shadow_blur / n_samples - half_blur;
            vec4 c = sc;
            c.x += dx;
            c.y += dy;
            s_total += textureProj(p3d_LightSource[0].shadowMap, c);
        }
    }
    float fator_luz = s_total / (n_samples * n_samples);
    float sombra = mix(1.0 - shadow_color.a, 1.0, fator_luz);

    vec3 emissao = p3d_ColorScale.rgb * (nucleo * (0.20 + 0.12 * pulso) + friso_neon * 0.45) * brilho_emissivo;
    vec3 cor_final = base.rgb * (0.36 + 0.78 * NdotL * sombra)
                   + vec3(especular * fator_luz)
                   + (p3d_ColorScale.rgb * fresnel)
                   + emissao;

    fragment_color = vec4(cor_final, base.a);
}
""",
    default_input={
        "texture_scale": Vec2(1, 1),
        "texture_offset": Vec2(0, 0),
        "shadow_color": color.rgba(0, 0, 0, 0.50),
        "shadow_bias": 0.001,
        "shadow_blur": 0.0045,
        "shadow_samples": 4,
        "camera_world_position": Vec3.zero,
        "tempo_global": 0.0,
        "brilho_emissivo": 1.0,
    },
)
SHADER_BLOCO_PBR.continuous_input["camera_world_position"] = (
    lambda: camera.world_position
)
SHADER_BLOCO_PBR.continuous_input["tempo_global"] = lambda: time.time()


SHADER_FUNDO_CYBER = Shader(
    language=Shader.GLSL,
    name="fundo_cyber_shader",
    vertex="""#version 150
uniform struct {
    vec4 position;
    vec3 color;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[1];

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;

in vec4 vertex;
in vec2 p3d_MultiTexCoord0;

out vec2 uv;
out vec4 shadow_coord;
out vec3 world_pos;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * vertex;
    vec3 v_pos = vec3(p3d_ModelViewMatrix * vertex);
    world_pos = (p3d_ModelMatrix * vertex).xyz;
    shadow_coord = p3d_LightSource[0].shadowViewMatrix * vec4(v_pos, 1.0);
    uv = p3d_MultiTexCoord0;
}
""",
    fragment="""#version 150
uniform struct {
    vec4 position;
    vec3 color;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[1];

uniform float tempo;
uniform int modo_tema;
uniform vec3 cor_acento;

in vec2 uv;
in vec4 shadow_coord;
in vec3 world_pos;

out vec4 fragment_color;

void main() {
    // Sombra real projetada na parede de fundo
    vec4 sc = shadow_coord;
    sc.z += 0.0012;
    float s = 0.0;
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            vec4 c = sc;
            c.x += float(x) * 0.0018;
            c.y += float(y) * 0.0018;
            s += textureProj(p3d_LightSource[0].shadowMap, c);
        }
    }
    s /= 9.0;

    if (modo_tema == 1) {
        // Tema 1: Studio White Arquitetonico com ondas sutis e sombra marcada
        vec2 p = (uv - 0.5) * vec2(88.0, 56.0);
        float anel = sin(length(p) * 0.45 - tempo * 1.8) * 0.015;
        vec3 base = vec3(0.95, 0.96, 0.98) + anel;
        float fator_sombra = mix(0.54, 1.0, s);
        fragment_color = vec4(base * fator_sombra, 1.0);
        return;
    }

    if (modo_tema == 2) {
        // Tema 2: Solar Vaporwave Outrun
        float grad = clamp(uv.y, 0.0, 1.0);
        vec3 ceu_baixo = vec3(0.95, 0.25, 0.55);
        vec3 ceu_meio = vec3(0.28, 0.08, 0.45);
        vec3 ceu_topo = vec3(0.05, 0.02, 0.16);
        vec3 cor = mix(ceu_baixo, ceu_meio, smoothstep(0.0, 0.48, grad));
        cor = mix(cor, ceu_topo, smoothstep(0.45, 1.0, grad));

        // Sol Synthwave listrado no horizonte
        vec2 p_sol = (uv - vec2(0.5, 0.44)) * vec2(1.6, 1.0);
        float dist_sol = length(p_sol);
        if (dist_sol < 0.22) {
            float listra = step(0.18, fract(uv.y * 28.0 - tempo * 0.35)) + smoothstep(0.42, 0.52, uv.y);
            if (listra > 0.5) {
                vec3 cor_sol = mix(vec3(1.0, 0.2, 0.5), vec3(1.0, 0.88, 0.2), (uv.y - 0.22) / 0.44);
                cor = mix(cor, cor_sol, smoothstep(0.22, 0.205, dist_sol));
            }
        }

        // Grade neon animada
        vec2 g = vec2(world_pos.x * 0.35, world_pos.y * 0.35 + tempo * 0.8);
        float gx = smoothstep(0.94, 1.0, abs(cos(g.x * 3.14159)));
        float gy = smoothstep(0.94, 1.0, abs(cos(g.y * 3.14159)));
        cor += vec3(1.0, 0.3, 0.8) * max(gx, gy) * 0.22 * (1.0 - grad * 0.6);
        cor *= mix(0.62, 1.0, s);
        fragment_color = vec4(cor, 1.0);
        return;
    }

    // Tema 0 (Padrao): Cyber Neon Cosmos (estilo Tetris Effect)
    vec2 p = uv - 0.5;
    float d = length(p);
    float nebulosa1 = sin(world_pos.x * 0.09 + tempo * 0.5) * cos(world_pos.y * 0.09 - tempo * 0.4);
    float nebulosa2 = sin((world_pos.x - world_pos.y) * 0.06 + tempo * 0.7);

    vec3 fundo = vec3(0.03, 0.045, 0.10);
    fundo += vec3(0.02, 0.10, 0.22) * (0.5 + 0.5 * nebulosa1);
    fundo += cor_acento * 0.12 * (0.5 + 0.5 * nebulosa2) * (1.0 - d * 0.9);

    // Grade holografica sutil com ondas de pulso
    vec2 grade = fract(vec2(world_pos.x * 0.25, world_pos.y * 0.25 - tempo * 0.25));
    float linha_x = 1.0 - smoothstep(0.0, 0.045, min(grade.x, 1.0 - grade.x));
    float linha_y = 1.0 - smoothstep(0.0, 0.045, min(grade.y, 1.0 - grade.y));
    float pulso_radial = 0.4 + 0.6 * (0.5 + 0.5 * sin(length(world_pos.xy - vec2(4.5, -9.5)) * 0.22 - tempo * 2.4));

    fundo += cor_acento * max(linha_x, linha_y) * 0.14 * pulso_radial;
    fundo *= mix(0.55, 1.0, s);
    fragment_color = vec4(fundo, 1.0);
}
""",
    default_input={
        "tempo": 0.0,
        "modo_tema": 0,
        "cor_acento": Vec3(0.0, 0.85, 1.0),
    },
)
SHADER_FUNDO_CYBER.continuous_input["tempo"] = lambda: time.time()


class GerenciadorPostProcess:
    """Ativa HDR Bloom real via GPU usando CommonFilters do Panda3D."""

    def __init__(self):
        self.filtros = None
        self.bloom_ativo = False
        try:
            self.filtros = CommonFilters(application.base.win, application.base.cam)
            self.ativar_bloom(intensidade=0.85)
        except Exception as e:
            print(f"Aviso Bloom: {e}")

    def ativar_bloom(self, intensidade=0.85, mintrigger=0.62):
        if self.filtros is None:
            return
        try:
            self.filtros.setBloom(
                blend=(0.3, 0.4, 0.3, 0.0),
                mintrigger=mintrigger,
                maxtrigger=1.0,
                desat=0.15,
                intensity=intensidade,
                size="medium",
            )
            self.bloom_ativo = True
        except Exception:
            self.bloom_ativo = False


class CampoEstelar3D:
    """Sistema continuo de particulas luminosas flutuando em 3D ao redor da arena."""

    def __init__(self, textura_flare, quantidade=55):
        self.estrelas = []
        cores_estrelas = [
            color.rgb32(0, 240, 255),
            color.rgb32(200, 120, 255),
            color.rgb32(255, 210, 90),
            color.rgb32(100, 255, 180),
        ]
        for _ in range(quantidade):
            pos = Vec3(
                random.uniform(-28, 36),
                random.uniform(-34, 14),
                random.uniform(-12, 2.2),
            )
            # Evita colocar estrelas bem na frente do tabuleiro 10x20
            if -2 <= pos.x <= 12 and -22 <= pos.y <= 2 and pos.z < 0.8:
                pos.x += random.choice([-16, 18])

            escala_base = random.uniform(0.22, 0.65)
            ent = Entity(
                model="quad",
                texture=textura_flare,
                position=pos,
                scale=escala_base,
                color=random.choice(cores_estrelas),
                billboard=True,
                unlit=True,
            )
            vel_y = random.uniform(0.35, 1.4)
            fase = random.uniform(0, 6.28)
            self.estrelas.append([ent, vel_y, escala_base, fase])

    def definir_visibilidade(self, visivel):
        for ent, _, _, _ in self.estrelas:
            ent.enabled = visivel

    def atualizar(self, dt, t):
        for item in self.estrelas:
            ent, vel_y, esc, fase = item
            if not ent.enabled:
                continue
            ent.y += vel_y * dt
            if ent.y > 15:
                ent.y = -35
            ent.scale = esc * (0.65 + 0.40 * (0.5 + 0.5 * math.sin(t * 2.6 + fase)))
