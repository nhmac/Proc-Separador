# Plano — limite de 100 folhas de inserção por trabalho (versão web 1.3)

## Contexto

Teste do utilizador no driver (2026-10-01): no campo **Inserir**, `1-100` é aceite; com `1-101` o botão **Adicionar** fica cinzento. Ou seja, há um teto de **100 folhas de inserção**, e o driver **recusa** (não corta em silêncio).

Hoje a app só avisa acima de 100 (`LIMITE_INSERCOES_TESTADO`) e entrega na mesma um plano que o driver não aceita (ex.: binder triplicado, 504 páginas, 123 inseridas numa linha).

Decisões do utilizador:
- acima de 100, **partir em vários trabalhos** (vários PDFs carimbados, impressos pela ordem);
- corte **sempre entre encomendas**, com **partes cheias** (ex.: 123 → ~100 + 23);
- **um botão de download por parte**; o guia continua a ser um só ficheiro.

Resultado pretendido: nenhum trabalho gerado pede mais de 100 inserções; a ordem do original mantém-se (invariante 1); nenhuma página se perde (invariante 2); com ≤ 100 inserções tudo fica **byte a byte igual** ao que sai hoje.

### Ponto ainda por confirmar no driver (não bloqueia)

O teste foi com **uma só entrada**. Não distingue "100 no total do trabalho" de "100 por entrada". Partir em partes de ≤ 100 funciona nos dois casos, por isso é o que se implementa. Teste barato para tirar a dúvida: adicionar `1-100` e depois tentar adicionar `101-102`.
- Se for recusado → limite total, a implementação fica como está.
- Se for aceite → o limite é por entrada: bastaria limitar cada linha a 100 folhas e voltar a um só trabalho (alteração pequena, só com pedido do utilizador).

## Ficheiros

- `web/separador.html` — único ficheiro de código alterado (`<script id="logica">`, interface, markup e CSS).
- `CLAUDE.md` do projeto — documentação atualizada.
- `pages/` — só gerado pelo `py build_pages.py`. **Não publicar** sem pedido.
- Python: **sem alterações** (o trabalho único é só da web; as regras de análise e de blocos não mudam).

## Lógica (`<script id="logica">`)

### Constantes (linha ~331)
- `LIMITE_INSERCOES_TESTADO` → **`LIMITE_INSERCOES = 100`**, com o comentário do teste (100 entra, 101 bloqueia o Adicionar). Atualizar o `return` do módulo (linha ~988).
- `LIMITE_CARACTERES` (300) e `dividirLinhas()` ficam iguais.

### Nova `partirTrabalho(info, gavetaInseridas, limite = LIMITE_INSERCOES)`
Devolve `{ cortes: [[inicio, fim), …], repartidas: [encomenda, …] }` (índices base 0, troços seguidos que cobrem `0..n`).
1. Grupos = troços seguidos com a mesma `encomenda` (já com a herança resolvida).
2. Guloso: junta grupos à parte atual enquanto `inseridas da parte + inseridas do grupo ≤ limite`; quando não cabe e a parte não está vazia, fecha a parte **antes** desse grupo.
3. Caso extremo: um grupo sozinho com mais de `limite` inseridas → corta dentro dele, logo antes da folha inserida que passaria o limite, e regista a encomenda em `repartidas` (gera aviso).
4. Verificação antes de devolver (como a de cobertura do `escrever()`): os cortes são contíguos, cobrem todas as páginas uma vez e nenhuma parte passa o limite; senão `throw`.

### `planoImpressao(info)` (linha 621)
- A base continua a ser global: papel maioritário do PDF inteiro, empate A4-Etiqueta. **O mesmo perfil em todas as partes.**
- Acrescenta `partes: [{ n, de, ate, total, contagem, paginasInseridas, linhas, folhasPorLinha }]`:
  - `de`/`ate` = páginas do original (base 1);
  - `paginasInseridas` e `linhas` na **numeração da parte** (1…total), com `intervalos()`, `dividirLinhas()` e `folhasDaLinha()` já existentes.
- `linhas` e `folhasPorLinha` **saem do nível de topo** (com várias partes estariam na numeração do original e seriam perigosas). Ficam no topo: `total`, `contagem`, `base`, `perfilBase`, `gavetaInseridas`, `paginasInseridas` (do original, só para contagens), `semInsercoes`, `continuacoes`, `avisos`.
- Cada continuação ganha `parte` e `paginaNaParte`.
- Avisos: **sai** o de "acima de 100 não foi testado"; **entra** o `ATENÇÃO` da encomenda repartida entre duas partes (caso 3 acima). Os outros dois ficam iguais.

### `pdfCarimbado()` → `pdfsCarimbados(origem, info, nomePdf, partes)` (linha 774)
- Um PDF por parte: `copyPages(origem, [inicio..fim-1])`, carimbo só nas continuações com número (mesmo `carimbar()`).
- Nomes: 1 parte → `nome_carimbado.pdf` (como hoje); N partes → `nome_carimbado_1de2.pdf` (com `zeros()` se N ≥ 10, para a ordem dos nomes ser a de impressão).
- Releitura de cada PDF: folhas = `parte.total`; soma de todas = `origem.getPageCount()` = `info.length`. Qualquer diferença → erro, não sai nada.
- Com 1 parte o caminho é exatamente o de hoje (bytes iguais).

