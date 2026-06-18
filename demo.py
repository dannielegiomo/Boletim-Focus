"""Pipeline local: baixa o Focus do BCB e extrai o texto em sequência."""

import argparse
import sys
import webbrowser
from pathlib import Path

# Adiciona src/ ao path para que os módulos sejam importados sem instalação
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from baixar_focus import baixar  # noqa: E402
from extrair_texto import extrair  # noqa: E402

# Pasta onde os PDFs e textos ficam armazenados
DATA_DIR = Path(__file__).resolve().parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa o Boletim Focus e extrai o texto."
    )
    parser.add_argument(
        "--abrir",
        action="store_true",
        help="Abre o arquivo .txt gerado no navegador padrão ao final.",
    )
    args = parser.parse_args()

    # Passo 1: download do PDF mais recente
    data_pub, pdf_path = baixar(DATA_DIR)
    tamanho_kb = pdf_path.stat().st_size / 1024
    print(f"[1/2] PDF baixado: {pdf_path.name} ({tamanho_kb:.1f} KB)")

    # Passo 2: extração do texto
    txt_path = extrair(pdf_path)
    print(f"[2/2] Texto extraído: {txt_path}")

    # Abre o .txt no navegador se a flag --abrir foi passada
    if args.abrir:
        webbrowser.open(txt_path.as_uri())


if __name__ == "__main__":
    main()
