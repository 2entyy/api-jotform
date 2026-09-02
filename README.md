# Extractor de Empresas CAE 68100 (> 250k Capital Social)

Script Python para extrair, filtrar e limpar dados de empresas portuguesas
com **CAE 68100** (Compra e Venda de Bens Imobiliários) e **capital social
superior a 250.000€**, gerando um ficheiro final pronto para uma campanha
de cold calling.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modo 1 — Ficheiro (recomendado)

O método mais fiável: carregue um CSV/Excel exportado de uma fonte oficial
ou aberta (ex.: dados.gov.pt, Portal da Empresa, IES/INE, exportações de
diretórios de empresas). O script reconhece automaticamente colunas comuns
(`Nome`/`Firma`/`Razão Social`, `Capital Social`, `Morada`, `Concelho`,
`Distrito`, `Telefone`/`Contacto`, `NIF`/`NIPC`, `CAE`), independentemente
de acentuação ou maiúsculas/minúsculas.

```bash
# gera um ficheiro de exemplo com o formato esperado
python3 extractor_cae68100.py --generate-template

# processa o seu ficheiro real
python3 extractor_cae68100.py --input o_seu_ficheiro.csv
python3 extractor_cae68100.py --input o_seu_ficheiro.xlsx --priority-only
```

## Modo 2 — Scraping (opcional, requer adapter próprio)

O script inclui um cliente HTTP genérico e "educado"
(`PoliteScraper` em `extractor_cae68100.py`) com:

- rotação de User-Agent entre browsers comuns;
- delays aleatórios entre pedidos (`--min-delay` / `--max-delay`);
- retries com backoff exponencial em erros de rede, `429` e `503`
  (respeitando `Retry-After` quando presente);
- verificação de `robots.txt` antes de cada pedido (pode desligar com
  `--ignore-robots`, apenas se tiver permissão explícita do site alvo);
- suporte opcional a proxies próprios (`--proxy`, repetível).

**Não vem com seletores para nenhum site concreto.** Tem de escrever um
"adapter" (ver `adapters/example_adapter.py`) que sabe interpretar o HTML
da fonte que escolher, e é responsável por confirmar que essa recolha
cumpre os Termos de Serviço e o `robots.txt` do site.

```bash
python3 extractor_cae68100.py \
    --scrape-url "https://exemplo.pt/pesquisa?cae=68100" \
    --site-adapter adapters/example_adapter.py \
    --max-pages 5
```

Pode combinar as duas fontes numa única execução (`--input` +
`--scrape-url`); os registos são juntos antes da filtragem.

## Filtros aplicados

- **CAE:** `68100` (registos sem CAE indicado não são excluídos por esta
  regra — só os que têm um CAE diferente são descartados).
- **Capital Social:** apenas `> 250.000€` (valores com símbolos de moeda,
  pontos de milhares e vírgulas decimais são normalizados automaticamente).
- **Duplicados:** remove NIFs repetidos, mantendo o registo com maior
  capital social.
- **Geografia:** todas as empresas válidas são incluídas, mas as dos
  distritos/concelhos prioritários (Porto, Matosinhos, Maia, Vila Nova de
  Gaia, Lisboa) ficam marcadas em `Prioritario = Sim` e ordenadas primeiro.
  Use `--priority-only` para manter só essas.

## Output

`empresas_alvo_68100_250k.csv` (separador `;`, `utf-8-sig` para abrir bem
no Excel), com as colunas:

```
Nome da Empresa; Capital Social (EUR); Morada Completa; Concelho; Distrito; Telefone; NIF; Prioritario
```

Registos corrompidos ou incompletos são ignorados individualmente (o
script nunca pára a execução por causa de um único registo mau) e ficam
registados em `erros_processamento.log`.

## Nota de conformidade

Antes de usar esta lista numa campanha de cold calling em Portugal:

- Verifique os contactos contra a **Lista Não Incomode** (ANACOM), quando
  aplicável.
- Assegure-se de que tem base legal (RGPD — tipicamente interesse
  legítimo para contactos B2B de pessoas coletivas) e um mecanismo de
  opt-out.
- Se usar o Modo 2 (scraping), confirme que a fonte escolhida permite
  recolha automatizada dos dados para este fim (Termos de Serviço e
  `robots.txt`).

Este script não substitui aconselhamento jurídico.
