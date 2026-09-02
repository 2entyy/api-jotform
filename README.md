# video-variator

App local (sem serviços na cloud, sem chaves de API) que pega num vídeo base e gera
várias variações subtilmente diferentes, para testar em Reels: cada uma tem uma
legenda/título diferente sugerido a partir do que é dito no vídeo, e uma combinação
aleatória de pequenas alterações de velocidade, cor e micro-zoom.

Usa apenas ferramentas que correm na tua máquina:

- **Whisper local** (`openai-whisper`) para transcrever o áudio, sem chamadas a APIs externas.
- **ffmpeg** para renderizar cada variação (texto, velocidade, cor, crop).

## Como funciona

Para cada vídeo, o pipeline:

1. Transcreve o áudio localmente com Whisper.
2. A partir das palavras mais frequentes na transcrição, gera um título/legenda
   chamativo diferente por variação (ex: `A VERDADE SOBRE VIAGENS`), usando modelos
   de frase prontos — sem chamar nenhuma IA externa.
3. Para cada variação escolhe, dentro de intervalos pequenos e configuráveis:
   - velocidade (±6%)
   - brilho/contraste/saturação/matiz (ajustes mínimos)
   - um micro-zoom/crop (até 3%)
   - opcionalmente espelhar o vídeo (desativado por omissão)
4. Desenha o título numa caixa de legenda no topo do vídeo com `drawtext` do ffmpeg.
5. Escreve um `*_manifest.json` na pasta de saída com os parâmetros exatos usados em
   cada variação, para poderes cruzar com o desempenho de cada Reel depois.

## Pré-requisitos

- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) instalado e no `PATH` (`ffmpeg -version` deve funcionar)
- Uma fonte `.ttf` (o script já procura DejaVu Sans Bold / Liberation Sans Bold,
  comuns na maioria das distros Linux)

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A primeira transcrição descarrega o modelo Whisper escolhido (fica em cache local
em `~/.cache/whisper`); depois disso corre totalmente offline.

## Uso

```bash
python -m video_variator.cli video.mp4 -n 5 -o output --model small
```

Opções principais:

| Flag | Descrição |
|---|---|
| `-n, --num-variations` | quantas variações gerar (default 5) |
| `-o, --output-dir` | pasta de saída (default `output`) |
| `--model` | tamanho do modelo Whisper: `tiny`, `base`, `small`, `medium`, `large` |
| `--seed` | fixa a aleatoriedade, para resultados reprodutíveis |
| `--font` | caminho para uma fonte `.ttf` própria |
| `--allow-mirror` | permite espelhar o vídeo como uma das variações possíveis |
| `--no-crop` | desativa o micro-zoom/crop |
| `--dry-run` | só transcreve e escreve o manifest, sem renderizar vídeo (útil para pré-visualizar os títulos sugeridos rapidamente) |

Cada variação sai como `<nome-original>_var1.mp4`, `_var2.mp4`, etc., mais um
`<nome-original>_manifest.json` com a transcrição e os parâmetros usados em cada uma.

## Testes

Os testes cobrem a geração de títulos e a construção dos filtros ffmpeg (não
precisam de ffmpeg nem de Whisper instalados):

```bash
pip install -r requirements-dev.txt
pytest
```

## Nota

Usa isto apenas com vídeos sobre os quais tens direitos — o objetivo é testar
diferentes ganchos/títulos e edições do teu próprio conteúdo, não republicar
conteúdo de terceiros.
