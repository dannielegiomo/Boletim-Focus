# Boletim Focus – Pipeline BCB

Pipeline que baixa o Boletim Focus do Banco Central do Brasil toda
segunda-feira, extrai o texto do PDF e, numa automação agendada, aciona um
agente de IA que lê o texto extraído e gera um resumo executivo — deixando-o
como rascunho de e-mail no Gmail para revisão humana antes do envio.

> **Importante:** os scripts Python fazem apenas o download e a extração do
> texto. O resumo executivo é escrito por um agente que lê o conteúdo do
> arquivo `.txt` e produz um markdown estruturado com as principais medianas
> do boletim. Nenhum número é inventado: toda estatística citada no resumo
> deve estar presente no texto original.

---

## Estrutura de pastas

```
Projeto_Boletim_Focus/
├── src/
│   ├── baixar_focus.py      # download do PDF do BCB com retrocesso de feriados
│   └── extrair_texto.py     # extração de texto via pdfplumber
├── tests/
│   ├── test_baixar_focus.py # testes unitários e de rede para o download
│   └── test_downloader.py   # testes unitários para utilitários de data
├── data/                    # PDFs e .txt baixados (não versionados)
├── output/
│   └── focus/               # resumos executivos em markdown (versionados)
├── .github/
│   └── workflows/
│       └── focus-download.yml  # GitHub Action: baixa e extrai toda segunda
├── demo.py                  # roda o pipeline completo localmente
├── requirements.txt
├── pytest.ini
└── CLAUDE.md                # briefing do projeto para o agente de IA
```

---

## Como rodar localmente

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Executar o pipeline

```bash
# Baixa o PDF mais recente e extrai o texto; --abrir abre o .txt no navegador
python demo.py --abrir
```

Os arquivos são salvos em `data/`:

```
data/focus_2026-06-05.pdf
data/focus_2026-06-05.txt
```

### 3. Rodar apenas um passo

```bash
# Só o download
python src/baixar_focus.py

# Só a extração (usa o PDF mais recente de data/ por padrão)
python src/extrair_texto.py

# Extração de um PDF específico
python src/extrair_texto.py --pdf data/focus_2026-06-05.pdf
```

---

## Como rodar os testes

```bash
# Testes offline (sem chamada de rede) — recomendado para CI local
pytest -m "not network"

# Todos os testes, incluindo o download real do BCB
pytest
```

O marker `network` sinaliza testes que fazem requisição real. Pule-os com
`-m "not network"` quando estiver sem acesso à internet ou em ambientes de CI
sem saída para a web.

---

## Automação semanal

O workflow `.github/workflows/focus-download.yml` roda toda segunda-feira às
9h15 BRT (12h15 UTC) e faz o download + extração automaticamente, commitando
os arquivos de volta ao repositório. Pode ser disparado manualmente pela aba
**Actions** do GitHub.

O resumo executivo e o rascunho de e-mail no Gmail são gerados por uma etapa
separada (agente de IA) que consome o `.txt` produzido por este pipeline.
