"""Baixa o Boletim Focus mais recente do Banco Central do Brasil."""

import datetime
from pathlib import Path

import urllib3
import requests

# Proxy corporativo faz SSL inspection com certificado próprio; desabilita verificação
# para que o requests não rejeite a cadeia auto-assinada da rede interna.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL do PDF com a data no formato AAAAMMDD (sem hífens)
URL_TEMPLATE = "https://www.bcb.gov.br/content/focus/focus/R{data}.pdf"

# Máximo de dias a retroagir (cobre feriados prolongados)
MAX_TENTATIVAS = 7

# Cabeçalho para evitar bloqueio por User-Agent padrão do requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def ultima_segunda(hoje: datetime.date) -> datetime.date:
    """Retorna a segunda-feira mais recente ESTRITAMENTE anterior a `hoje`.

    Se `hoje` já é segunda, retrocede para a segunda da semana passada.
    """
    # weekday(): segunda=0 … domingo=6
    # Quantos dias retroceder para chegar à segunda anterior:
    # - se hoje é terça (1): 1 dia; se domingo (6): 6 dias; se segunda (0): 7 dias
    dias = hoje.weekday() or 7  # 0 vira 7 para forçar retrocesso numa semana inteira
    return hoje - datetime.timedelta(days=dias)


def baixar(dest: Path) -> tuple[datetime.date, Path]:
    """Baixa o PDF do Focus mais recente e salva na pasta `dest`.

    Parte da última segunda anterior a hoje e recua dia a dia até
    MAX_TENTATIVAS. Valida que o arquivo começa com b'%PDF' antes de aceitar.

    Retorna (data_da_publicacao, caminho_do_arquivo).
    Levanta RuntimeError se nenhuma tentativa funcionar.
    """
    dest.mkdir(parents=True, exist_ok=True)

    inicio = ultima_segunda(datetime.date.today())

    for delta in range(MAX_TENTATIVAS):
        candidata = inicio - datetime.timedelta(days=delta)
        url = URL_TEMPLATE.format(data=candidata.strftime("%Y%m%d"))

        resposta = requests.get(url, headers=HEADERS, timeout=30, verify=False)

        # Verifica se o servidor retornou OK e se o conteúdo é um PDF válido
        if resposta.status_code == 200 and resposta.content[:4] == b"%PDF":
            caminho = dest / f"focus_{candidata.isoformat()}.pdf"
            caminho.write_bytes(resposta.content)
            return candidata, caminho

    raise RuntimeError(
        f"PDF do Focus não encontrado nos {MAX_TENTATIVAS} dias anteriores a {inicio}."
    )


def main() -> None:
    """Baixa o Focus para data/ e exibe o caminho e o tamanho em KB."""
    pasta_destino = Path(__file__).resolve().parent.parent / "data"

    data_pub, caminho = baixar(pasta_destino)
    tamanho_kb = caminho.stat().st_size / 1024

    print(f"Publicado em : {data_pub.isoformat()}")
    print(f"Arquivo      : {caminho}")
    print(f"Tamanho      : {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
