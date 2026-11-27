# Separador de Papel (Proc-Separador)

**Primeiro passo de cada sessão, antes de ler ou alterar código:** `git pull --ff-only`. O utilizador
trabalha em dois PCs e no Claude Code na web, e o GitHub é a única fonte. Se o pull falhar (alterações
locais por enviar, conflito, sem rede), parar e avisar o utilizador. Nunca forçar.

**No fim**, se houver alterações, commit e push (publicar só quando o utilizador pedir): não deixar
trabalho só neste PC.

Ferramenta de posto de trabalho para o PDF de encomendas (Dreambooks/Fotoprix, o "binder"), que mistura folhas de dois papéis. Distingue página a página o papel de cada folha e prepara a impressão **pela ordem do PDF original**, para o operador não ter de mudar de papel à mão página a página.

Na versão web (a que está em uso) imprime-se de uma só forma:

- **Um só trabalho (desde a 1.2):** o **PDF original**, impresso inteiro no Acrobat com o perfil do papel maioritário, e as folhas do outro papel como **folhas de inserção** do driver da Canon. A app só mostra a impressora, a gaveta e as linhas do campo **Inserir** para copiar. O driver só aceita **100 folhas de inserção por trabalho**: acima disso, desde a **1.3**, a app parte o trabalho em **partes** (um PDF por parte, cópia tal e qual do troço do original, impressos pela ordem), cada uma com 100 inserções no máximo.

Desde a **1.6** (2026-10-22) **não há carimbo nem guia** na web: a pedido do utilizador, que os considera obsoletos. Com as folhas de inserção cada continuação sai no sítio, por isso o carimbo deixou de ser preciso, e o guia nunca foi usado. Até 100 inserções a app não gera ficheiro nenhum. Ver "Decisões já tomadas".

Desde a **1.9** (2026-11-23) há um **segundo modo, escolhido à mão: Álbuns DBP - Divisão blocos**, para os álbuns DreambooksPRO, que reorganiza o PDF combinado em blocos por cópias (ver "Modo Álbuns DBP - Divisão blocos"). O modo **Original** (o de sempre) não mudou.

Desde a **1.8** (2026-11-19) **o tipo de PDF é detetado sozinho**, folha a folha, e um PDF pode misturar os dois tipos (ver "O domínio" → "Deteção automática"). Da 1.5 à 1.7.4 o operador escolhia primeiro o **tipo de PDF**: **Fotolivros / Álbuns Dreambooks** (a regra de sempre, etiqueta detetada pela imagem) ou **Biscates / Álbuns 00** (folhas DreambooksPro Express, e desde a 1.7.3 também os álbuns DreambooksPRO da pasta "00", em que a etiqueta é a folha com o número de encomenda visível). Ver "O domínio" → "Tipo de PDF".

O **modo antigo (ZIP)**, com o PDF partido em blocos por papel, foi **removido da web na 1.4** (2026-10-01), a pedido do utilizador. Continua a existir na versão Python e pode ser reposto a partir do git (ver "Restaurar o modo antigo").

A versão Python (desktop, customtkinter) é a origem da lógica de análise e a única que tem o modo de blocos. Não tem o modo de um só trabalho nem o tipo Biscates.

## Onde está o código

Tudo na raiz do projeto:

| Ficheiro | Papel |
|---|---|
| `web/separador.html` | **Fonte do site.** Lógica no `<script id="logica">`, interface no `<script>` seguinte. |
| `build_pages.py` | Gera o site em `_site/` (ignorado no git). Só usa a biblioteca padrão. |
| `.github/workflows/pages.yml` | A cada push ao `main`, o GitHub Actions corre o `build_pages.py` e publica o `_site/` no GitHub Pages. |
| `PROJETO.md` | O README do projeto (o `README.md` da raiz é o do GitHub, comentado de propósito pelo utilizador: não mexer). |
| `separar_gavetas.py` | Motor Python: deteção, agrupamento, escrita dos blocos e do guia. Funciona sozinho por linha de comandos. |
| `separar_gavetas_gui.py` | Janela Python (customtkinter). Só orquestra e mostra, não tem lógica de negócio. |
| `processamento_ui.py` | Aspeto comum da linha de apps "Processamento" (cores `COR`, fontes Inter, componentes). **Cópia idêntica** em `Processamento_Batches/` (AutoBatch) e `Processamento_PDF Scanner/`: alterar nas três e subir o `VERSAO_UI`. |
| `Inter/`, `icone.ico` | Fonte Inter (SIL OFL) e ícone, usados pelo site e pela versão Python. O ícone (`icone.ico`, `web/icon-192.png`, `web/icon-512.png`) é o "p" da família em amarelo (`#dbd136`); desde a 1.8.1 (2026-11-19, a pedido do utilizador) o "p" é branco com sombra, como nas outras apps (antes era escuro). |
| `requirements.txt`, `README.md` | Para recriar o `.venv` da versão Python. |
| `binder-álbuns-amador.pdf`, `binder-offset-fotolivros.pdf` | Os dois PDFs de teste, o banco de provas de tudo. Desde 2026-09-30 o `binder-álbuns-amador.pdf` é um lote real de 168 páginas (o "Binder1.pdf" da especificação da 1.2); o de 101 páginas usado até à 1.1 foi substituído. |
| `binder-álbuns-amador-x3.pdf` | O mesmo lote triplicado pelo utilizador (504 páginas, 123 inseridas): o banco de provas das partes, acima das 100 inserções. |
| `v1.5/` | Material da 1.5, trazido pelo utilizador a 2026-10-22: `Binder1.pdf` (31 páginas, **Biscates**: o banco de provas do tipo Biscates), `Binder2.pdf` (48 páginas, Fotolivros / Álbuns), o `proc-separador-express.patch` (diff contra o `index.html` da 1.4), o `separador.html` de referência e o `plano.md`. **Atenção ao nome:** este `Binder1.pdf` não é o "Binder1.pdf" da especificação da 1.2 (esse é o `binder-álbuns-amador.pdf`). |

## Versão web

Desde 2026-09-27 a app usa-se no browser: https://nhmac.github.io/Proc-Separador/. Os PCs do posto usam Chrome ou Edge. Passou a site porque o Smart App Control bloqueava os `.exe` sem assinatura (ver "Ambiente"). Tudo corre no browser (pdf.js lê, pdf-lib escreve): **nenhum ficheiro é enviado para lado nenhum**, e isso tem de continuar assim. Não introduzir pedidos de rede nem bibliotecas novas.

### Publicar

Desde 2026-11-08 a pasta do projeto **é o repositório** `nhmac/Proc-Separador` (código-fonte no `main`) e o site é gerado pelo GitHub Actions. O utilizador trabalha em dois PCs e no Claude Code na web: o GitHub é a única fonte.

- **Antes de mexer:** `git pull --ff-only` (ver o primeiro passo, no topo).
- Alterar só `web/separador.html` (e subir o "Versão web" do rodapé). Testar com `py build_pages.py` (gera `_site/`).
- Publicar = commit ("Versão X: …") e `git push` para o `main`. O workflow "Publicar site" gera e publica em 1-2 minutos; confirmar com `gh run list` e com `curl` ao site.
- Commits até à 1.7.4 são do site gerado (o histórico antigo, antes de o código entrar no repositório): o `index.html` desses commits está na raiz.
- Commits do site: 1.4 = `168f1a1`, 1.5 = `97677d1` ("Versão 1.5: tipo de PDF Biscates"), 1.6 = `c3bfde2` ("Versão 1.6: sem carimbo nem guia"), e na mesma 1.6 `06c6f9e` ("Área Impressão: resumo compacto e passos numerados", só a interface) e `d903b08` (auditoria: troca de PDF segura, PDF misto recusado; passos 2 e 3 só com o papel), 1.7 = `1e43046` ("Versão 1.7: barra de progresso com legenda") e, na mesma 1.7, `4c769b2` (textos dos passos 1 e 4 no infinitivo). A 1.7.1 (`8112c3b`), a 1.7.2 (`fcf9271`) e a 1.7.3 (`0ec28ed`, `e57b33e`) foram feitas pelo utilizador **diretamente no GitHub** (2026-10-23 e 2026-10-27) e passadas para `web/separador.html` a 2026-10-28. A 1.7.4 = `7a53116` ("Versão 1.7.4: tipos de PDF sem descrição e com nomes novos"). Só a 1.3 tem tag, `v1.3`. A fonte de qualquer versão recupera-se do `index.html` desse commit (ver "Restaurar o modo antigo", passo 1).
- Um patch trazido de fora (contra o `index.html` publicado) aplica-se à fonte com `patch -p1`. Depois do build, comparar o `_site/index.html` com a página de referência, se a houver.
- **Push recusado** (alterações feitas noutro PC, na web ou diretamente no GitHub): `git pull --rebase` e resolver. Nunca forçar o push. Alterações feitas no GitHub editam já a fonte (`web/separador.html`), não o site.
- **No Claude Code na web** (usado no PC do trabalho, que não tem git): as alterações vão para um ramo `claude/...`, não para o `main`. Para publicar, criar o pull request e o utilizador faz **Merge** no github.com (o Actions publica a seguir). Os PDFs de teste não existem lá: testar no site publicado.
- O `README.md` da raiz está comentado de propósito pelo utilizador ("COMO COMENTARIO DE PROPÓSITO, NÃO ALTERAR"): não mexer.
- O `sw.js` muda de versão sempre que algum ficheiro muda. Nos PCs a página nova pode só aparecer à segunda abertura, ou depois de Ctrl+F5. Confirmar pelo rodapé "Versão web 1.7.4" da sidebar, ou com `curl` ao site.
- O build acrescenta `[hidden] { display: none !important; }` (em `FONTES_CSS`). O `web/separador.html` aberto sozinho mostra overlays e o empty state por cima de tudo: **testar sempre o `_site/index.html`**.

