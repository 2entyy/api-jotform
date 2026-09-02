# video-variator

Editor de vídeo local, assistido por IA, para preparar Reels a partir de um vídeo base:
transcrição, sugestão de gancho para a abertura, vários estilos de legenda com
pré-visualização, música de fundo com ducking automático, um "crítico" que pontua a
abertura, uma caixa de comandos em linguagem natural ("Pedir à IA"), e no fim, geração de
várias variações subtis do vídeo aprovado para testar em Reels.

Tudo corre na tua máquina: transcrição com Whisper local, renderização com ffmpeg, sem
contas, sem hosting, sem chaves de API obrigatórias.

## O que a app faz

1. **Sobes um vídeo.** É transcrito localmente (Whisper), com timestamps por segmento e
   por palavra.
2. **Sugestão de gancho**: a partir das palavras mais frequentes na transcrição, gera
   várias opções de título/legenda chamativa para a abertura (ex: "A VERDADE SOBRE...").
3. **Estilos de legenda**: 6 presets — Discreto, Editorial, Impacto, Karaoke, Uma palavra,
   Manuscrito — cada um com fonte/cor/posição próprias; Karaoke e Uma palavra destacam
   palavra a palavra, sincronizadas com a fala. Podes gerar um "lote" de pré-visualizações
   curtas para veres como cada estilo fica antes de escolheres.
4. **Corte manual** (início/fim) e **velocidade** ajustável.
5. **Música de fundo** opcional, com volume automaticamente reduzido ("ducking") por cima
   da fala.
6. **Crítico de IA**: analisa os primeiros segundos da transcrição e dá uma pontuação
   ("Força X/10") com sugestões concretas para reforçar o gancho.
7. **Pedir à IA**: caixa de comandos em português — "tira a música", "gancho mais forte",
   "estilo karaoke", "acelera" — que edita o projeto diretamente.
8. **Aprovar e renderizar**: gera o vídeo final com tudo aplicado.
9. **Variações para Reels**: a partir do vídeo aprovado, gera N cópias quase-idênticas
   com pequenos ajustes aleatórios de velocidade, cor e enquadramento, para testares
   várias publicações sem repostares exatamente o mesmo ficheiro.

Se tiveres o [Ollama](https://ollama.com) a correr localmente, o crítico e o "Pedir à IA"
usam-no automaticamente para respostas mais ricas; caso contrário usam heurísticas locais
— a app funciona por completo sem ele.

## Arquitetura

```
backend/    FastAPI + Whisper local + ffmpeg (a API e o motor de edição)
frontend/   React + Vite (a interface: transcrição, timeline, assistente)
video_variator/   motor original de variações (velocidade/cor/crop), reutilizado
                   pelo backend para o passo "Variações para Reels"; também
                   continua a funcionar como CLI standalone (ver abaixo)
```

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- [`ffmpeg`](https://ffmpeg.org/) e `ffprobe` instalados e no `PATH`
- Uma fonte `.ttf` (o backend procura DejaVu Sans Bold / Liberation Sans Bold)
- Opcional: [Ollama](https://ollama.com) a correr em `localhost:11434` para respostas de
  IA mais ricas no crítico e no "Pedir à IA"

## Instalação e arranque

**Backend** (a partir da raiz do repositório, para que os pacotes `backend` e
`video_variator` sejam ambos importáveis):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

A primeira transcrição descarrega o modelo Whisper escolhido (fica em cache local em
`~/.cache/whisper`); depois disso corre offline.

**Frontend** (noutro terminal):

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. O frontend fala com o backend em `http://localhost:8000`
(CORS já configurado).

Os projetos (vídeo, transcrição, renders, previews) ficam em `backend/data/projects/<id>/`.

## Testes

Cobrem toda a lógica pura (geração de títulos, construção de `.ass`, crítico, parser de
comandos, ducking de música, escaping de filtros ffmpeg) — não precisam de ffmpeg, Whisper
nem Node instalados:

```bash
pip install -r requirements-dev.txt
pytest
```

Para o frontend, `cd frontend && npx tsc -b && npx vite build` valida tipos e build.

## Limitações conhecidas (honestamente)

- A timeline é informativa e clicável (clica numa legenda para saltar o vídeo para lá),
  mas não tem arrastar/redimensionar blocos — o corte é feito pelos campos numéricos de
  início/fim.
- O upload e a renderização são pedidos síncronos: para vídeos longos ou modelos Whisper
  maiores, o pedido demora — não há barra de progresso, só o estado "a processar".
- A deteção de batidas de música (`backend/app/music.py`, via `librosa`) está implementada
  mas não está ligada à interface — por agora o ducking usa apenas as janelas de fala.

## O motor de variações como CLI standalone

O pacote `video_variator/` continua a funcionar sozinho, sem o backend/frontend, para
quem só quer gerar variações a partir da linha de comandos:

```bash
python -m video_variator.cli video.mp4 -n 5 -o output --model small
```

Ver `video_variator/cli.py --help` para todas as opções.

## Nota

Usa isto apenas com vídeos sobre os quais tens direitos.