### `guiaImpressaoUnica()` (linha 664)
- Extrair o corpo atual (passos 1–6, CONTINUAÇÕES, PONTOS DE VERIFICAÇÃO) para uma função interna por parte, a trabalhar sobre `info.slice(inicio, fim)` com numeração da parte.
- **1 parte:** texto idêntico ao atual.
- **N partes:**
  - cabeçalho: `Ficheiros a imprimir: N, pela ordem das partes`, a conferência total de hoje e uma linha por parte (`Parte 1: 395 folhas (páginas 1-395 do original) · 100 folhas de inserção`);
  - frase fixa: o driver só aceita 100 folhas de inserção por trabalho; os números do Inserir são **os de cada parte**, não os do original;
  - uma secção `PARTE n de N — <ficheiro> (x folhas)` com os 6 passos (mesma impressora em todas), "confirmar x linhas na lista" com o x **da parte**, as continuações e os pontos de verificação dessa parte (folha na parte + página do original);
  - no fim de cada parte, a junção das pilhas: última folha da parte e encomenda com que começa a parte seguinte;
  - avisos no fim, como hoje.

### `separar()` (linha 808)
Devolve `carimbados: [{ nome, bytes, carimbadas, folhas }]` em vez de `carimbado`. O resto igual.

## Interface

- **Markup (linhas 261–286):** o `.card.plano` estático passa a um contentor `#partes`; os cartões são criados em JS (`cartaoParte()`), reutilizando `el()`, `linhaInserir()` e `copiar()`.
  - 1 parte: cartão igual ao de hoje, botão "Descarregar PDF carimbado" no topo.
  - N partes: o botão do topo esconde-se; cada cartão tem cabeçalho `Parte n de N · x folhas · páginas a–b do original` e o botão **Descarregar parte n**. A nota do topo passa a "Mais de 100 folhas de inserção: o PDF foi partido em N partes. Imprima-as pela ordem, cada uma inteira, seguindo o guia."
- `linhaInserir()` recebe a parte (linhas e `folhasPorLinha` da parte).
- **Conferência independente** (handler do Separar, linha ~1112): `contarFolhas()` em cada parte; cada uma tem de bater com `parte.total` e a soma com o original; senão erro "não imprimir", como hoje. Texto com N partes: `"x.pdf" = 504 folhas | PDFs carimbados: 395 + 109 = 504 folhas ✓`.
- Chip e estado: `OK · 504/504 folhas ✓` igual; estado final "… descarregue as N partes e o guia".
- Sem pop-up novo: partir o PDF é o tratamento normal, não um aviso.
- CSS: só o cabeçalho do cartão de parte e o espaço entre cartões; conferir a 390 px.
- Rodapé: **"Versão web 1.3"** (linha 241), para confirmar no posto que a página nova chegou.

## CLAUDE.md

Atualizar: "A página" (1.3, cartões por parte), "Como a app faz" (`partirTrabalho`, `pdfsCarimbados`, base global), "Preocupação em aberto" (registar o teste de 2026-10-01: 100 aceite, 101 recusado com Adicionar cinzento; pendente o teste por entrada vs total), invariantes 1 e 2 (as partes concatenadas dão o original), "Resultados de referência" (binder triplicado) e os unitários novos em "Como testar".

## Verificação

Tudo no scratchpad, seguindo "Como testar → Web" do CLAUDE.md.

1. **Antes de mexer:** referência de `Logica.separar` nos dois binders (blocos, guias, PDF carimbado e guia único).
2. `py build_pages.py` (sem publicar); testar `pages/index.html` com servidor Node + Brave (`puppeteer-core`, `userDataDir` temporário).
3. **Regressão (≤ 100 inserções):** nos dois binders, ZIP, guia antigo, **guia único e PDF carimbado byte a byte iguais** à referência; `partes.length === 1`.
4. **Unitários com `info` forjado:**
   - 100 inseridas → 1 parte; 101 → 2 partes; 250 → 3 partes;
   - nenhuma parte acima de 100; cortes só em inícios de encomenda; partes contíguas a cobrir tudo;
   - as linhas de cada parte, repostas na numeração do original, dão exatamente as inseridas globais;
   - encomenda com mais de 100 inseridas → corte interno + aviso;
   - os de hoje: linhas ≤ 300, base 1, empate, sem inserções, continuação sem número e fora do sítio.
5. **Binder triplicado** (504 páginas, gerado com o pypdf no scratchpad) → 2 partes. Reler em Python:
   - partes concatenadas = 504 páginas, hash do conteúdo igual ao original em todas as que não são continuações, pela mesma ordem;
   - em cada parte, as páginas do Inserir são exatamente as do papel minoritário (`analisar_paginas()`), e as restantes são do papel base;
   - carimbo só nas continuações (`0 <= top < 20`), igual ao texto do guia.
6. **Interface:** `uploadFile` + Separar com o binder normal e com o triplicado; Copiar em linhas de partes diferentes; download de cada parte e do guia; screenshots a 1280 e 390 px sem scroll horizontal.
7. Publicar (`py build_pages.py --publicar`) só quando o utilizador pedir.