### A página (1.7)

Especificação original: o `makeover-lógica.md`, já apagado pelo utilizador; o que interessa dele está nesta secção e na seguinte.

Linguagem minimalista, igual à da versão Python: dark mode, Inter, sidebar à esquerda com o botão verde em baixo e poucos pop-ups (só avisos e erros; não há pop-up de sucesso).

- **Sidebar:** título "Proc-Separador", subtítulo **"Para imprimir Fotolivros, Álbuns Dreambooks, Biscates e Álbuns 00"** (desde a 1.7.3, mudado pelo utilizador no GitHub; na 1.5 "… e Biscates"; antes "Para imprimir Fotolivros e Álbuns Dreambooks"), a secção **Tipo de PDF** (só até à 1.7.4: saiu na 1.8, com a deteção automática), **Escolher PDF…** (ou arrastar um só PDF), chip com nome, folhas e estado (`OK · 168/168 folhas ✓`), nota de privacidade, botão **Separar** e "Versão web 1.7.4".
- **Tipo de PDF (1.5 a 1.7.4; saiu na 1.8, com a deteção automática):** dois cartões de rádio (`.tipos` / `.tipo`, `name="tipo"`), só com o nome, sem descrição (desde a 1.7.4, a pedido do utilizador; antes tinham "Etiqueta detetada pela imagem no canto da folha" e "1.ª folha de cada encomenda em etiqueta, o resto em normal"): **Fotolivros / Álbuns Dreambooks** (`album`; até à 1.7.3 "Fotolivros / Álbuns") e **Biscates / Álbuns 00** (`express`; na 1.7.3 "Biscates e Álbuns 00", até à 1.7.2 só "Biscates"). Os nomes vêm de `Logica.TIPOS` (atributo `data-nome-tipo`).
  - **Sem valor por omissão**: Separar sem tipo dá o pop-up "Escolha primeiro o tipo de PDF: …" e marca o seletor (`.tipos.falta`, borda âmbar). O tipo é verificado antes do PDF;
  - mudar de tipo depois de separar deita fora o resultado ("Tipo mudado para … · carregue em Separar de novo");
  - os rádios ficam desativados durante a separação;
  - o nome do trabalho mostra o tipo numa pill (`.pill.neutro`) ao lado do nome do PDF; o texto do `#nome-trabalho` é `binder.pdfFotolivros / Álbuns` (sem separador).
- **Barra de progresso com legenda (1.7, 2026-10-22, igual nas três apps da linha):** `criarProgresso()`, num `<script>` próprio entre a lógica e a interface; o mesmo bloco de CSS e JS está no Proc-Batches e no Proc-Scanner, e no Python é o `ui.Progresso`. É a barra fina e, por baixo, o detalhe à esquerda e a "% · ~tempo que falta" à direita, com o título do separador do browser a mostrar a %. No fim fica verde ("Concluído em 18 s") e recolhe 1,5 s depois. Fases:
  - ao escolher o PDF: "A ler o PDF · 75 MB" (sem medida) e "PDF lido · 168 folhas";
  - ao separar: "A abrir o PDF · 75 MB" (sem medida, cerca de 7 s nos binders de 78 MB), "Folha n de N", "Parte k de P · nome" e "A conferir as folhas com o original…" (sem medida);
  - o progresso da lógica leva um 2.º argumento opcional `{fase, atual, total, nome}`; os números e os PDFs não mudam (verificado contra a 1.6);
  - o peso das fases: até 2 × `LIMITE_INSERCOES` folhas sai sempre uma só parte (a base é o papel maioritário, por isso as inserções são no máximo metade), e a análise é a barra toda; acima disso, análise 70 % e partes 30 % (medido no triplicado: 26 s e 12 s).
- **Arranque vazio:** o exemplo com dados fictícios foi **retirado pelo utilizador** a 2026-09-28. Não o repor.
- **Área "Impressão":**
  - **resumo compacto** (`.card.resumo`, desde 2026-10-22, a pedido do utilizador para descomplicar): o nome do PDF com a pill do tipo, as três contagens lado a lado (folhas no total; A4-Etiqueta com o número âmbar; A4-Normal com o número azul e as continuações; um quadrado da cor do papel serve de legenda das pills) e, por baixo, a linha de conferência. Os tiles grandes (com o fundo âmbar) saíram. **Não há botões no topo** desde a 1.6 (saíram "Descarregar guia" e "Descarregar PDF carimbado");
  - o contentor `#partes`, com **um cartão por parte** (`cartaoParte()`), em **passos numerados pela ordem do driver** (contador de CSS no `.rotulo::before`, `passo(rotulo, conteudo, dica)`):
    1. **PDF**: o nome do original e "Abrir no Acrobat e imprimir inteiro (Páginas: Tudo), num só trabalho."; com várias partes, o botão **Descarregar parte n** e o nome do ficheiro;
    2. **Impressora**: "Fonte de papel:" + a pill do papel base (âmbar para A4-Etiqueta, azul para A4-Normal). O nome do perfil (`Canon 2 › Cor › Gaveta 3`) **saiu do ecrã a pedido do utilizador** (2026-10-22); o `plano.perfilBase` continua na lógica;
    3. **Folhas de inserção**: "Fonte de papel:" + a pill do papel das inseridas (sem o "Gaveta N", também a pedido) e "Imprimir em: Somente na frente", com o caminho no driver como dica (Propriedades › Fonte de papel › Seleção do papel: Folhas de inserção › Configurações › Folhas inseridas). Sem inserções, o texto "Nenhuma: …" e não há passo 4;
    4. **Inserir**: cada linha com o botão **Copiar** (azul, `btn-principal azul copiar`) e, por baixo, `9 folhas · colar no campo Inserir e carregar em Adicionar` (com várias linhas, `Linha k de n · x folhas · um Adicionar por linha`). O nº de folhas só aparece aqui. O botão muda para "Copiado ✓" (fundo verde) durante 1,5 s; sem clipboard, seleciona o texto e mostra "Ctrl+C". No ecrã, cada intervalo fica inteiro (`<span>` nowrap + `<wbr>` depois das vírgulas), mas o texto copiado é a linha tal e qual;
  - **com uma só parte** (até 100 inserções) há um só cartão, sem cabeçalho e **sem download**: imprime-se o original. O `#nota-trabalho` fica escondido e o estado é "Pronto a imprimir";
  - **com várias partes:** cada cartão abre com `Parte n de N` + `x folhas · páginas a–b do original`, e o download é o passo 1; o `#nota-trabalho` (`.banner`, entre o resumo e os cartões) mostra "Mais de 100 folhas de inserção: o trabalho foi partido em N partes. Descarregue-as e imprima-as pela ordem, cada uma inteira."; o estado passa a "Pronto a imprimir · descarregue as N partes". **Desde a 1.9.2** (2026-11-23, a pedido do utilizador, para evitar erros) aparece também um **pop-up** (`avisoPartes()`, nos dois modos) a dizer que há N ficheiros para descarregar, com o nome, as folhas e as inserções de cada parte, e os passos: descarregar todas, imprimir pela ordem cada uma num trabalho à parte, usar só a linha do Inserir de cada parte. Até à 1.9.1 não havia pop-up;
  - a conferência independente: `"Binder2.pdf" = 48 folhas | Plano: 39 A4-Etiqueta + 9 A4-Normal = 48 folhas ✓` ou, com partes, `"binder-álbuns-amador-x3.pdf" = 504 folhas | Partes: 392 + 112 = 504 folhas ✓`. O original é contado com o pdf.js e tem de ter as folhas do plano; com partes, cada PDF gerado é contado também, cada um tem de ter as folhas da sua parte e a soma as do original. Senão, erro "não imprimir". O chip mostra `OK · <plano>/<original> folhas ✓`.
- **Não há modo antigo na página** desde a 1.4: sem ZIP, sem lista de blocos e sem "Ver encomendas". Não repor sem o utilizador pedir.
- **Não há impressão guiada na web** (decisão de 2026-09-27): uma página não abre o Acrobat. Não repor Abrir / Impresso / CONCLUÍDO sem o utilizador pedir.
- O botão continua a chamar-se "Separar". Mudar o nome só se o utilizador pedir.

### A lógica na web

O `<script id="logica">` não mexe no DOM (para se poder testar à parte) e segue o `separar_gavetas.py` função a função **na análise** (`palavras`, `imagens`, `detectaEtiqueta`, `numeroNoCabecalho`, `analisarPaginas`, `verificarFormato`). **Uma alteração às regras de análise faz-se nos dois sítios** (exceto o tipo Biscates, que existe só na web). O modo de blocos existe só no Python desde a 1.4. `separar(dados, nomePdf, {progresso, tipo})` faz análise → `verificarFormato` → `planoImpressao` → `pdfsPartes` e devolve `{info, plano, pdfs, avisos, nPaginas, tipo}` (`pdfs` vazio com uma só parte); só usa o pdf.js e o pdf-lib. **Desde a 1.8 o `tipo` por omissão é `"auto"`** (deteção folha a folha, a única que a página usa); `"album"` e `"express"` (as chaves de `TIPOS`) continuam a dar a regra manual; outro valor dá erro. Da 1.5 à 1.7.4 o `tipo` era obrigatório: os testes e scripts antigos que chamam `separar()` sem `tipo` para ter a regra dos álbuns têm agora de passar `{tipo: "album"}`.

