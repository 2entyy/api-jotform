#!/usr/bin/env python3
"""
Extractor de Empresas CAE 68100 (Compra e Venda de Bens Imobiliarios)
com Capital Social > 250.000 EUR.

Duas formas de alimentar o pipeline:

  1) FICHEIRO (recomendado) - carrega um CSV/Excel exportado de uma fonte
     oficial ou aberta (ex.: dados.gov.pt, Portal da Empresa, IES/INE,
     exportacoes de diretorios de empresas). E o metodo mais fiavel e o
     unico garantido a funcionar sem dependencias de terceiros.

  2) SCRAPING (opcional/plugavel) - um scraper HTTP generico e "educado"
     (rotacao de User-Agent, delays aleatorios, retries com backoff,
     verificacao de robots.txt) que aceita um "adapter" escrito por si
     para o site concreto que quiser usar. Nao vem com seletores de
     nenhum site especifico: tem de fornecer o seu proprio adapter
     (ver adapters/example_adapter.py) e e responsavel por confirmar que
     o scraping desse site cumpre os respetivos Termos de Servico e o
     robots.txt.

Uso tipico:

    python3 extractor_cae68100.py --generate-template
    # edite empresas_input_exemplo.csv com os seus dados
    python3 extractor_cae68100.py --input empresas_input_exemplo.csv

    # com scraping (precisa de um adapter proprio):
    python3 extractor_cae68100.py --scrape-url "https://exemplo.pt/pesquisa?cae=68100" \\
        --site-adapter adapters/example_adapter.py --max-pages 5

Nota de conformidade (RGPD / cold calling B2B em Portugal):
  - Antes de usar estes contactos numa campanha de cold calling, verifique
    a Lista Nao Incomode (ANACOM) e assegure-se de que tem base legal
    (interesse legitimo) e mecanismo de opt-out para contactos de pessoas
    coletivas. Este script nao faz essa verificacao automaticamente.
"""

from __future__ import annotations

import argparse
import logging
import random
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib import robotparser
from urllib.parse import urlparse

import pandas as pd

# --------------------------------------------------------------------------
# Configuracao
# --------------------------------------------------------------------------

TARGET_CAE = "68100"
MIN_CAPITAL_SOCIAL = 250_000.0

PRIORITY_DISTRICTS = [
    "porto",
    "matosinhos",
    "maia",
    "vila nova de gaia",
    "lisboa",
]

OUTPUT_FILENAME = "empresas_alvo_68100_250k.csv"
LOG_FILENAME = "erros_processamento.log"

# Colunas finais do CSV de saida
OUTPUT_COLUMNS = [
    "Nome da Empresa",
    "Capital Social (EUR)",
    "Morada Completa",
    "Concelho",
    "Distrito",
    "Telefone",
    "NIF",
    "Prioritario",
]

# Alias de cabecalhos aceites nos ficheiros de entrada (normalizados: sem
# acentos, minusculas, sem pontuacao). Cobre exportacoes tipicas de
# INE / IES / Portal da Empresa / diretorios de empresas.
COLUMN_ALIASES: dict[str, list[str]] = {
    "nome": ["nome", "empresa", "firma", "designacao", "designacao social",
              "nome empresa", "razao social", "denominacao", "company", "name"],
    "capital_social": ["capital social", "capital_social", "capital",
                        "capitalsocial", "capital socialeur", "share capital"],
    "morada": ["morada", "morada completa", "endereco", "endereco completo",
               "address", "morada sede"],
    "concelho": ["concelho", "municipio", "cidade", "city", "town"],
    "distrito": ["distrito", "district"],
    "telefone": ["telefone", "contacto", "contacto telefonico", "contato",
                 "phone", "telemovel", "numero telefone", "tel"],
    "nif": ["nif", "nipc", "vat", "tax id", "contribuinte", "numero contribuinte"],
    "cae": ["cae", "cae principal", "codigo cae", "cae_principal", "cae1"],
}

logger = logging.getLogger("extractor_cae68100")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    file_handler = logging.FileHandler(LOG_FILENAME, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )

    logger.addHandler(console)
    logger.addHandler(file_handler)


