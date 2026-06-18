"""Envia o resumo HTML do Boletim Focus por e-mail via SMTP do Gmail.

As credenciais NUNCA ficam no código: são lidas de variáveis de ambiente.
    FOCUS_SMTP_USER          -> e-mail remetente (login do Gmail)
    FOCUS_SMTP_APP_PASSWORD  -> senha de app do Gmail (não a senha normal)
    FOCUS_EMAIL_DEST         -> destinatários, separados por vírgula
    FOCUS_EMAIL_BCC          -> cópia oculta, separada por vírgula (opcional)
"""

import argparse
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from html import unescape
from pathlib import Path

# Pasta padrão onde os resumos em HTML são gerados
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "focus"

# Servidor SMTP do Gmail com SSL implícito (porta 465)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# Nomes das variáveis de ambiente esperadas (NUNCA colocar credenciais no código)
ENV_USER = "FOCUS_SMTP_USER"
ENV_PASSWORD = "FOCUS_SMTP_APP_PASSWORD"
ENV_DEST = "FOCUS_EMAIL_DEST"
ENV_BCC = "FOCUS_EMAIL_BCC"


def html_mais_recente() -> Path | None:
    """Retorna o focus_*.html mais recente em OUTPUT_DIR, ou None se não houver.

    A ordenação alfabética coincide com a cronológica porque o nome segue o
    padrão focus_AAAA-MM-DD.html.
    """
    candidatos = sorted(OUTPUT_DIR.glob("focus_*.html"))
    return candidatos[-1] if candidatos else None


def _data_do_nome(html_path: Path) -> str | None:
    """Extrai a data AAAA-MM-DD do nome do arquivo (ex.: focus_2026-06-05.html)."""
    achado = re.search(r"\d{4}-\d{2}-\d{2}", html_path.stem)
    return achado.group(0) if achado else None


def assunto_padrao(html_path: Path) -> str:
    """Monta o assunto padrão 'Resumo Focus — AAAA-MM-DD' a partir do nome."""
    data = _data_do_nome(html_path)
    return f"Resumo Focus — {data}" if data else "Resumo Focus"


def _split_emails(valor: str | None) -> list[str]:
    """Divide uma string de e-mails separados por vírgula em uma lista limpa."""
    if not valor:
        return []
    return [item.strip() for item in valor.split(",") if item.strip()]


def _html_para_texto(html: str) -> str:
    """Gera um fallback em texto puro a partir do HTML.

    Não é um conversor completo: serve apenas para clientes de e-mail que não
    renderizam HTML. Remove <style>/<script>, transforma tags de bloco em
    quebras de linha, tira as demais tags e converte entidades HTML.
    """
    # Remove blocos de estilo e script por completo (conteúdo incluído)
    texto = re.sub(r"(?is)<(style|script).*?</\1>", "", html)
    # Tags que devem virar quebra de linha para preservar a leitura
    texto = re.sub(r"(?i)<br\s*/?>", "\n", texto)
    texto = re.sub(r"(?i)</(p|div|tr|h[1-6]|li|table)>", "\n", texto)
    # Remove todas as demais tags
    texto = re.sub(r"(?s)<[^>]+>", "", texto)
    # Converte entidades (&amp;, &ccedil; etc.) em caracteres
    texto = unescape(texto)
    # Colapsa sequências de 3+ quebras de linha em no máximo uma linha em branco
    texto = re.sub(r"\n\s*\n\s*\n+", "\n\n", texto)
    return texto.strip()


def montar_email(
    html_path: Path,
    remetente: str,
    destinatarios: list[str],
    assunto: str,
    bcc: list[str] | None = None,
) -> EmailMessage:
    """Monta o EmailMessage com corpo HTML e fallback em texto puro.

    O texto puro entra como conteúdo principal e o HTML como alternativa
    preferencial (multipart/alternative), padrão para máxima compatibilidade.
    """
    corpo_html = html_path.read_text(encoding="utf-8")
    corpo_texto = _html_para_texto(corpo_html)

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = ", ".join(destinatarios)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    msg.set_content(corpo_texto)  # versão texto (fallback)
    msg.add_alternative(corpo_html, subtype="html")  # versão HTML (preferida)
    return msg


def enviar(msg: EmailMessage, usuario: str, senha: str) -> None:
    """Envia a mensagem via smtp.gmail.com:465 usando SSL e senha de app."""
    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=contexto) as servidor:
        servidor.login(usuario, senha)
        servidor.send_message(msg)


