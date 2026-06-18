"""Extrai o texto de um PDF do Boletim Focus e salva como .txt."""

import argparse
import sys
from pathlib import Path

import pdfplumber

# Pasta padrão onde os PDFs são salvos pelo baixar_focus.py
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def extrair(pdf_path: Path) -> Path:
    """Extrai o texto de todas as páginas do PDF e salva em arquivo .txt.

    O arquivo de saída recebe o mesmo nome do PDF com extensão trocada para
    .txt e é gravado no mesmo diretório do PDF, em UTF-8.

    Retorna o caminho do arquivo .txt gerado.
    """
    txt_path = pdf_path.with_suffix(".txt")

    with pdfplumber.open(pdf_path) as pdf:
        # Extrai o texto de cada página; substitui None por string vazia
        # para evitar erro ao juntar páginas sem texto selecionável
        paginas = [pagina.extract_text() or "" for pagina in pdf.pages]

    # Separa as páginas com uma linha em branco para facilitar a leitura
    texto_completo = "\n\n".join(paginas)

    txt_path.write_text(texto_completo, encoding="utf-8")
    return txt_path


def _pdf_mais_recente() -> Path | None:
    """Retorna o focus_*.pdf mais recente em DATA_DIR, ou None se não houver."""
    candidatos = sorted(DATA_DIR.glob("focus_*.pdf"))
    return candidatos[-1] if candidatos else None


def main() -> None:
    """Ponto de entrada via linha de comando.

    Uso:
        python src/extrair_texto.py                    # usa o PDF mais recente de data/
        python src/extrair_texto.py --pdf caminho.pdf  # usa o PDF especificado
    """
    parser = argparse.ArgumentParser(
        description="Extrai o texto de um PDF do Boletim Focus."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Caminho para o PDF a ser extraído (padrão: mais recente em data/).",
    )
    args = parser.parse_args()

    if args.pdf:
        pdf_path = args.pdf
    else:
        # Busca automaticamente o PDF mais recente na pasta data/
        pdf_path = _pdf_mais_recente()
        if pdf_path is None:
            print(
                "Nenhum PDF encontrado em data/. "
                "Execute primeiro: python src/baixar_focus.py"
            )
            sys.exit(1)

    txt_path = extrair(pdf_path)
    tamanho_kb = txt_path.stat().st_size / 1024

    print(f"PDF de origem : {pdf_path}")
    print(f"Texto salvo   : {txt_path}")
    print(f"Tamanho       : {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