# --------------------------------------------------------------------------
# Utilitarios de limpeza / normalizacao
# --------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_header(header: str) -> str:
    header = strip_accents(str(header)).lower().strip()
    header = re.sub(r"[^a-z0-9]+", " ", header)
    return re.sub(r"\s+", " ", header).strip()


def build_column_map(columns: list[str]) -> dict[str, str]:
    """Devolve {nome_canonico: nome_original_da_coluna} para as colunas
    encontradas no ficheiro, usando correspondencia difusa de cabecalhos."""
    normalized_to_original = {normalize_header(c): c for c in columns}
    result: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_to_original:
                result[canonical] = normalized_to_original[alias]
                break
    return result


def clean_capital_social(raw) -> Optional[float]:
    """Extrai um valor numerico de capital social a partir de texto livre,
    lidando com simbolos de moeda e formatos PT (1.234.567,89) e EN
    (1,234,567.89)."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        if pd.isna(raw):
            return None
        return float(raw)

    text = str(raw).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "-"}:
        return None

    text = strip_accents(text).lower()
    text = re.sub(r"(eur|euros?|€)", "", text)
    text = text.strip()
    text = re.sub(r"[^0-9.,\-]", "", text)
    if not text:
        return None

    has_dot = "." in text
    has_comma = "," in text

    try:
        if has_dot and has_comma:
            if text.rfind(",") > text.rfind("."):
                # "." = milhares, "," = decimal (formato PT)
                text = text.replace(".", "").replace(",", ".")
            else:
                # "," = milhares, "." = decimal (formato EN)
                text = text.replace(",", "")
        elif has_comma and not has_dot:
            # so virgula: assume separador decimal
            text = text.replace(",", ".")
        elif has_dot and not has_comma:
            # so ponto(s): se houver mais que um, sao milhares
            if text.count(".") > 1:
                text = text.replace(".", "")
            else:
                integer_part, _, decimal_part = text.partition(".")
                # "250.000" -> tipicamente milhares em PT; "250.5" -> decimal
                if len(decimal_part) == 3 and len(integer_part) <= 3:
                    text = integer_part + decimal_part
        return float(text)
    except (ValueError, ZeroDivisionError):
        return None


def clean_cae(raw) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    digits = re.sub(r"\D", "", str(raw))
    return digits or None


def clean_nif(raw) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    digits = re.sub(r"\D", "", str(raw))
    return digits or None


def clean_phone(raw) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "-"}:
        return None
    # mantem "+" inicial se existir, remove tudo o resto que nao seja digito
    prefix = "+" if text.startswith("+") else ""
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return prefix + digits


def clean_text_field(raw) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip()
    return text or None


def is_priority_district(concelho: Optional[str], distrito: Optional[str]) -> bool:
    haystack = strip_accents(f"{concelho or ''} {distrito or ''}").lower()
    return any(district in haystack for district in PRIORITY_DISTRICTS)


# --------------------------------------------------------------------------
# Carregamento a partir de ficheiro (CSV / Excel)
# --------------------------------------------------------------------------

def load_from_file(path: Path) -> pd.DataFrame:
    logger.info("A carregar dados de %s ...", path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        # tenta detetar separador automaticamente (',' ou ';')
        raw_df = pd.read_csv(path, sep=None, engine="python", dtype=str,
                              keep_default_na=False, na_values=[""])
    elif suffix in (".xlsx", ".xls"):
        raw_df = pd.read_excel(path, dtype=str)
    else:
        raise ValueError(f"Formato de ficheiro nao suportado: {suffix}")

    column_map = build_column_map(list(raw_df.columns))
    missing = [c for c in ("nome", "capital_social") if c not in column_map]
    if missing:
        raise ValueError(
            "Nao foi possivel identificar as colunas obrigatorias "
            f"{missing} no ficheiro de entrada. Colunas encontradas: "
            f"{list(raw_df.columns)}. Use --generate-template para ver o "
            "formato esperado."
        )

    records: list[dict] = []
    for idx, row in raw_df.iterrows():
        try:
            record = {
                canonical: row.get(original)
                for canonical, original in column_map.items()
            }
            records.append(record)
        except Exception as exc:  # nunca deixar um registo corrompido parar tudo
            logger.warning("Linha %s ignorada (erro ao ler): %s", idx + 2, exc)
            continue

    logger.info("Carregados %d registos de %s.", len(records), path.name)
    return pd.DataFrame(records)


def generate_template(path: Path) -> None:
    sample = pd.DataFrame([
        {
            "Nome": "Imobiliaria Exemplo, Lda",
            "CAE": "68100",
            "Capital Social": "300.000,00 EUR",
            "Morada Completa": "Rua Exemplo, 123",
            "Concelho": "Porto",
            "Distrito": "Porto",
            "Telefone": "+351 220 000 000",
            "NIF": "500000000",
        },
        {
            "Nome": "Predial Exemplo 2, S.A.",
            "CAE": "68100",
            "Capital Social": "1.250.000,00 EUR",
            "Morada Completa": "Av. Exemplo, 456",
            "Concelho": "Lisboa",
            "Distrito": "Lisboa",
            "Telefone": "213456789",
            "NIF": "500000001",
        },
    ])
    sample.to_csv(path, index=False, sep=";", encoding="utf-8-sig")
    logger.info("Template gerado em %s", path)


# --------------------------------------------------------------------------
# Scraping generico e "educado" (opcional, requer adapter proprio)
# --------------------------------------------------------------------------

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 "
    "Firefox/125.0",
]


@dataclass
class ScraperConfig:
    user_agents: list[str] = field(default_factory=lambda: list(DEFAULT_USER_AGENTS))
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 6.0
    max_retries: int = 3
    backoff_base_seconds: float = 3.0
    timeout_seconds: float = 15.0
    proxies: Optional[list[str]] = None  # ex.: ["http://user:pass@host:port"]
    respect_robots_txt: bool = True


class PoliteScraper:
    """Cliente HTTP generico com rotacao de User-Agent, delays aleatorios
    entre pedidos, retries com backoff exponencial e verificacao opcional
    de robots.txt. Nao contem logica para nenhum site em particular -
    combine-o com um "adapter" (ver adapters/example_adapter.py) que sabe
    interpretar o HTML do site escolhido.

    Antes de usar, confirme que tem permissao/legitimidade para recolher
    dados do site alvo (Termos de Servico, robots.txt, RGPD)."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        import requests

        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self._robots_cache: dict[str, robotparser.RobotFileParser] = {}

    def _robots_allowed(self, url: str) -> bool:
        if not self.config.respect_robots_txt:
            return True
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_cache.get(origin)
        if rp is None:
            rp = robotparser.RobotFileParser()
            rp.set_url(origin + "/robots.txt")
            try:
                rp.read()
            except Exception as exc:
                logger.debug("Nao foi possivel ler robots.txt de %s: %s", origin, exc)
                # se nao conseguirmos ler o robots.txt, assumimos permissivo
                # mas continuamos a aplicar delays/backoff normalmente
                self._robots_cache[origin] = rp
                return True
            self._robots_cache[origin] = rp
        user_agent = random.choice(self.config.user_agents)
        return rp.can_fetch(user_agent, url)

    def get(self, url: str, params: Optional[dict] = None):
        import requests

        if not self._robots_allowed(url):
            logger.warning("robots.txt nao permite aceder a %s - a saltar.", url)
            return None

        headers = {"User-Agent": random.choice(self.config.user_agents)}
        proxies = None
        if self.config.proxies:
            proxy = random.choice(self.config.proxies)
            proxies = {"http": proxy, "https": proxy}

        last_exc = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=self.config.timeout_seconds,
                )
                if response.status_code == 200:
                    self._sleep_politely()
                    return response
                if response.status_code in (429, 503):
                    wait = self.config.backoff_base_seconds * (2 ** (attempt - 1))
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    logger.warning(
                        "HTTP %s em %s (tentativa %d/%d) - a aguardar %.1fs",
                        response.status_code, url, attempt,
                        self.config.max_retries, wait,
                    )
                    time.sleep(wait)
                    continue
                logger.warning("HTTP %s em %s - a saltar.", response.status_code, url)
                return None
            except requests.RequestException as exc:
                last_exc = exc
                wait = self.config.backoff_base_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Erro de rede em %s (tentativa %d/%d): %s - a aguardar %.1fs",
                    url, attempt, self.config.max_retries, exc, wait,
                )
                time.sleep(wait)

        logger.error("Falha definitiva ao aceder a %s: %s", url, last_exc)
        return None

    def _sleep_politely(self) -> None:
        delay = random.uniform(self.config.min_delay_seconds, self.config.max_delay_seconds)
        time.sleep(delay)


