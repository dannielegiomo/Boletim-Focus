# Projeto Boletim Focus – BCB

## Objetivo
Baixar o Boletim Focus do Banco Central do Brasil toda segunda-feira, extrair
o texto do PDF e gerar um resumo executivo em markdown.

## Fonte
- Página de publicações: https://www.bcb.gov.br/publicacoes/focus
- Padrão de URL do PDF: `https://www.bcb.gov.br/content/focus/focus/R{AAAAMMDD}.pdf`
  - `AAAAMMDD` é a data de publicação (ex.: `R20240108.pdf` para 08/01/2024).

## Estrutura de pastas
```
Projeto_Boletim_Focus/
├── src/                  # código-fonte do projeto
├── tests/                # testes automatizados
├── data/                 # PDFs e textos extraídos (nunca versionar PDFs grandes)
├── output/
│   └── focus/            # resumos executivos em markdown
└── .github/
    └── workflows/        # automações CI/CD e agendamento semanal
```

## Convenções de nomenclatura
- Todos os arquivos gerados seguem o padrão `focus_AAAA-MM-DD`, onde a data
  é a data oficial de publicação do boletim (ex.: `focus_2024-01-08.pdf`,
  `focus_2024-01-08.txt`, `focus_2024-01-08.md`).
- `data/` armazena os PDFs baixados e os arquivos de texto extraídos.
- `output/focus/` armazena os resumos executivos em markdown.

## Regras de download
1. O Focus é publicado normalmente toda segunda-feira.
2. Quando a segunda-feira é feriado, o BCB publica na terça-feira (ou no
   próximo dia útil). O script deve retroagir dia a dia a partir da
   segunda-feira até encontrar um PDF válido (máximo de 7 tentativas).
3. Nunca inventar número: toda mediana ou estatística citada no resumo deve
   estar explicitamente presente no texto extraído do PDF. Se um número não
   for encontrado no texto, omiti-lo ou sinalizar como não disponível.

## Regras de resumo
- O resumo executivo deve destacar: indicadores de inflação (IPCA, IGP-M),
  câmbio (USD/BRL), Selic, crescimento do PIB e quaisquer revisões
  relevantes em relação ao boletim anterior.
- Formato: markdown, com seções claras e uma tabela de principais medianas.
- Nunca inventar número — ver regra acima.

## Dependências esperadas
- `requests` ou `httpx` – download do PDF
- `pdfplumber` ou `pymupdf` – extração de texto
- `python-dotenv` – variáveis de ambiente (se necessário)
- Agendamento via GitHub Actions (`.github/workflows/`)
