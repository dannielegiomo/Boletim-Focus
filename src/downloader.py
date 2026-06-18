"""Download do Boletim Focus do Banco Central do Brasil."""

import datetime
from pathlib import Path

import requests

BASE_URL = "https://www.bcb.gov.br/content/focus/focus/R{date}.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RETRIES = 7


def last_monday(reference: datetime.date | None = None) -> datetime.date:
    """Retorna a segunda-feira mais recente a partir de `reference` (padrão: hoje)."""
    ref = reference or datetime.date.today()
    days_since_monday = ref.weekday()  # segunda=0, domingo=6
    return ref - datetime.timedelta(days=days_since_monday)


def find_focus_date(start: datetime.date) -> tuple[datetime.date, str]:
    """
    Tenta baixar o PDF do Focus retroagindo dia a dia a partir de `start`.
    Retorna (data_publicacao, conteúdo_bytes) ou levanta RuntimeError.
    """
    for delta in range(MAX_RETRIES):
        candidate = start - datetime.timedelta(days=delta)
        url = BASE_URL.format(date=candidate.strftime("%Y%m%d"))
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return candidate, response.content
    raise RuntimeError(
        f"PDF do Focus não encontrado nos {MAX_RETRIES} dias anteriores a {start}."
    )


def download_focus(reference: datetime.date | None = None) -> Path:
    """
    Baixa o Boletim Focus mais recente e salva em data/.
    Retorna o caminho do arquivo salvo.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    start = last_monday(reference)
    pub_date, content = find_focus_date(start)

    pdf_path = DATA_DIR / f"focus_{pub_date.isoformat()}.pdf"
    pdf_path.write_bytes(content)
    print(f"PDF salvo: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    download_focus()