def load_site_adapter(adapter_path: Path):
    """Carrega dinamicamente um modulo Python de adapter fornecido pelo
    utilizador. O modulo deve expor:
        SEARCH_URL_TEMPLATE (opcional, str) e/ou usar o url fornecido em --scrape-url
        extract_records(soup) -> list[dict]   (obrigatorio)
        has_next_page(soup) -> bool           (opcional)
        next_page_url(soup, current_url, page_number) -> str | None (opcional)
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("site_adapter", adapter_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Nao foi possivel carregar o adapter em {adapter_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "extract_records"):
        raise AttributeError(
            f"O adapter {adapter_path} tem de definir extract_records(soup)."
        )
    return module


def scrape_with_adapter(
    start_url: str,
    adapter_path: Path,
    max_pages: int = 1,
    scraper_config: Optional[ScraperConfig] = None,
) -> pd.DataFrame:
    from bs4 import BeautifulSoup

    adapter = load_site_adapter(adapter_path)
    scraper = PoliteScraper(scraper_config)

    all_records: list[dict] = []
    url = start_url
    page = 1
    while url and page <= max_pages:
        logger.info("A pesquisar pagina %d: %s", page, url)
        response = scraper.get(url)
        if response is None:
            logger.warning("Sem resposta para %s - a parar paginacao.", url)
            break
        try:
            soup = BeautifulSoup(response.text, "lxml")
            page_records = adapter.extract_records(soup)
            logger.info("Pagina %d: %d registos extraidos.", page, len(page_records))
            all_records.extend(page_records)
        except Exception as exc:
            logger.warning("Erro ao interpretar a pagina %d (%s): %s", page, url, exc)

        next_url = None
        if hasattr(adapter, "next_page_url"):
            try:
                next_url = adapter.next_page_url(soup, url, page)
            except Exception as exc:
                logger.debug("Erro ao calcular proxima pagina: %s", exc)
        url = next_url
        page += 1

    return pd.DataFrame(all_records)


# --------------------------------------------------------------------------
# Processamento / filtragem
# --------------------------------------------------------------------------

def process_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        logger.warning("Nenhum registo para processar.")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows_out: list[dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        try:
            nome = clean_text_field(row.get("nome"))
            if not nome:
                skipped += 1
                logger.debug("Registo %s ignorado: sem nome.", idx)
                continue

            cae = clean_cae(row.get("cae"))
            if cae is not None and cae != TARGET_CAE:
                continue  # nao e o CAE alvo, ignora silenciosamente

            capital = clean_capital_social(row.get("capital_social"))
            if capital is None or capital <= MIN_CAPITAL_SOCIAL:
                continue  # abaixo do limiar ou nao numerico

            morada = clean_text_field(row.get("morada"))
            concelho = clean_text_field(row.get("concelho"))
            distrito = clean_text_field(row.get("distrito"))
            telefone = clean_phone(row.get("telefone"))
            nif = clean_nif(row.get("nif"))

            prioritario = is_priority_district(concelho, distrito)

            rows_out.append({
                "Nome da Empresa": nome,
                "Capital Social (EUR)": round(capital, 2),
                "Morada Completa": morada or "",
                "Concelho": concelho or "",
                "Distrito": distrito or "",
                "Telefone": telefone or "",
                "NIF": nif or "",
                "Prioritario": "Sim" if prioritario else "Nao",
            })
        except Exception as exc:
            skipped += 1
            logger.warning("Registo %s corrompido, a saltar: %s", idx, exc)
            continue

    logger.info("Registos validos apos filtragem: %d (ignorados: %d)",
                len(rows_out), skipped)

    result = pd.DataFrame(rows_out, columns=OUTPUT_COLUMNS)
    if result.empty:
        return result

    # remove duplicados por NIF (mantem o de maior capital social)
    before = len(result)
    result = (
        result.sort_values("Capital Social (EUR)", ascending=False)
        .drop_duplicates(subset=["NIF"], keep="first")
    )
    if before != len(result):
        logger.info("Removidos %d duplicados por NIF.", before - len(result))

    # ordena: prioritarios primeiro, depois por capital social descendente
    result["_prioridade_sort"] = (result["Prioritario"] == "Sim").astype(int)
    result = result.sort_values(
        by=["_prioridade_sort", "Capital Social (EUR)"],
        ascending=[False, False],
    ).drop(columns="_prioridade_sort")

    return result.reset_index(drop=True)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extractor de empresas CAE 68100 com capital social > 250k EUR.",
    )
    parser.add_argument("--input", type=Path, help="Ficheiro CSV/Excel de entrada.")
    parser.add_argument("--scrape-url", type=str, help="URL inicial para scraping (requer --site-adapter).")
    parser.add_argument("--site-adapter", type=Path, help="Ficheiro Python com o adapter do site a fazer scraping.")
    parser.add_argument("--max-pages", type=int, default=1, help="Numero maximo de paginas a percorrer no scraping.")
    parser.add_argument("--output", type=Path, default=Path(OUTPUT_FILENAME), help="Ficheiro CSV de saida.")
    parser.add_argument("--priority-only", action="store_true",
                         help="Mantem apenas empresas em distritos prioritarios (Porto, Matosinhos, Maia, Vila Nova de Gaia, Lisboa).")
    parser.add_argument("--generate-template", action="store_true",
                         help="Gera um ficheiro de exemplo empresas_input_exemplo.csv e termina.")
    parser.add_argument("--min-delay", type=float, default=2.0, help="Delay minimo (s) entre pedidos de scraping.")
    parser.add_argument("--max-delay", type=float, default=6.0, help="Delay maximo (s) entre pedidos de scraping.")
    parser.add_argument("--proxy", action="append", help="Proxy a usar no scraping (pode ser repetido). Ex.: http://user:pass@host:port")
    parser.add_argument("--ignore-robots", action="store_true",
                         help="Ignora robots.txt no scraping (use apenas se tiver permissao explicita do site alvo).")
    parser.add_argument("--verbose", action="store_true", help="Logging detalhado.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    setup_logging(args.verbose)

    if args.generate_template:
        generate_template(Path("empresas_input_exemplo.csv"))
        return 0

    frames: list[pd.DataFrame] = []

    if args.input:
        if not args.input.exists():
            logger.error("Ficheiro de entrada nao encontrado: %s", args.input)
            return 1
        try:
            frames.append(load_from_file(args.input))
        except Exception as exc:
            logger.error("Falha ao carregar %s: %s", args.input, exc)
            return 1

    if args.scrape_url:
        if not args.site_adapter:
            logger.error("--scrape-url requer --site-adapter (ver adapters/example_adapter.py).")
            return 1
        if not args.site_adapter.exists():
            logger.error("Adapter nao encontrado: %s", args.site_adapter)
            return 1
        try:
            scraper_config = ScraperConfig(
                min_delay_seconds=args.min_delay,
                max_delay_seconds=args.max_delay,
                proxies=args.proxy,
                respect_robots_txt=not args.ignore_robots,
            )
            frames.append(
                scrape_with_adapter(
                    args.scrape_url, args.site_adapter, args.max_pages, scraper_config
                )
            )
        except Exception as exc:
            logger.error("Falha no scraping: %s", exc)

    if not frames:
        logger.error(
            "Nenhuma fonte de dados fornecida. Use --input FICHEIRO ou "
            "--scrape-url + --site-adapter. Use --generate-template para "
            "ver o formato de ficheiro esperado."
        )
        return 1

    combined = pd.concat(frames, ignore_index=True, sort=False)
    logger.info("Total de registos combinados: %d", len(combined))

    result = process_records(combined)

    if args.priority_only:
        before = len(result)
        result = result[result["Prioritario"] == "Sim"].reset_index(drop=True)
        logger.info("Filtro de distritos prioritarios: %d -> %d registos.",
                    before, len(result))

    result.to_csv(args.output, index=False, sep=";", encoding="utf-8-sig")
    logger.info("Ficheiro final gravado em %s (%d empresas).", args.output, len(result))

    if not result.empty:
        n_priority = int((result["Prioritario"] == "Sim").sum())
        logger.info("Resumo: %d empresas alvo | %d em distritos prioritarios | "
                    "capital social medio: %.2f EUR",
                    len(result), n_priority, result["Capital Social (EUR)"].mean())

    return 0


if __name__ == "__main__":
    sys.exit(main())