O tipo (1.5) entra em:
- `analisarPaginas(pdf, caixas, progresso, tipo = "album")`: além de `gaveta`/`encomenda`/`estado`, cada página traz `imagemEtiqueta` (o `detectaEtiqueta` de sempre), `etiquetaAlbum` (desde a 1.7.2: `detectaEtiquetaAlbum`, só a etiqueta grande dos álbuns, `width > 200` e `height > 120`; o `imagens()` passou a devolver também `height`) e `rodapeExpress` (`RE_RODAPE_EXPRESS`, `/DreambooksPro\s+Express/i`, no texto da página). Em `album`, `gaveta = imagemEtiqueta ? 3 : 1`; em `express`, `gaveta = estado === "visivel" ? 3 : 1`. Tipo desconhecido → erro;
- `verificarFormato(info, rotacoes, tipo = "album")`: as verificações cruzadas (ver "O domínio" → "Tipo de PDF");
- `TIPOS` está exposto na `Logica`. O modo de um só trabalho (`partirTrabalho`, `planoImpressao`, `pdfsPartes`) existe **só na web**, por decisão do utilizador.

Saíram na 1.6 (estão na 1.5, commit `97677d1`, se for preciso repor): `carimbar()`, `pdfsCarimbados()`, `guiaImpressaoUnica()`, `NOME_GUIA`, `PONTOS_VERIFICACAO`, as constantes `CARIMBO_*` e `umDecimal`; na interface, os botões `#btn-guia` e `#btn-carimbado`, o `.acoes` e o seu CSS.

Armadilhas já resolvidas, não desfazer:
- o pdf.js descarta o texto fora da área da página, e o cabeçalho "invisível" está aí. A leitura faz-se numa cópia com a MediaBox/CropBox alargada (`abrirParaLeitura()`); sem isso as folhas `invisivel` passam a `ausente`;
- no pdfplumber um espaço separa sempre palavras: entre "Encomenda" e o número há um espaço de 2,9 pt, menos que a tolerância de 3 pt;
- as medidas seguem a MediaBox, como o pdfplumber (`top = altura - y`);
- os guias do Python saem com CRLF (a web já não tem guia desde a 1.6).

Limites conhecidos da análise (auditoria de 2026-10-22). Nenhum afeta os PDFs reais, que têm a MediaBox com origem 0, a CropBox igual à MediaBox e não têm /Rotate. Corrigir só se o template mudar ou o utilizador pedir:
- **Erram igual no Python e na web:**
  - MediaBox com origem ≠ 0: o `dentro` e o `detectaEtiqueta` comparam com 0..largura/altura sem descontar a origem, o que pode pôr uma folha no papel errado;
  - CropBox menor do que a MediaBox: conta como visível o que o Acrobat não imprime;
  - o `detectaEtiqueta` não tem limite inferior: uma imagem acima da página conta como etiqueta.
- **Divergem:**
  - a web separa palavras nos espaços sintéticos do pdf.js (a partir de cerca de 0,1 × o tamanho da letra) e o pdfplumber só acima de 3 pt. Nos reais, a folga entre "Encomenda" e o número é de 2,9 a 3,0 pt, mas há um carácter de espaço real;
  - o `x1` de cada palavra na web é estimado por proporção de caracteres.
- Os PDFs e os scripts desta auditoria ficaram no scratchpad dessa sessão (`paridade/`).

### Restaurar o modo antigo (web 1.3)

A 1.3, a última com o modo antigo, está neste repositório na tag **`v1.3`** (commit `83e2100`, do tempo em que o git só guardava o site gerado). O git dessa altura só tem o site, mas o build só embrulha a fonte, por isso a fonte recupera-se do `index.html`. Foi verificado a 2026-10-01, antes de remover, que a reconstrução dá o `web/separador.html` da 1.3 byte a byte.

1. `git show v1.3:index.html` e desfazer o `gerar_html()` do `build_pages.py`: a fonte é a linha do `<title>`, seguida do que vem depois do bloco `FONTES_CSS`, tirando o `</head>\n<body>\n` a seguir ao `</style>` e, no fim, o `<script>` que regista o service worker com o `</body>` e o `</html>`.
2. `web/vendor/jszip/` (`jszip.min.js` e `LICENSE.markdown`): `git show v1.3:vendor/jszip/<ficheiro> > web/vendor/jszip/<ficheiro>`, com a ferramenta Bash (o PowerShell estraga os bytes).
3. Repor no `COPIAR` do `build_pages.py` as duas entradas `vendor/jszip/…`.
4. `py build_pages.py` e confirmar que `_site/index.html` e `_site/vendor/` ficam iguais aos da `v1.3` (`git show v1.3:index.html | diff - _site/index.html`).

Para repor só o modo antigo numa versão mais recente, o que saiu na 1.4 foi: na lógica, `escrever()` e `criarZip()` (com `separarOrfas`, `porEncomenda`, `ordemDasEncomendas`, `agruparOrfasPorEncomenda`, `agruparBlocos`, `ROTULO_CONTINUACAO` e `NOME_LOTE_ORFAS`); na interface, o `<details class="antigo">`, o CSS da lista (`.antigo`, `.lista`, `.linha`, `.encomendas`, `.link`), `linhaBloco()`, `descricaoGaveta()`, a contagem dos blocos no handler do Separar e o botão do ZIP.

Em emergência, a forma mais rápida de repor o site é reconstruir a fonte como acima e fazer push: o GitHub Actions publica-a.

## Impressão num só trabalho (1.2), em partes acima de 100 inserções (1.3), e o driver

### O que já foi validado no driver (pelo utilizador)

- A Canon 2 está instalada no Windows como **uma impressora por perfil**: `Canon 2 › Cor › Gaveta 3` (A4-Etiqueta) e `Canon 2 › Cor › Gaveta 1` (A4-Normal). Estes nomes estão em `PERFIL`.
- Caminho no driver: Propriedades → Fonte de papel → Seleção do papel: **Folhas de inserção** → Configurações de folhas de inserção → tipo **Folhas inseridas**, com Fonte de papel, **Imprimir em: Somente na frente** e o campo **Inserir**.
- Com "Somente na frente", a folha inserida **substitui** a página indicada; não acrescenta folhas.
- O campo aceita números e intervalos separados por vírgulas, sem espaços (`3,5,7-12`). **Testados:** 344 caracteres e 100 páginas numa só entrada, sem problemas.
- Páginas repetidas entre entradas bloqueiam o botão Adicionar.
- **Limite de 100 folhas de inserção** (teste de 2026-10-01): `1-100` é aceite; com `1-101` o botão **Adicionar** fica cinzento. O driver **recusa**, não corta em silêncio.
- Os números são os das páginas **do trabalho enviado**: imprime-se sempre o PDF inteiro (Páginas: Tudo). Por isso, com várias partes, as linhas do Inserir estão na **numeração de cada parte** (1…total da parte), nunca na do original.

### Como a app faz

- `partirTrabalho(info, gavetaInseridas, limite = LIMITE_INSERCOES)` → `{cortes: [[inicio, fim), …], repartidas}` (índices do original, base 0):
  - grupos = troços seguidos com a mesma `encomenda` (o código inteiro, `3452270_643175`; dois itens da mesma encomenda são dois grupos);
  - guloso, com **partes cheias**: junta grupos enquanto as inserções couberem no limite; quando o grupo seguinte não cabe, a parte fecha **antes** dele. O corte fica sempre num início de encomenda (decisão do utilizador);
  - caso extremo: uma encomenda sozinha com mais de 100 inserções vai enchendo as partes e é cortada por dentro, logo antes da folha inserida que passaria o limite. Fica em `repartidas` e dá um `ATENÇÃO`;
  - com várias partes, todas têm pelo menos uma inserção;
  - verifica antes de devolver (como a cobertura dos blocos): cortes contíguos, todas as páginas uma vez, nenhuma parte acima do limite. Senão, erro e não sai nada.
- `planoImpressao(info)`:
  - base = papel com mais folhas **do PDF inteiro** (empate: A4-Etiqueta). É **o mesmo perfil em todas as partes**;
  - `partes: [{n, de, ate, total, contagem, paginasInseridas, linhas, folhasPorLinha}]`: `de`/`ate` são páginas do original (base 1); `paginasInseridas` e `linhas` estão na numeração da parte, em intervalos sem espaços (`intervalos()`);
  - `dividirLinhas()` junta-as em linhas de no máximo `LIMITE_CARACTERES` (300), cortando **só nas vírgulas**; `folhasPorLinha` dá as folhas de cada uma;
  - no topo ficam `total`, `contagem`, `base`, `perfilBase`, `gavetaInseridas`, `paginasInseridas` (na numeração do original, **só para contagens**), `semInsercoes`, `continuacoes` e `avisos`. **`linhas` e `folhasPorLinha` já não existem no topo**: com várias partes estariam na numeração do original e seriam perigosas;
  - cada continuação tem `pagina` (original), `parte` e `paginaNaParte`;
  - `avisos`: continuação sem número (o mesmo `ATENÇÃO` do Python, `avisoSemNumero()`); continuação que não vem logo a seguir a uma folha da mesma encomenda; encomenda repartida entre partes. O aviso "acima de 100 não foi testado" da 1.2 **saiu**;
  - tudo do mesmo papel → `semInsercoes`, e o cartão diz para imprimir só com o perfil base, sem Folhas de inserção.
- `pdfsPartes(origem, info, nomePdf, partes)`: **só com várias partes** (com uma devolve `[]`). Um PDF por parte, cópia tal e qual do troço do original (as mesmas páginas, pela mesma ordem, sem carimbo). Nomes: `nome_parte_1de2.pdf` (com zeros à esquerda a partir de 10 partes, para a ordem dos nomes ser a de impressão). Cada um é relido no fim: se as folhas de uma parte, ou a soma de todas, não baterem, dá erro e não sai nada. `separar()` devolve `pdfs: [{nome, bytes, folhas}]`.
- Com as continuações no sítio, a invariante 3 (órfãs da mesma encomenda juntas) só se aplica ao lote do modo de blocos (Python). No trabalho único, cada continuação sai onde está no original, a seguir à sua folha principal. Nos binders de teste isto verifica-se sempre (às vezes com duas continuações seguidas). Se um dia não se verificar, sai o aviso (pop-up) "continuações que não vêm logo a seguir a uma folha da mesma encomenda".