def main() -> None:
    """Ponto de entrada via linha de comando.

    Uso:
        # Envio real (exige as variáveis de ambiente configuradas)
        python src/enviar_email.py

        # Apenas montar e inspecionar, sem enviar nem exigir credenciais
        python src/enviar_email.py --dry-run

        # Sobrescrevendo arquivo, destinatários e assunto
        python src/enviar_email.py --html output/focus/focus_2026-06-05.html \\
            --dest "a@x.com,b@y.com" --assunto "Focus da semana"
    """
    # Garante UTF-8 no stdout para o console do Windows não quebrar ao imprimir
    # caracteres como o travessão "—" do assunto (cp1252 levantaria erro).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(
        description="Envia o resumo HTML do Boletim Focus por e-mail (SMTP do Gmail)."
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Caminho do .html a enviar (padrão: mais recente em output/focus/).",
    )
    parser.add_argument(
        "--dest",
        default=None,
        help=f"Destinatários separados por vírgula (padrão: variável {ENV_DEST}).",
    )
    parser.add_argument(
        "--assunto",
        default=None,
        help="Assunto do e-mail (padrão: 'Resumo Focus — AAAA-MM-DD').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Monta e exibe o e-mail SEM enviar e SEM exigir credenciais.",
    )
    args = parser.parse_args()

    # Resolve o arquivo HTML a enviar
    if args.html:
        html_path = args.html
    else:
        html_path = html_mais_recente()
        if html_path is None:
            print(
                "Nenhum focus_*.html encontrado em output/focus/. "
                "Gere o resumo antes de enviar."
            )
            sys.exit(1)

    if not html_path.is_file():
        print(f"Arquivo não encontrado: {html_path}")
        sys.exit(1)

    # Assunto: usa o informado em --assunto ou deriva do nome do arquivo
    assunto = args.assunto or assunto_padrao(html_path)

    # Destinatários: --dest tem prioridade sobre a variável de ambiente
    destinatarios = _split_emails(args.dest or os.environ.get(ENV_DEST))
    bcc = _split_emails(os.environ.get(ENV_BCC))

    # ----- Modo dry-run: monta e mostra, sem enviar e sem exigir credenciais -----
    if args.dry_run:
        # No dry-run o remetente pode estar ausente; montamos mesmo assim só
        # para validar o HTML e gerar a prévia em texto.
        remetente = os.environ.get(ENV_USER, "")
        msg = montar_email(html_path, remetente, destinatarios, assunto, bcc)

        # Imprimimos os valores calculados diretamente (e não msg['From'] etc.),
        # pois parênteses em cabeçalhos de e-mail são tratados como comentários
        # pela RFC 5322 e o aviso de placeholder seria descartado na exibição.
        print("=== DRY-RUN: e-mail montado; nada será enviado ===")
        print(f"HTML    : {html_path}")
        print(f"De      : {remetente or f'(não definido — defina {ENV_USER})'}")
        print(
            "Para    : "
            + (", ".join(destinatarios) or f"(nenhum — use --dest ou defina {ENV_DEST})")
        )
        if bcc:
            print(f"Cco     : {', '.join(bcc)}")
        print(f"Assunto : {assunto}")
        # Mostra uma prévia do fallback em texto para conferência rápida
        texto = msg.get_body(preferencelist=("plain",)).get_content()
        previa = texto[:500] + ("…" if len(texto) > 500 else "")
        print("--- prévia (texto) ---")
        print(previa)
        return

    # ----- Envio real: exige credenciais e ao menos um destinatário -----
    usuario = os.environ.get(ENV_USER, "")
    senha = os.environ.get(ENV_PASSWORD, "")

    faltando = [
        nome
        for nome, valor in ((ENV_USER, usuario), (ENV_PASSWORD, senha))
        if not valor
    ]
    if faltando:
        print(
            "Variáveis de ambiente obrigatórias ausentes: "
            + ", ".join(faltando)
            + ". (Use --dry-run para testar sem credenciais.)"
        )
        sys.exit(1)

    if not destinatarios:
        print(f"Nenhum destinatário informado. Use --dest ou defina {ENV_DEST}.")
        sys.exit(1)

    msg = montar_email(html_path, usuario, destinatarios, assunto, bcc)
    enviar(msg, usuario, senha)

    print("E-mail enviado com sucesso.")
    print(f"De      : {usuario}")
    print(f"Para    : {', '.join(destinatarios)}")
    if bcc:
        print(f"Cco     : {', '.join(bcc)}")
    print(f"Assunto : {assunto}")


if __name__ == "__main__":
    main()
