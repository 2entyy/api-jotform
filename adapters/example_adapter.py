"""
Template de "site adapter" para o extractor_cae68100.py.

Este ficheiro NAO faz scraping de nenhum site concreto - e um ponto de
partida que tem de adaptar ao HTML real da fonte que escolher usar
(diretorio aberto de empresas, portal de dados publicos, etc.).

Antes de o usar contra um site real:
  1. Leia os Termos de Servico e o robots.txt desse site.
  2. Confirme que a recolha automatizada destes dados e permitida.
  3. Ajuste os seletores CSS abaixo para a estrutura HTML real da pagina.

O extractor_cae68100.py chama extract_records(soup) para cada pagina
carregada e junta os dicionarios devolvidos ao pipeline de filtragem
(que depois aplica o filtro de CAE 68100 e capital social > 250k).

As chaves aceites em cada dicionario (todas opcionais, mas "nome" e
"capital_social" sao necessarias para o registo ser aproveitado) sao:
    nome, capital_social, morada, concelho, distrito, telefone, nif, cae
"""

from bs4 import BeautifulSoup


def extract_records(soup: BeautifulSoup) -> list[dict]:
    """Recebe o HTML (ja parseado) de uma pagina de resultados e devolve
    uma lista de dicionarios, um por empresa encontrada na pagina.

    Exemplo ilustrativo (ajuste os seletores ao site real):

        records = []
        for card in soup.select("div.company-card"):
            records.append({
                "nome": card.select_one(".company-name").get_text(strip=True),
                "capital_social": card.select_one(".share-capital").get_text(strip=True),
                "morada": card.select_one(".address").get_text(strip=True),
                "concelho": card.select_one(".city").get_text(strip=True),
                "telefone": card.select_one(".phone").get_text(strip=True),
                "nif": card.select_one(".tax-id").get_text(strip=True),
                "cae": "68100",
            })
        return records
    """
    raise NotImplementedError(
        "Personalize adapters/example_adapter.py com os seletores CSS do "
        "site que pretende usar antes de correr o scraping."
    )


def next_page_url(soup: BeautifulSoup, current_url: str, page_number: int) -> str | None:
    """Opcional: devolva o URL da pagina seguinte de resultados, ou None
    para parar a paginacao. Por omissao, o extractor para apos 1 pagina
    se esta funcao nao for personalizada.
    """
    return None