### Limites do driver: o que se sabe e o que falta

**Resolvido a 2026-10-01:** o teto é de **100 folhas de inserção** (`1-100` entra, `1-101` deixa o Adicionar cinzento), e o driver **recusa** em vez de cortar sem aviso. O caso perigoso (folhas de fora a sair no papel errado) não se verificou. Desde a 1.3 nenhum trabalho gerado pede mais de 100 (`LIMITE_INSERCOES`), por decisão do utilizador: partir em vários trabalhos, corte sempre entre encomendas, partes cheias e um botão de download por parte (o guia saiu na 1.6).

**Por confirmar (não bloqueia):**

1. se os 100 são **no total do trabalho** ou **por entrada**. O teste foi com uma só entrada e não distingue os dois casos; partes de ≤ 100 funcionam em ambos. Teste barato: adicionar `1-100` e depois tentar adicionar `101-102`.
   - Recusado → o limite é total, a implementação fica como está.
   - Aceite → o limite é por entrada: bastaria limitar cada linha a 100 folhas e voltar a um só trabalho (alteração pequena, **só com pedido do utilizador**);
2. quantas **entradas** a lista do driver aceita. Nunca foram testadas várias entradas seguidas. Com 100 folhas no máximo por parte, uma parte só passa de uma linha com muitas folhas isoladas (100 folhas isoladas de 3 dígitos dão 2 linhas);
3. se o driver valida os números contra o total de páginas do trabalho.

O que protege:
- partes com 100 inserções no máximo, verificado no `partirTrabalho()` antes de escrever;
- linhas de 300 caracteres no máximo, abaixo dos 344 testados;
- o nº de folhas de cada linha do Inserir, mostrado por cima dela no cartão (e o total da parte em "Folhas inseridas"), para conferir com a lista do driver. O guia, com o "confirmar N linhas na lista", os pontos de verificação e a JUNÇÃO entre partes, saiu na 1.6.

Como testar sem gastar papel: fazer os passos até ao fim e carregar em **Cancelar**, confirmando que cada linha entra inteira, que o Adicionar funciona em todas e que a contagem da lista bate com a da página.

Se aparecer outro limite:
- **por entrada (caracteres):** baixar `LIMITE_CARACTERES` (o resto adapta-se);
- **no total de folhas:** ajustar `LIMITE_INSERCOES` (as partes adaptam-se);
- **no total de entradas:** baixar o `LIMITE_INSERCOES`, para cada parte ficar com menos linhas. O modo antigo já não está na página; só voltaria pelo git.

Resultados dos testes do driver (registar aqui os novos, quando o utilizador os trouxer):

- 2026-09-30 — `binder-álbuns-amador.pdf` triplicado pelo utilizador (`binder-álbuns-amador-x3.pdf`): 504 páginas, 123 inseridas, **uma só linha de 269 caracteres** na 1.2.
- 2026-10-01 — `1-100` aceite; `1-101` recusado (Adicionar cinzento). Com a 1.3 o triplicado dá 2 partes: 392 folhas com 100 inserções e 112 folhas com 23. Falta imprimir um lote real em partes e fazer o teste "por entrada ou no total".

## O domínio, em três conceitos

Os dois papéis chamam-se **`A4-Etiqueta`** e **`A4-Normal`** em tudo o que é visível: nomes de ficheiro, guia (Python), página e documentação. Foi o utilizador que escolheu estes nomes. Internamente continuam a ser `gaveta` 3 e 1 (`PAPEL = {1: "A4-Normal", 3: "A4-Etiqueta"}`), que são também os números das gavetas da Canon.

- **A4-Etiqueta** (3) — folhas COM etiqueta de envio (logo + código de barras + "Lote"), impressas em papel autocolante. Detetadas pela imagem grande no canto superior direito (`detecta_etiqueta()` / `detectaEtiqueta`). A etiqueta manda sempre: uma folha com etiqueta é A4-Etiqueta aconteça o que acontecer.
- **A4-Normal** (1) — tudo o resto. Há um segundo modelo de folha de encomenda (miniaturas de 75 pt em x=20, sem etiqueta) que é legitimamente A4-Normal com número visível (por exemplo a p91 do `binder-álbuns-amador.pdf`). Não é erro de deteção.
- **Folhas órfãs / de índice / continuações** — folhas de continuação das miniaturas, sem o número de encomenda **visível**. Depois de impressas ficam anónimas. No modo de blocos (Python) levam o carimbo com o número; na web o carimbo saiu na 1.6, porque no trabalho único ficam no sítio (ver "Decisões já tomadas"). São A4-Normal (`eOrfa`: gaveta 1 e estado ≠ `visivel`). No modo de blocos (Python) vão todas para um lote próprio, **CONTINUAÇÃO-INDEX** (`ROTULO_CONTINUACAO`), no ficheiro `Continuacao-Index_A4-Normal.pdf`, sem acentos de propósito. No trabalho único ficam no sítio.

O número de encomenda tem a forma `3452270_643175` e pode estar em três estados (`_numero_no_cabecalho()` / `numeroNoCabecalho`):

- `visivel` — impresso na folha, identifica-se sozinha;
- `invisivel` — está no conteúdo do PDF mas posicionado acima do bordo superior, por isso nunca é impresso. **Este é o cerne do problema**: para quem olha para a folha, é tão anónima como as que não têm cabeçalho;
- `ausente` — não há cabeçalho nenhum; herda o número da última folha anterior identificada.

### Deteção automática (web 1.8)

Desde a **1.8** (2026-11-19), a pedido do utilizador, **não há escolha de tipo na página**: o tipo é detetado folha a folha (`classificarAuto()`), e um PDF pode **misturar** encomendas Dreambooks / Fotoprix (etiqueta em imagem) e DreambooksPro Express no mesmo binder, para a app servir todos os processos. A página chama sempre `separar(…, {tipo: "auto"})` (o valor por omissão). Os dois tipos manuais continuam na lógica (`TIPOS`, `{tipo: "album"}` / `{tipo: "express"}`), para os testes e para repor o seletor se for preciso (está na 1.7.4, commit `7a53116`).

- Marcas de cada página, lidas no `analisarPaginas`: `etiquetaAlbum` (a etiqueta de envio dos álbuns em imagem, 284 × 195), `modeloExpress` (`RE_MODELO_EXPRESS`: o rodapé "DreambooksPro Express" **ou** o "LFM Express Nº" do cabeçalho da folha de etiqueta, porque há Biscates sem o rodapé) e `modeloAlbum` (`modeloAlbumNo()`: "Método de Pagamento" **e** "Saída Estimada", com E maiúsculo, do modelo Dreambooks / Fotoprix; as folhas Express têm "Pagamento:" e "Saída estimada:"). Medido a 2026-11-19 em 421 folhas reais: `modeloAlbum` em todas as 56 folhas Dreambooks / Fotoprix com número visível (48 com etiqueta e 8 do segundo modelo, trazidas pelo utilizador) e em nenhuma das 365 Express; `modeloExpress` em todas as Express e em nenhuma Dreambooks.
- PDF **sem nenhuma** folha Express → o PDF todo pela regra `album`; **sem nenhuma** folha Dreambooks (nem etiqueta de álbum em imagem nem `modeloAlbum`) → o PDF todo pela regra `express`. Nos dois casos o resultado é igual ao do tipo manual (verificado: plano igual ao da 1.7.4 nos troços puros do binder misto).
- **Misto** (as duas famílias no PDF): folha com número visível → etiqueta de álbum em imagem: A4-Etiqueta; só `modeloExpress`: A4-Etiqueta; só `modeloAlbum` (o **segundo modelo de folha**, miniaturas de 75 pt em x = 20): a regra dos álbuns, A4-Normal; folha sem número visível → A4-Normal (continuação), com a família herdada da última folha com número visível (`familia`).
- Recusas novas (`verificarFormato` com o tipo efetivo `misto` ou `indefinido`):
  - misto, folha com número visível **sem nenhuma das marcas, ou com as dos dois modelos**: recusa (podia ser etiqueta Express ou A4-Normal). A mensagem sugere separar essas encomendas num PDF à parte;
  - misto, continuação de álbum (família ≠ express) com etiqueta em imagem: a regra de sempre dos álbuns. Nas continuações Express a miniatura no canto é ignorada, como no tipo Express;
  - rodapé Express sem número visível (Express e misto);
  - nenhuma das duas marcas em todo o PDF (`indefinido`): "Não reconheço as folhas deste PDF".
- `separar()` devolve o tipo **efetivo** (`album`, `express` ou `misto`) e `composicao` (`{album, express}`, folhas de cada família). A página mostra o tipo na pill (`nomeTipo()`: "Misto" no misto) e, por baixo das contagens, o `#linha-tipos` ("Dreambooks / Fotoprix: 48 folhas · DreambooksPro Express: 176 folhas", nomes em `FAMILIAS`).
- Os Álbuns 00 (PDF "álbuns geral", 284 folhas) e os Biscates (111 folhas) do utilizador têm todos o rodapé e o "LFM Express". As folhas Express **sem rodapé** são raras; os dois exemplos do utilizador (`6524360_1499423_label.pdf` e `6521088_1493712_label.pdf`, 2026-11-19, "Tipo: A - Dreambooks") têm o "LFM Express Nº" no cabeçalho e passam: sozinhas, igual à 1.7.4 Biscates (3131); num misto com etiquetas Dreambooks e uma folha do segundo modelo, A4-Etiqueta com as continuações em A4-Normal. Uma folha Express sem rodapé **e** sem "LFM Express" daria `indefinido` (sozinha) ou ambígua (num misto): recusa, nunca papel errado.

### Tipo de PDF (web 1.5)

Da 1.5 à 1.7.4 escolhido à mão pelo operador; desde a 1.8, detetado (ver acima). Decide como se reconhece a folha A4-Etiqueta:

- **Fotolivros / Álbuns Dreambooks** (`album`) — a regra de sempre, descrita acima (imagem da etiqueta no canto superior direito). Com este tipo, a 1.5 deu exatamente os mesmos PDFs e plano que a 1.4, e a 1.6 o mesmo plano que a 1.5.
- **Biscates** (`express`) — folhas **DreambooksPro Express**. A etiqueta não é imagem (código de barras em fonte, logótipo pequeno), por isso o `detectaEtiqueta` não serve. Cada encomenda tem sempre uma folha de etiqueta, **a que tem o cabeçalho "Encomenda N_N" visível**, com o rodapé "DreambooksPro Express". Tudo o resto (páginas de miniaturas, continuações da tabela) é A4-Normal e, como não tem número visível, é continuação.
  - Nas páginas de miniaturas o template já imprime o código `N_N` no canto superior direito (x ≈ 498, top ≈ 13), mas sem a palavra "Encomenda": o estado é `ausente` e o número herda-se da etiqueta anterior (é o mesmo).
  - Algumas miniaturas calham no canto superior direito e o `detectaEtiqueta` dá-as como etiqueta (`imagemEtiqueta` verdadeiro em folhas `ausente`). É um falso positivo esperado. A regra Biscates ignora-o, e é por isso que um PDF Biscates é recusado como Fotolivros / Álbuns.
  - Serve também, desde a 1.7.3, para os **álbuns DreambooksPRO da pasta "00"** (1 ou mais de 2 folhas), que têm as mesmas folhas: a 1.ª folha de cada encomenda em etiqueta, o resto em normal.
  - "Biscates / Álbuns 00" (na 1.7.3 "Biscates e Álbuns 00", até à 1.7.2 "Biscates") é um nome **provisório**, escolhido pelo utilizador: o nome original era "Express". Para o mudar, muda-se só `TIPOS.express` e o subtítulo da página.

Verificações cruzadas (`verificarFormato`), todas com erro e "nada foi escrito", e a sugestão "Confirme o tipo de PDF: se for …, escolha esse tipo e separe de novo." quando faz sentido:
- **Biscates / Álbuns 00** (regras da 1.7.2, feitas pelo utilizador no GitHub):
  - folha com número visível e a **etiqueta grande dos álbuns** (`etiquetaAlbum`, 284 × 195 pt) → recusa (é de álbum). Antes contava qualquer imagem do `detectaEtiqueta`, e o carimbo "AGRUPADO" (118 × 32) das folhas Biscates dava falsos positivos; o logótipo dessas folhas tem 97 × 29;
  - a recusa "folha com número visível sem o rodapé Express" **saiu na 1.7.2**: há encomendas Biscates sem esse rodapé;
  - folha com o rodapé Express sem número visível → recusa (iria para A4-Normal sem ser continuação).
  - Verificado a 2026-10-28 no site publicado: `v1.5/Binder1.pdf` passa (22 A4-Etiqueta); `v1.5/Binder2.pdf`, `binder-offset-fotolivros.pdf` e `binder-álbuns-amador.pdf` continuam recusados.
- **Fotolivros / Álbuns:**
  - a regra de sempre (etiqueta sem número visível → recusa). Se o PDF tiver rodapés Express, a mensagem sugere Biscates;
  - folha com número visível e rodapé Express, sem etiqueta em imagem → recusa (auditoria de 2026-10-22: um PDF misto, álbum + folhas Express, passava com as etiquetas Express em A4-Normal);
  - nenhuma etiqueta em imagem e há rodapés Express → recusa (um PDF Express sem miniaturas passaria com zero etiquetas).

## Modo Álbuns DBP - Divisão blocos (web 1.9)

Desde a **1.9** (2026-11-23), a pedido do utilizador, a página tem um seletor **Modo** (`input[name="modo"]`) com dois modos à parte, escolhidos à mão:

