# Proc-Separador

Prepara a impressão do PDF de encomendas (o "binder"), que mistura folhas de dois papéis
(A4-Etiqueta / A4-Normal), num só trabalho e pela ordem do original.

- **App:** https://nhmac.github.io/Proc-Separador/ (Chrome ou Edge; pode ser instalada como app)
- **Repositório:** https://github.com/nhmac/Proc-Separador (código-fonte no `main`; o site é gerado e publicado pelo GitHub Actions)
- **Versão atual:** web 1.8

O PDF é lido no browser e não é enviado para lado nenhum.

Fluxo (desde a 1.2; o modo antigo com ZIP e blocos saiu da web na 1.4):

1. Escolher o PDF e carregar em **Separar**. Desde a 1.8 o tipo é detetado sozinho, folha a
   folha, e o mesmo PDF pode misturar encomendas:
   - **Dreambooks / Fotoprix** (Fotolivros, Álbuns): a etiqueta é detetada pela imagem no canto da folha;
   - **DreambooksPro Express** (Biscates, Álbuns 00): a folha com o número de encomenda vai em
     etiqueta, as continuações em normal.
2. O que não se consegue classificar com segurança é recusado e nada é escrito.
3. Imprimir o **PDF original inteiro** no Acrobat, num só trabalho, com o papel maioritário. As
   folhas do outro papel vão como **folhas de inserção** do driver da Canon: a página mostra a
   fonte de papel e as linhas para copiar para o campo **Inserir**.
4. O driver só aceita 100 folhas de inserção por trabalho. Acima disso, a app parte o trabalho em
   partes: descarregar cada parte e imprimi-las pela ordem, cada uma inteira.

## Atualizar a app

O GitHub é a única fonte: funciona igual em qualquer PC ou no Claude Code na web.

1. `git pull` (sempre antes de começar).
2. Alterar `web/separador.html` e subir o "Versão web".
3. Testar: `py build_pages.py` gera o site em `_site/` (abrir o `_site/index.html`).
4. Publicar: commit e `git push`. O GitHub Actions ("Publicar site") gera e publica o site em
   1-2 minutos; os PCs recebem a versão nova ao abrir a app com internet.

Só usa a biblioteca padrão do Python e o git.

## Pastas

| | |
|---|---|
| `web/` | Fonte do site: `separador.html`, ícones PNG e bibliotecas em `vendor/`: pdf.js 3.11.174 (lê, Apache 2.0) e pdf-lib 1.17.1 (escreve as partes, MIT). O JSZip saiu na 1.4, com o ZIP |
| `.github/workflows/pages.yml` | Gera e publica o site a cada push ao `main` |
| `Inter/`, `icone.ico` | Fonte Inter (SIL OFL) e ícone, usados pelo site e pela versão Python |
| `binder-*.pdf`, `v1.5/` | PDFs de teste (só nos PCs, fora do git) (`v1.5/Binder1.pdf` é o de Biscates) |
| `separar_gavetas.py`, `separar_gavetas_gui.py`, `processamento_ui.py` | Versão Python original (referência da lógica; só tem o modo antigo de blocos e não tem o tipo Biscates) |
| `CLAUDE.md` | O domínio, as invariantes e as decisões já tomadas |

A lógica do site está no bloco `<script id="logica">` do `web/separador.html` e segue o
`separar_gavetas.py` função a função na análise. Uma alteração às regras faz-se nos dois sítios,
exceto no tipo Biscates e Álbuns 00, que só existe na web.

Alterações feitas diretamente no GitHub editam a fonte (`web/separador.html`) e são publicadas
pelo GitHub Actions: basta fazer `git pull` antes de trabalhar.

## Versão Python

Precisa do `customtkinter`, do `pypdf` e do `pdfplumber`, num ambiente virtual:

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe separar_gavetas_gui.py
```
