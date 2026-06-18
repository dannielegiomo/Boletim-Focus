"""Testes para src/baixar_focus.py."""

import datetime
import sys
from pathlib import Path

import pytest

# Insere src/ no path para importar sem instalar o pacote
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from baixar_focus import baixar, ultima_segunda  # noqa: E402

# ---------------------------------------------------------------------------
# Testes puros (sem rede) – ultima_segunda
# ---------------------------------------------------------------------------

def test_ultima_segunda_quinta():
    # Quinta 12/06/2025 → segunda anterior é 09/06/2025
    assert ultima_segunda(datetime.date(2025, 6, 12)) == datetime.date(2025, 6, 9)


def test_ultima_segunda_terca():
    # Terça 10/06/2025 → segunda anterior é 09/06/2025
    assert ultima_segunda(datetime.date(2025, 6, 10)) == datetime.date(2025, 6, 9)


def test_ultima_segunda_segunda_recua_semana():
    # Segunda 09/06/2025 → deve recuar para segunda da semana passada: 02/06/2025
    assert ultima_segunda(datetime.date(2025, 6, 9)) == datetime.date(2025, 6, 2)


def test_ultima_segunda_domingo():
    # Domingo 15/06/2025 → segunda anterior é 09/06/2025
    assert ultima_segunda(datetime.date(2025, 6, 15)) == datetime.date(2025, 6, 9)


def test_ultima_segunda_varredura_60_dias():
    """Para qualquer dia nos próximos 60 dias, o retorno é sempre uma segunda
    ESTRITAMENTE anterior à data dada (nunca igual, nunca no futuro)."""
    hoje = datetime.date.today()
    for delta in range(60):
        data = hoje + datetime.timedelta(days=delta)
        resultado = ultima_segunda(data)
        # deve ser segunda-feira (weekday == 0)
        assert resultado.weekday() == 0, f"{data}: retornou {resultado} (não é segunda)"
        # deve ser estritamente anterior à data fornecida
        assert resultado < data, f"{data}: retornou {resultado} (não é anterior)"


# ---------------------------------------------------------------------------
# Teste de rede – baixar()
# ---------------------------------------------------------------------------

@pytest.mark.network
def test_baixar_download_real(tmp_path):
    """Faz o download real do PDF e valida o arquivo recebido."""
    data_pub, pdf_path = baixar(tmp_path)

    # Arquivo deve ter sido criado
    assert pdf_path.exists(), "O arquivo PDF não foi criado."

    # Deve ser um PDF válido (magic bytes)
    assert pdf_path.read_bytes()[:4] == b"%PDF", "O arquivo não começa com %PDF."

    # Deve ter mais de 50 KB (boletim real sempre ultrapassa isso)
    tamanho_kb = pdf_path.stat().st_size / 1024
    assert tamanho_kb > 50, f"PDF muito pequeno: {tamanho_kb:.1f} KB."

    # Nome do arquivo deve bater com a data retornada
    nome_esperado = f"focus_{data_pub.isoformat()}.pdf"
    assert pdf_path.name == nome_esperado, (
        f"Nome inesperado: {pdf_path.name!r} (esperado {nome_esperado!r})."
    )

    # Data deve estar dentro da janela esperada: não no futuro, não há mais de 14 dias
    hoje = datetime.date.today()
    assert data_pub <= hoje, f"Data de publicação {data_pub} está no futuro."
    assert (hoje - data_pub).days <= 14, (
        f"Data de publicação {data_pub} está há mais de 14 dias."
    )