- **Normal** (por omissão; chamava-se **Original** até à 1.9.2 — o `value` do rádio continua `original`): tudo o que está descrito acima, sem nenhuma alteração (verificado: `info`, `plano`, `avisos` e PDFs das partes byte a byte iguais aos da 1.8.1 no combinado real de 20/11).
- **Álbuns DBP - Divisão blocos** (`Logica.NOME_MODO_BLOCOS`; o nome foi escolhido pelo utilizador): para o PDF combinado dos `*_label.pdf` dos álbuns DreambooksPRO do dia, pela ordem das pastas de papel (sem Proc-Scanner e sem as pastas 00 / #Basic). Devolve **sempre** um PDF novo (o lote), para descarregar e imprimir inteiro com o perfil de **frente e verso** da A4-Etiqueta e as folhas A4-Normal como folhas de inserção. Mudar de modo deita fora o resultado; os rádios ficam desativados durante a separação.

Desde a **1.9.3** (2026-11-27, a pedido do utilizador) cada modo tem uma descrição curta por baixo do nome (`.modo .desc`): Normal = "Imprime o PDF pela ordem em que está. Serve para todos os PDFs DBP, DBC e FTX."; Álbuns DBP = "Só para álbuns DBP. Separa o lote em blocos: com cópia, sem cópia e índices." A lógica não mudou.

É a **única exceção à invariante 1** (ordem do original), decidida pelo utilizador: dentro de cada álbum a ordem das folhas mantém-se e as continuações com dados ficam sempre coladas; só mudam de sítio os álbuns sem cópia (bloco 2) e as folhas de índice a mais (bloco 3). As páginas do original nunca são alteradas: só se reordenam e se acrescentam a folha de rosto, os separadores e versos em branco.

O lote: folha de rosto (totais, conferência, linhas do Inserir e, desde a **1.9.1**, o **texto das observações** de cada álbum com a página da etiqueta; passa a duas ou mais folhas se for preciso), separador, **bloco 1** (com cópia do Atelier), separador, **bloco 2** (sem cópia), separador, **bloco 3** (índices a mais dos álbuns do bloco 1, pela ordem do bloco 1; cada folha tem o código `N_N` no topo e junta-se ao álbum na picagem; desde a **1.9.1** o separador do bloco 3 mostra, ao lado de cada álbum, o **formato do papel** entre `[ ]`, por exemplo `6540404_1533337  (2 fl.)  [30x30]`, para encontrar o álbum na pilha: o PDF combinado não traz o nome das pastas). Dentro de cada bloco mantém-se a ordem do combinado.

Desde a 1.9.1 (2026-11-23, a pedido do utilizador): o texto das observações (`obsTexto`) vai do "Observações:" até ao fim da tabela, antes do "Ficheiros de:", sem o rodapé "DreambooksPro Express v2.0", em todas as folhas do álbum; o formato (`formatoDoAlbum()`) vem da linha "Papel Fotográfico - 30x25 - …" ou, sem ela, do primeiro produto com um formato (`20x20`, `38x25`). As páginas acrescentadas são compostas por `comporInfo()` e podem ter várias folhas; a folha de rosto depende da numeração, por isso compõe-se até o número de folhas estabilizar.

Regras (as mesmas do script usado nos testes reais de 19/11, 20/11 e 23/11):
- **Álbum** = uma folha com "Encomenda N_N" visível e as seguintes (todas têm o código `N_N` impresso; se não tiverem, recusa). Álbum repetido no PDF → recusa. A 1.ª folha tem de ter a tabela de produtos.
- **Página de dados** (`lerPaginaBlocos`): antes do marcador "Ficheiros de:", uma linha começada por um código de 7 dígitos, "Item Produtos" ou "Observações:". Senão é **índice** (só miniaturas).
- **Etiqueta**: cada álbum ocupa uma; frente = folha 1; verso = página 2 se for índice, senão **em branco** (uma continuação com dados nunca vai para o verso: a cópia do Atelier é só de frentes). As continuações com dados saem logo a seguir, em A4-Normal. Índices a mais: álbuns do bloco 1 → bloco 3; do bloco 2 → logo a seguir ao álbum.
- **Bloco 2** (`blocoDoAlbum`): capa (último segmento da linha `Capa - …`) Basic, KoyLab, Minibook 20x20, Christmas Photo Album, Heritage Golden Christmas Album ou Gold Book, ou `Formato - Mini Books`, **sem** linha `Mala / Box` (a **Bolsa Líbia** não conta como box). Tudo o resto, incluindo capa cortada pelo gerador ou folha sem capa, vai para o bloco 1 (uma cópia a mais custa menos do que uma em falta).
- Os produtos são o texto da coluna Produtos: as palavras a seguir ao código até uma folga de mais de 12 pt (`FOLGA_COLUNA`).
- Só aceita PDFs só com folhas DreambooksPro Express (tipo efetivo `express` da deteção da 1.8, com o mesmo `verificarFormato`); outro PDF → recusa, com a sugestão do modo Original.
- **Partes**: acima de `LIMITE_INSERCOES` folhas normais, o lote parte-se como no modo Original (`partirLote`): cortes só entre unidades (uma etiqueta com as folhas coladas, ou uma folha normal solta), partes cheias, linhas do Inserir na numeração de cada parte. Nomes: `<nome>_blocos.pdf` ou `<nome>_blocos_parte_1de2.pdf`.
- Memória: os combinados têm 170-300 MB. A leitura (pdf.js, no próprio PDF, sem a cópia do `abrirParaLeitura`: nas folhas Express o número está sempre visível) e a escrita (pdf-lib) não ficam abertas ao mesmo tempo. Num browser de teste com 8 GB passou o combinado de 284 MB (886 páginas, 404 álbuns) em cerca de 55 s.
- Verificações: cobertura (cada página do original exatamente uma vez), paridade (nenhuma folha de inserção a meio de uma etiqueta), releitura de cada PDF gerado e, na página, a contagem independente com o pdf.js.
- Páginas acrescentadas desenhadas com as fontes padrão do pdf-lib (Helvetica): só WinAnsi, o resto passa a "?" (`seguroWinAnsi`).

Resultados de referência (a sequência do lote igual, posição a posição, à do script Python dos testes reais; a coluna é a linha do Inserir):

```
combinado 23/11  616 pág, 273 álbuns (241 + 32)  -> 627 pág  1-2,187,224,277,350,383,448,459,492,535,558-627
                                    (1.9.1: rosto com 2 folhas, 22 observações -> 628 pág  1-3,188,225,278,351,384,449,460,493,536,559-628)
combinado 20/11  563 pág, 251 álbuns             -> 568 pág  1-2,407,438,493,508-568
combinado 19/11b 665 pág, 296 álbuns             -> 672 pág  1-2,67,92,101,468,599-672
combinado 19/11  886 pág, 404 álbuns, 284 MB     -> 894 pág  1-2,183,318,407,460,685,764,817-894
298 PDFs de teste combinados, 582 pág            -> 639 pág  1-2,35,254,285,306,389,396,437,606-639  (1.9.1: 640 pág, 1-3,…)
20/11 com limite 30 (teste das partes)           -> 3 partes: 532 + 30 + 6, 30/30/6 inserções, a sequência igual à de uma só parte
```
Na 1.9.1 a sequência é a mesma (as folhas acrescentadas contam como uma), só muda o número de folhas da folha de rosto; o 20/11 continua igual (rosto com uma folha).

Recusas testadas: álbum repetido, folha sem o código do álbum, PDF a começar numa folha de índice, PDF em branco, e (2026-11-23, com folhas reais trazidas pelo utilizador: `3482740_2071692_label.pdf` Dreambooks e `10256574_10361830_processed_label.pdf` Fotoprix) um PDF Dreambooks, um Fotoprix e um misto com álbuns DBP: os três recusados neste modo e aceites no modo Original.

Depois da validação das observações, os Basic do bloco 2 podem ficar fora da ordem das pastas nas folhas físicas (decisão do utilizador, 2026-11-23): não é preciso repô-los na ordem.

## Invariantes que não se podem quebrar

1. **A impressão sai pela ordem do PDF original.** Não se reordena nada. **Única exceção:** o modo Álbuns DBP - Divisão blocos (1.9), ligado à mão, em que só mudam de sítio os álbuns sem cópia e as folhas de índice a mais (ver a secção desse modo). Esta regra **tem prioridade sobre o número de mudanças de papel** (ver "Decisões já tomadas"). No trabalho único imprime-se o próprio original; com várias partes, os PDFs das partes juntos pela ordem das partes dão exatamente o original, folha a folha (cada parte é um troço seguido, sem alterações). No modo de blocos (Python), os blocos são troços seguidos do mesmo papel: concatenados por ordem alfabética dos nomes, dão exatamente as páginas não-órfãs por ordem crescente.
2. **Nenhuma página se perde nem se duplica.** A união dos índices usados tem de ser exatamente `range(n_paginas)`; o plano tem de ter o mesmo número de folhas do original; com várias partes, cada PDF tem as folhas do seu troço e a soma é a do original (os cortes do `partirTrabalho()` são contíguos e cobrem tudo uma vez).
3. **(Modo de blocos, Python) Toda a folha órfã da mesma encomenda sai junta no lote**, seja qual for o número delas, mesmo que no original apareçam separadas.
4. **Uma folha sem número de onde herdar nunca recebe um número inventado**: é assinalada em `ATENÇÃO` (no Python, sai sem carimbo).
5. **Nunca sair uma pilha incompleta sem aviso.** Houve um incidente real (versão antiga): no fim da impressão faltavam ~20 folhas seguidas, ou seja, um bloco inteiro. O motor não perdia páginas; a perda estava a jusante (pasta partilhada sem limpeza, escrita não atómica numa pasta vigiada, ou um bloco saltado). Proteções atuais, que não se removem:
   - verificação de cobertura antes de escrever;
   - `_verificar_formato()` / `verificarFormato`, que pára antes de escrever quando o PDF tem uma forma inesperada;
   - na web: a verificação de cobertura do `partirTrabalho()`, a releitura de cada PDF das partes e a contagem independente com o pdf.js (o original contra o plano e, com partes, cada PDF contra a sua parte);
   - no Python: `_limpar_saida()` tudo ou nada (muda os nomes para `.nome.apagar`; se algum estiver aberto, repõe e dá erro) e escrita tudo ou nada (`_escrever_pdf()` escreve `.nome.pdf.tmp`, `_verificar_saida()` relê, `_publicar()` dá o nome final, qualquer exceção chama `_desfazer()`);
   - a conferência no topo de cada guia (Python) e a linha de conferência da página (web);
   - na GUI Python: a confirmação ao marcar um bloco não aberto e o aviso de blocos em falta no fim.
6. **(Modo de blocos, Python) A ordem alfabética dos nomes é a ordem de impressão.** Prefixo de 2 dígitos (3 ou mais quando há mais de 99 blocos, ver `largura`) + papel no fim (`01_A4-Normal.pdf`, `02_A4-Etiqueta.pdf`…). O `Continuacao-Index_A4-Normal.pdf` começa por letra de propósito, para ficar sempre em último, inclusive com `--prefixo`. `_PADROES_GERADOS` reconhece também os nomes antigos (`gaveta1`/`gaveta3`, `indexs_…`), para limpar pastas de versões anteriores.

## Como o motor funciona (Python; a web segue-o só na análise)

`gerar_blocos()` é a espinha dorsal. Na web só existe o passo 1 (análise e verificação de formato); os passos 2 a 6 (blocos) saíram na 1.4:

1. `analisar_paginas()` — lê o PDF **uma só vez** e devolve, por página, `gaveta` / `encomenda` / `estado`, já com a herança de números resolvida. "Visível" quer dizer que a palavra "Encomenda" e o número estão **inteiros** dentro da página (x e y). Não basta o `top`: numa página rodada, o cabeçalho escondido fica fora pela lateral.
   - Logo a seguir, `_verificar_formato()` dá erro antes de escrever quando:
     - o PDF tem 0 páginas;
     - há páginas com `/Rotate`;
     - não há nenhum número `visivel` em todo o PDF (o template mudou);
     - uma página A4-Etiqueta não tem número visível. Cada etiqueta é uma encomenda distinta; sem número, as folhas de índice seguintes herdariam o da anterior.
   - Foi o utilizador que escolheu parar com erro em vez de avisar.
2. `separar_orfas()` — separa as folhas de índice do resto. Ambas as listas saem pela ordem do original.
3. `ordem_das_encomendas()` — sequência das encomendas na pilha impressa (principais pela ordem original, depois as que só têm órfãs). Serve para ordenar o lote de índices.
4. `agrupar_orfas_por_encomenda()` — ordena o lote de índices por essa mesma sequência.
5. `agrupar_blocos(info, restantes)` — junta páginas contíguas do mesmo papel. Como as órfãs já saíram, páginas A4-Etiqueta separadas só por uma folha de índice ficam no mesmo bloco.
6. Escreve os blocos, depois o lote (carimbando cada folha) e por fim o guia. Verifica e só então entrega (ver invariante 5).
   - `avisos` (uma lista) recebe o `ATENÇÃO` das folhas sem número, que as interfaces mostram num pop-up.
   - O carimbo parte da `cropbox` da página (`left + 20`, `top − 11`), não de (0,0). Com uma caixa deslocada, o `top` do pdfplumber engana. Para confirmar a posição, ler o `Td` no conteúdo com o pypdf.

O carimbo é só o código do cabeçalho, `3452270_643175` (nº de encomenda + item id). Uma encomenda com dois itens aparece com dois códigos (`10193434_235805` e `10193434_235806`). No Python é escrito à mão em sintaxe PDF (`_sobreposicao_numero()`), em latin-1: **evitar caracteres fora do ASCII no carimbo** (o `·` sai como bullet). Na web usou-se Helvetica-Bold do pdf-lib (`carimbar()`), com as mesmas medidas, até à 1.5.

### Resultados de referência (para apanhar regressões)

```
Modo de blocos (só Python, desde a web 1.4)
binder-offset-fotolivros.pdf  46 pág -> 01_A4-Etiqueta (31) + Continuacao-Index_A4-Normal (15)
binder-álbuns-amador.pdf     168 pág -> 27 blocos alternados (01 = A4-Etiqueta p1-10) + Continuacao-Index_A4-Normal (6)

Trabalho único (os dois com base Gaveta 3, inseridas da Gaveta 1, uma só linha)
binder-álbuns-amador.pdf     127 E + 41 N  11-17,24,28-30,42,45,52-63,68,74-75,79,81,86-87,90-92,112,132-133,139,148,165
                             continuações 68, 90, 92, 139, 148, 165 (a seguir a 67, 89, 91, 138, 147, 164)
binder-offset-fotolivros.pdf  31 E + 15 N  2,5,10-11,14,17,20,25-26,32,34,38,40,43,45
                             (p10-11 e p25-26: duas continuações seguidas)

Em partes (desde a 1.3; base Gaveta 3, inseridas da Gaveta 1)
binder-álbuns-amador-x3.pdf  381 E + 123 N, 18 continuações -> 2 partes
                             parte 1: 392 folhas (p1-392), 100 inserções, …_parte_1de2.pdf (até à 1.5: …_carimbado_1de2.pdf)
                             parte 2: 112 folhas (p393-504), 23 inserções, …_parte_2de2.pdf
                             Inserir da parte 2, na numeração da parte: 1-7,12,18-19,23,25,30-31,34-36,56,76-77,83,92,109
                             corte entre 3471981_672860 (p392) e 3471981_672861 (p393): dois itens da mesma encomenda

Tipo de PDF (desde a 1.5; uma só parte, base Gaveta 3, inseridas da Gaveta 1)
v1.5/Binder1.pdf  Biscates   31 pág, 22 encomendas: 22 E + 9 N, sem avisos
                             Inserir 2,4,7-8,11,20,22,29-30 (todas continuações)
                             continuações a seguir a 1, 3, 6, 7, 10, 19, 21, 28, 29 (p7-8 e p29-30 seguidas)
                             como Fotolivros / Álbuns: recusado (etiqueta sem número nas p2,4,7,11,20,22,30)
v1.5/Binder2.pdf  Álbuns     48 pág, 44 encomendas: 39 E + 9 N
                             Inserir 11,13,19,23,27,30,35,41,47
                             continuações 11, 13, 41, 47 (invisivel; a seguir a 10, 12, 40, 46);
                             19, 23, 27, 30, 35 são A4-Normal com número visível (o segundo modelo)
                             plano igual ao da 1.4; análise igual à do motor Python
                             como Biscates: recusado (etiqueta em imagem)
binder-offset-fotolivros.pdf e binder-álbuns-amador*.pdf como Biscates: recusados (etiqueta em imagem)

Biscates acima de 100 inserções (não há PDF real; gerado no scratchpad com o pypdf: v1.5/Binder1.pdf × 12)
Binder1-x12.pdf   Biscates   372 pág: 264 E + 108 N -> 2 partes, sem avisos
                             parte 1: 343 folhas (p1-343), 100 inserções em 2 linhas (83 + 17 folhas)
                             parte 2: 29 folhas (p344-372), 8 inserções: 2,5-6,9,18,20,27-28
                             corte entre 6529601_1508920 (p343) e a etiqueta de 6531158_1511678 (p344)

Deteção automática (desde a 1.8; o binder misto do utilizador, 2026-11-19, 224 pág)
Binder1 misto  auto -> misto: 48 Dreambooks / Fotoprix (p1-48) + 176 DreambooksPro Express
                             219 E + 5 N, uma só parte, base Gaveta 3, Inserir 57,59,77,89,91 (todas continuações Express)
                             = o plano da 1.7.4 com album nas p1-48 e express nas p49-224; recusado nos dois tipos manuais
troços puros (p1-48, p49-224) em auto: plano igual ao do tipo manual na 1.7.4
biscates.pdf (111 pág) e álbuns geral (284 pág, 2 partes) do utilizador, em auto: plano igual ao do tipo Biscates / Álbuns 00 na 1.7.4
8 folhas do segundo modelo Dreambooks (uma por PDF, 2026-11-19): sozinhas = album, 8 A4-Normal (igual à 1.7.4 Álbuns);
                             num misto com etiquetas Dreambooks e Biscates: A4-Normal (a 1.ª versão da 1.8, sem modeloAlbum, recusava-o)

Sem carimbo nem guia (desde a 1.6)
nos seis PDFs acima: análise, plano e avisos iguais aos da 1.5
uma só parte -> nenhum PDF; com partes, os PDFs juntos = original folha a folha (hash do conteúdo igual)
```

O `partirTrabalho()` e o `planoImpressao()` não dependem do tipo: um Biscates acima de 100 inserções parte-se como um álbum (verificado com o `Binder1-x12.pdf`, 2026-10-22). Para o recriar: `PdfWriter` com as 31 páginas do `v1.5/Binder1.pdf` adicionadas 12 vezes. Os únicos PDFs na pasta acima de 100 inserções são o `binder-álbuns-amador-x3.pdf` (álbum) e, gerado, este.

## Versão Python (desktop)

Continua a funcionar e tem impressão guiada, mas já não é a que o posto usa. Precisa do `.venv` (ver `README.md`), que neste momento não existe na pasta. O `.exe` e o `.bat` deixaram de existir; o código ainda tem referências a eles (`frozen`, `pythonw`) e os ficheiros `.py` mantêm o nome `separar_gavetas…` porque o motor é importado por esse nome.

Linguagem **minimalista**, pedida pelo utilizador. O aspeto é o da linha "Processamento", igual ao AutoBatch (`Processamento_Batches/main.py`). Tudo o que é cor, fonte ou botão vem do `processamento_ui.py`: não pôr cores soltas no `separar_gavetas_gui.py` (as cores por papel estão em `CORES_PAPEL`). A app chama-se **"Processamento · Separador de Papel"** (`NOME_APP`). A pasta da configuração é uma constante à parte, `PASTA_CONFIG = "Separador de Papel"`, que **não acompanha** o `NOME_APP`, para não se perder a hot folder guardada.

- **Um PDF de cada vez.** A GUI guarda `self.pdf` e `self.trabalho` (None ou dict), não listas.
- **Sidebar:**
  - **Escolher PDF…** e o chip do estado (`OK · N blocos · s/n folhas ✓` ou ✗);
  - **Separar** no fundo;
  - largar vários PDFs ou uma pasta dá «Largue só um PDF de cada vez»;
  - não há consola de logs (`_escrever_log()` só faz `print`);
  - não há pop-up de sucesso;
  - duas confirmações antes de separar: `_confirmar_recomeco()` (impressão a meio) e `_confirmar_substituicao()` (subpasta com ficheiros de uma separação não apagada);
  - `_esquecer_trabalho()` ao arrancar.
- **Robustez:**
  - o `("fim",)` é publicado num `finally`;
  - o `_drenar_fila` apanha erros por mensagem;
  - `root.report_callback_exception = _erro_inesperado`.
- **Hot folder:**
  - guardada em `%APPDATA%\Separador de Papel\config.json`; lê a do nome antigo (`Separador de gavetas`) enquanto essa não existir;
  - separar sem pasta, ou com uma inacessível, abre o `askdirectory`;
  - a saída é `<hot folder>\<nome do PDF>\`. Sem `raiz` (consola), é `<pasta do PDF>\hot_folder_amador\`.
- **Área Imprimir:**
  - painel `BLOCO n DE N` com o papel em letra grande (âmbar para A4-Etiqueta, azul para A4-Normal, verde no CONCLUÍDO);
  - **Abrir** (ou duplo clique numa linha), **Impresso ▶** e **Desmarcar**;
  - barra de progresso em folhas e as linhas `x de N blocos · f de F folhas impressas` e `"binder.pdf" = F folhas  |  Contagem total blocos separados: F folhas ✓` (contadas com `contar_folhas()` nos PDFs do disco);
  - lista em `CTkScrollableFrame`, com linhas criadas em lotes por `after`;
  - no fim, **Apagar ficheiros**: apaga só `ficheiros_gerados_em(pasta)`, nunca o original, e faz `rmdir` só se a pasta ficar vazia.
- **Removidos a pedido, não repor:**
  - as abas "1. Separar" / "2. Imprimir";
  - vários PDFs, "Limpar lista", "Adicionar pasta" e "Remover selecionados";
  - a combobox de PDFs;
  - "Retomar";
  - a caixa de Prefixo (o `--prefixo` existe só na consola);
  - "↻ TROCAR PAPEL", "Primeiro bloco" e "Conte a pilha";
  - Ctrl+O / Ctrl+Enter e ◀ ▶.
- O "impresso" vive só em memória (`trabalho["impressos"]`).

## Ambiente e armadilhas

- **Windows 11, PowerShell 5.1.** Português de Portugal em tudo o que é visível. O browser da máquina é o **Brave** (não há Chrome); os PCs do posto usam Chrome ou Edge.
- **Python global (`C:\Python314`, também pelo `py`):** tem o `pdfplumber` e o `pypdf` nos pacotes do utilizador (`%APPDATA%\Python\Python314`), por isso o motor e as verificações correm com `py`. **Não tem o `customtkinter`**: a GUI precisa do `.venv`. Para importar o motor a partir do scratchpad, `PYTHONPATH=.` na pasta do projeto.
- **Node 24** com `puppeteer-core` global (`%APPDATA%\npm\node_modules\puppeteer-core`, requerido pelo caminho completo).
- **Smart App Control está LIGADO** e bloqueia executáveis sem assinatura de reputação (incluindo PyInstaller). Foi por isso que a app passou a site. Desligar é irreversível sem reinstalar o Windows: **não mexer nisso**.
- Patches: escrever um script Python **num ficheiro** no scratchpad (Write) e corrê-lo, com `assert texto.count(velho) == 1` antes de cada substituição. Heredocs no Bash com muitas aspas e crases (código JS) falham com "unexpected EOF". Ficheiros sempre em UTF-8 com `newline="\n"`.
- A consola do Windows mostra os acentos como lixo: é só o codepage. Nos scripts de teste, `sys.stdout.reconfigure(encoding="utf-8")`. No PowerShell 5.1 as aspas dentro de `python -c` perdem-se: usar a ferramenta Bash.
- Para testar a GUI Python: copiar o PDF para o scratchpad, simular o `filedialog.askdirectory` e redirecionar o `APPDATA` para o scratchpad **depois** dos imports (antes parte o `import pypdf`). Nunca escrever no `config.json` real.

## Decisões já tomadas (não voltar a propor)

- **Reordenar encomendas por tipo de papel** (todas as A4-Etiqueta primeiro) — implementado e **recusado**: a impressão tem de sair pela ordem do original. A 1.9 não muda isto: o modo Álbuns DBP - Divisão blocos reorganiza por **cópias** (não por papel), só nos álbuns DBP e só quando é escolhido à mão.
- **Filas de impressão por gaveta / impressão direta pela aplicação** — não é possível criar impressoras no posto. A Canon 2 já está instalada como uma impressora por perfil de gaveta, e é isso que a 1.2 usa. A impressão direta continua fora de questão: uma página web não imprime com um perfil escolhido.
- **Juntar todas as folhas A4-Normal num lote único** — recusado: quebra a ordem original.
- **Vários PDFs de uma vez** — retirado: era a origem de várias falhas. Um PDF de cada vez.
- **Anomalias de formato: parar ou avisar?** — **parar com erro**.
- **Nº de ordem no carimbo e no guia** (`26 | 3452270_643175`) — retirado; fica só `encomenda_item id`. O "Item" da tabela (1990458…) também foi recusado.
- **Modo de um só trabalho na versão Python** — não fazer (decisão de 2026-09-30).
- **Modo antigo (ZIP) na web** — **removido na 1.4** (2026-10-01), a pedido do utilizador, que o considera obsoleto; o restauro faz-se pelo git (tag `v1.3`, ver "Restaurar o modo antigo"). Foi removido antes de haver um lote real impresso em partes: se as partes falharem no driver, a alternativa no posto é repor a 1.3. Não repor sem pedido.
- **Mais de 100 inserções** (2026-10-01) — partir em vários trabalhos, com corte sempre entre encomendas e partes cheias (123 → 100 + 23); um botão de download por parte. Desde a 1.6 os PDFs das partes saem sem carimbo e não há guia. Não voltar ao aviso da 1.2, nem equilibrar as partes. O corte pode cair entre dois itens da mesma encomenda (`3471981_672860` | `3471981_672861`): o utilizador confirmou que não há problema.
- **Tipo de PDF** — na 1.5 (2026-10-22) escolha manual e obrigatória, sem valor por omissão. **Mudado na 1.8 (2026-11-19), a pedido do utilizador:** deteção automática folha a folha, sem seletor, com PDFs mistos; o que não se consegue classificar com segurança é recusado (parar com erro), nunca adivinhado.
- **Carimbo e guia na web** — **removidos na 1.6** (2026-10-22), a pedido do utilizador. O carimbo só fazia sentido no modo de blocos, em que as continuações eram separadas e agrupadas à mão; com as folhas de inserção saem no sítio, e no posto a app já era usada sem o download do PDF carimbado. O guia nunca foi usado. Não repor sem pedido (estão na 1.5, commit `97677d1`).
  - **Até 100 inserções** imprime-se o **PDF original** inteiro (Páginas: Tudo): os números do Inserir são os do original. A app não gera ficheiro nenhum.
  - **Acima de 100** continua a haver **um PDF por parte**, cópia tal e qual do troço do original (sem carimbo), porque as linhas do Inserir estão na numeração de cada parte: o original inteiro com essas linhas poria as inserções nas folhas erradas. Foi a opção escolhida pelo utilizador por ser a única validada no driver. A alternativa sem PDFs (o original com Páginas `de`–`ate` de cada parte) fica por validar: não se sabe se, com um intervalo no Acrobat, o Inserir conta a partir do início do intervalo.

## Como testar

Nunca escrever nas pastas do utilizador durante os testes: usar o scratchpad da sessão.

### Web (depois de mexer em `web/separador.html`)

1. **Antes de mexer**, guardar uma referência: correr `Logica.separar` sem tipo (auto) no binder misto da 1.8 e nos outros, e (com `{tipo: "album"}`) nos três binders e no `v1.5/Binder2.pdf`, e com `{tipo: "express"}` no `v1.5/Binder1.pdf`, e gravar o `plano`, os `avisos` e os PDFs das partes. Em alternativa, comparar na mesma página com a lógica publicada (ver o último ponto dos unitários). Para ter um Biscates acima de 100 inserções, gerar o `Binder1-x12.pdf` no scratchpad (ver os resultados de referência).
2. Correr `py build_pages.py` e testar o **`_site/index.html`**:
   - servir a pasta do projeto com um `http.createServer` do Node (o pdf.js não carrega o worker em `file://`);
   - abrir o Brave com `puppeteer-core` (`executablePath` do Brave, `headless: true`) e **um `userDataDir` temporário no scratchpad**, que impede o service worker de ficar com versões antigas;
   - chamar a lógica com `page.evaluate` e devolver os bytes em base64. Com PDFs de 78 MB é mais simples a página fazer `fetch` do PDF ao servidor de teste e devolver cada ficheiro gerado com um `POST` ao mesmo servidor, que o grava no scratchpad (isto vive só no script de teste, nunca na app).
3. **Regressão:** nos três binders, nos dois `v1.5/Binder*.pdf` e no `Binder1-x12.pdf`, o `info`, o `plano` e os `avisos` iguais à referência, e os **PDFs das partes** byte a byte iguais (o pdf-lib com `updateMetadata: false` é determinístico). Os binders normais têm `partes.length === 1` e `pdfs.length === 0`; o triplicado e o `Binder1-x12.pdf`, 2. Cada PDF com o tipo errado tem de ser recusado.
4. **Unitários** do plano com `info` forjado:
   - lista longa (linhas ≤ 300, cortes só nas vírgulas, as linhas juntas dão as páginas todas);
   - mais normais do que etiquetas → base 1;
   - empate → base 3;
   - sem inserções;
   - continuação sem número;
   - continuação fora do sítio;
   - 100 inseridas → 1 parte; 101 → 2 partes (100 + 1); 250 → 3 partes;
   - nenhuma parte acima de 100, cortes só em inícios de encomenda, partes contíguas a cobrir tudo;
   - as linhas de cada parte, repostas na numeração do original, dão exatamente as inseridas globais;
   - encomenda sozinha com mais de 100 inseridas → corte interno + aviso, sem nenhuma parte vazia de inserções;
   - `partirTrabalho()` com `info` ao acaso e limites pequenos (o terceiro argumento);
   - plano igual ao da versão publicada, em `info` ao acaso (com uma e com várias partes): a lógica publicada tira-se do git (o `index.html` do site publicado, com `curl` ao site, o texto do `<script id="logica">`) e carrega-se na página com `new Function(texto + "\nreturn Logica;")()`;
   - `verificarFormato` com `info` forjado (com `imagemEtiqueta` e `rodapeExpress`): cada verificação cruzada da secção "Tipo de PDF", nos dois sentidos, e `separar()` sem tipo → erro.
5. **Reler em Python os PDFs das partes** (triplicado e `Binder1-x12.pdf`):
   - as partes juntas têm as folhas do original e o hash do conteúdo de **todas** as folhas é igual ao do original, pela mesma ordem (já não há carimbo);
   - em cada parte, as páginas das linhas do Inserir (do `plano`) são exatamente as A4-Normal dessa parte, na numeração da parte, e no máximo 100;
   - o corte fica num início de encomenda;
   - nos álbuns, `analisar_paginas()` do Python dá o mesmo papel e estado que a web.
6. **Interface:**
   - `uploadFile` no `#input-pdf`, **esperar pelo `#chip.escolhido`** (o `definirPdf` lê o PDF de forma assíncrona; clicar antes dá "Escolha primeiro o PDF.") e clicar em Separar (desde a 1.8 não há tipo a escolher);
   - o tipo detetado na pill do `#nome-trabalho` e a composição no `#linha-tipos`;
   - com uma só parte: nenhum botão de download, os passos 1-4, o banner escondido, o estado "Pronto a imprimir" e a linha `Plano: … ✓`;
   - para ver a classificação de um PDF novo, uma folha de contacto com as miniaturas das páginas (pdf.js num canvas) com a borda da cor do papel ajuda muito;
   - Copiar, com `overridePermissions` de clipboard e leitura com `navigator.clipboard.readText()`;
   - o download de cada parte (`Browser.setDownloadBehavior` por CDP), com hash igual ao dos PDFs da lógica;
   - `page.on("request")`: nenhum pedido para fora do servidor de teste;
   - um PDF em branco feito com o pypdf → pop-up de erro de formato e nada à vista;
   - com partes (triplicado ou `Binder1-x12.pdf`): dois cartões, cada um com "Descarregar parte n", Copiar em linhas de partes diferentes, a linha `Partes: … ✓`, e depois separar um binder normal para confirmar que a página volta a um cartão sem downloads;
   - screenshots a 1280 e a 390 px, sem scroll horizontal.
7. Publicar (commit e push) só quando o utilizador pedir. Depois, confirmar com `curl` que o site serve a versão nova.

A comparação com o Python página a página (estado, número, etiqueta, posição de cada imagem e da palavra "Encomenda") e bloco a bloco foi feita na 1.1. Repeti-la se se mexer na análise.

### Python

```
python separar_gavetas.py "binder-álbuns-amador.pdf"     --saida <scratch>/saida1
python separar_gavetas.py "binder-offset-fotolivros.pdf" --saida <scratch>/saida2
```

Verificar:
- a pilha principal, reconstruída por hash do conteúdo de cada página, igual a `restantes` por ordem crescente;
- o papel de cada página, sem dois blocos seguidos do mesmo papel;
- a soma das folhas e a cobertura exata;
- o carimbo relido com o pdfplumber (`0 <= top < 20`; o cabeçalho invisível tem `top` negativo).

Verificar também os caminhos de falha:
- bloco antigo aberto com `open(..., "rb")` → erro e pasta intacta;
- exceção a meio da escrita (monkeypatch em `PdfWriter.write`) → pasta sem ficheiros gerados;
- cada anomalia do `_verificar_formato()` → erro, sem criar a pasta.

**A janela:**
- montar com `ui.preparar()`, `root = ctk.CTk()` e `Aplicacao(root)`;
- trocar os `messagebox` por `print` (e o `askyesno` por respostas pré-definidas);
- chamar `_separar()` e bombear `root.update()` até `processando` ficar `False`;
- ao criar várias `Aplicacao` no mesmo teste, **não destruir as antigas** (o `Tcl_AsyncDelete` rebenta): guardá-las numa lista e sair com `os._exit(0)`;
- cliques: `event_generate("<ButtonPress-1>", ..., time=t)` no `_label` interno do `CTkLabel`. Dois `ButtonPress` no mesmo ponto fazem o duplo clique. **Passar sempre `time=`** a crescer, senão o Tk faz um triplo clique;
- ver o aspeto com o `PIL.ImageGrab`, recortando pela geometria da `root`.

Para casos que os PDFs reais não têm (grupos longos de órfãs, órfãs sem número, etiqueta sem número), forjar o `info`, simular o `_numero_no_cabecalho` numa página, ou construir um PDF de teste com o pypdf.
