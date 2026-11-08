#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Separa PDFs de encomendas (Dreambooks/Fotoprix) em blocos prontos para a
hot folder de impressão, mantendo sempre a ordem original das páginas.

REGRA DE DETEÇÃO
  - A4-Normal    -> páginas SEM a etiqueta de envio
  - A4-Etiqueta  -> páginas COM a etiqueta de envio (papel autocolante)
    (a etiqueta é identificada pela imagem grande no canto superior
    direito: logo + código de barras + "Lote")

ORDEM DE IMPRESSÃO
  A pilha impressa tem de sair pela ordem do PDF original. Por isso as
  páginas são cortadas em blocos seguidos: sempre que o tipo de papel muda,
  começa um ficheiro novo. Nada é reordenado.

FOLHAS DE ÍNDICE (ÓRFÃS) E A CONTINUAÇÃO-INDEX
  As folhas de continuação das miniaturas não trazem cabeçalho visível, por
  isso, depois de impressas e separadas da pilha, ficam sem identificação.
  Como vêm sempre a seguir às folhas da sua encomenda, herdam o número da
  última página que o traz e recebem-no carimbado no topo.

  Essas folhas saem todas juntas do fluxo normal e formam um lote próprio, a
  CONTINUAÇÃO-INDEX ('Continuacao-Index_A4-Normal.pdf'), impresso de uma só
  vez em A4-Normal, pela ordem do
  original (que já as agrupa por encomenda). Assim não é preciso andar a
  trocar de papel a cada duas folhas. Uma página com etiqueta de envio
  fica sempre em A4-Etiqueta, mesmo sem número visível: a etiqueta manda.

NOMENCLATURA DE SAÍDA
  O final do nome do ficheiro diz o papel ('A4-Normal' / 'A4-Etiqueta') e
  o prefixo numérico de 2 dígitos garante que a ordem alfabética dos nomes
  é a ordem de impressão. A CONTINUAÇÃO-INDEX começa por letra, logo
  ordena-se sozinho em último:

      01_A4-Normal.pdf
      02_A4-Etiqueta.pdf
      03_A4-Normal.pdf
      ...
      Continuacao-Index_A4-Normal.pdf

USO (linha de comandos)
    python3 separar_gavetas.py entrada.pdf --saida PASTA [--prefixo TEXTO]
    python3 separar_gavetas.py pasta_de_blocos --imprimir

  Nota: invocado sem qualquer opção (ex.: 'python3 separar_gavetas.py
  entrada.pdf') o programa entra no modo interativo descrito a seguir.

USO (.exe compilado, modo arrastar-e-largar)
    Arraste um ou mais ficheiros PDF (ou uma pasta com PDFs) para cima do
    ficheiro .exe. Cada PDF é processado na SUA PRÓPRIA
    subpasta dentro de "hot_folder_amador", criada ao lado do respetivo
    ficheiro original:

        hot_folder_amador/<nome_do_pdf>/01_A4-Normal.pdf

    Assim vários PDFs largados de uma só vez nunca se sobrepõem.
    Um único ficheiro com problemas (não é PDF, está corrompido, etc.)
    não interrompe o processamento dos restantes.
"""

import io
import sys
import os
import re
import argparse
from pypdf import PdfReader, PdfWriter
import pdfplumber


# Ficheiros que este programa gera e que, por isso, pode limpar com segurança
# numa nova execução sobre a mesma pasta de saída. Os nomes antigos
# ('gaveta1' / 'gaveta3') continuam na lista para que pastas geradas por
# versões anteriores também fiquem limpas.
_PADROES_GERADOS = (
    re.compile(r"^(.+_)?\d{2,}_(A4-Normal|A4-Etiqueta|gaveta[13])\.pdf$", re.IGNORECASE),
    re.compile(r"^(.+_)?(Continuacao-Index|indexs)_(A4-Normal|gaveta1)\.pdf$", re.IGNORECASE),
    re.compile(r"^(.+_)?0+_guia_impressao\.txt$", re.IGNORECASE),
    re.compile(r"^\.estado_impressao\.json$", re.IGNORECASE),
    # Restos de uma escrita interrompida (ver _escrever_pdf) ou de uma limpeza
    # interrompida (ver _limpar_saida).
    re.compile(r"^\..+\.(pdf|txt)\.tmp$", re.IGNORECASE),
    re.compile(r"^\..+\.apagar$", re.IGNORECASE),
)

# Nomes que o Windows reserva para dispositivos: não podem ser nome de pasta.
_NOMES_RESERVADOS = {"CON", "PRN", "AUX", "NUL",
                     *(f"COM{n}" for n in range(1, 10)),
                     *(f"LPT{n}" for n in range(1, 10))}

# Nome de cada tipo de papel, tal como aparece nos ficheiros e nos textos.
# Internamente o papel continua a ser identificado por 1 (normal) e 3
# (etiqueta), os números das gavetas da impressora.
PAPEL = {1: "A4-Normal", 3: "A4-Etiqueta"}

# O lote com as folhas de índice chama-se CONTINUAÇÃO-INDEX. O nome do ficheiro
# vai sem acentos, por segurança com a hot folder, e começa por letra de
# propósito: assim ordena-se depois de todos os blocos numerados, que é quando
# deve ser impresso.
ROTULO_CONTINUACAO = "CONTINUAÇÃO-INDEX"
NOME_LOTE_ORFAS = f"Continuacao-Index_{PAPEL[1]}.pdf"

# Número da encomenda tal como aparece no cabeçalho: "3452270_643175".
_RE_NUMERO_ENCOMENDA = re.compile(r"^\d+_\d+$")

# Carimbo do número de encomenda, em pontos. Vai no topo da folha, encostado ao
# bordo superior: é onde o operador olha primeiro. Nas folhas que precisam de
# carimbo há 18,3 pt livres acima do conteúdo, por isso 8 pt de letra dentro de
# uma caixa de 14 pt cabem sem tapar nada. O x=20 alinha com o bordo esquerdo
# onde começam as miniaturas.
_CARIMBO_X = 20
_CARIMBO_TAMANHO = 8
_CARIMBO_ALTURA_CAIXA = 14
_CARIMBO_BASE_DO_TOPO = 11  # distância do bordo superior à linha de base do texto


# --------------------------------------------------------------------------
# Deteção e geração de blocos (lógica original, inalterada)
# --------------------------------------------------------------------------

def detecta_etiqueta(page) -> bool:
    """
    Devolve True se a página tem a imagem da etiqueta de envio
    (bloco grande no canto superior direito: logo + código de barras + Lote).
    """
    for im in page.images:
        if im["top"] < 250 and im["width"] > 100 and im["x0"] > 250:
            return True
    return False


def _numero_no_cabecalho(page):
    """
    Procura o número da encomenda no cabeçalho e diz se ele é mesmo visível.

    Devolve (estado, numero), com estado em:
        "visivel"   -> o número está impresso na folha
        "invisivel" -> o número existe no ficheiro mas está posicionado fora da
                       área da página, logo nunca é impresso nem visto
        "ausente"   -> não há cabeçalho nenhum

    A distinção é o cerne do problema: muitas destas folhas trazem o cabeçalho
    no conteúdo do PDF mas colocado acima do bordo superior (top negativo).
    Quem imprime a folha não vê número nenhum, por isso, para efeitos de
    identificação, elas são tão anónimas como as que não têm cabeçalho de todo.
    """
    def dentro(palavra):
        # Inteira dentro da folha. Só o 'top' não chega: numa página rodada o
        # cabeçalho escondido fica fora pela lateral, não por cima.
        return (palavra["x0"] >= 0 and palavra["x1"] <= page.width
                and palavra["top"] >= 0 and palavra["bottom"] <= page.height)

    numero_invisivel = None
    palavras = page.extract_words()

    for i, palavra in enumerate(palavras):
        if palavra["text"].lower() != "encomenda":
            continue
        # O número é a palavra imediatamente a seguir a "Encomenda".
        if i + 1 >= len(palavras):
            continue
        seguinte = palavras[i + 1]
        if not _RE_NUMERO_ENCOMENDA.match(seguinte["text"]):
            continue
        if dentro(palavra) and dentro(seguinte):
            return "visivel", seguinte["text"]
        numero_invisivel = numero_invisivel or seguinte["text"]

    if numero_invisivel:
        return "invisivel", numero_invisivel
    return "ausente", None


def analisar_paginas(caminho_pdf):
    """
    Lê o PDF uma única vez e devolve, por página, um dicionário com:

        gaveta     -> 3 (A4-Etiqueta) se tem etiqueta de envio, 1 (A4-Normal)
                      caso contrário
        encomenda  -> número da encomenda (ex.: "3452270_643175") ou None
        estado     -> "visivel" | "invisivel" | "ausente" (ver _numero_no_cabecalho)

    Só as páginas com o número visível se identificam sozinhas. As restantes,
    depois de impressas e separadas da pilha, ficam anónimas: as de cabeçalho
    invisível usam o número que elas próprias trazem escondido, e as que não
    têm cabeçalho nenhum herdam o da última página anterior identificada —
    aparecem sempre logo a seguir às folhas da sua encomenda.
    """
    with pdfplumber.open(caminho_pdf) as pdf:
        info = []
        for p in pdf.pages:
            estado, numero = _numero_no_cabecalho(p)
            info.append({
                "gaveta": 3 if detecta_etiqueta(p) else 1,
                "encomenda": numero,
                "estado": estado,
            })

    atual = None
    for pagina in info:
        if pagina["encomenda"]:
            atual = pagina["encomenda"]
        else:
            pagina["encomenda"] = atual
    return info


def e_orfa(pagina):
    """
    Diz se a página é uma folha de índice órfã: sem etiqueta de envio e sem o
    número da encomenda visível. São estas que precisam de carimbo e que vão
    todas juntas para o lote A4-Normal. Uma página com etiqueta fica sempre
    em A4-Etiqueta, mesmo sem número visível.
    """
    return pagina["gaveta"] == 1 and pagina["estado"] != "visivel"


def separar_orfas(info):
    """Devolve (indices_orfas, indices_restantes), ambos pela ordem do original."""
    orfas, restantes = [], []
    for i, pagina in enumerate(info):
        (orfas if e_orfa(pagina) else restantes).append(i)
    return orfas, restantes


def _por_encomenda(info, indices):
    """Agrupa índices de página por encomenda, mantendo as duas ordens de
    aparição: a das encomendas entre si e a das páginas dentro de cada uma."""
    grupos = {}
    for i in indices:
        grupos.setdefault(info[i]["encomenda"], []).append(i)
    return grupos


def ordem_das_encomendas(info, principais, orfas):
    """
    Sequência das encomendas tal como saem da impressora: primeiro as da pilha
    principal, pela ordem do original, e a seguir as que só têm folhas de
    índice. É por esta ordem que as folhas de índice saem no lote, para que
    juntá-las à pilha principal seja uma passagem linear.
    """
    ordem = []
    for i in list(principais) + list(orfas):
        encomenda = info[i]["encomenda"]
        if encomenda and encomenda not in ordem:
            ordem.append(encomenda)
    return ordem


def agrupar_orfas_por_encomenda(info, orfas, ordem=()):
    """
    Ordena as folhas órfãs de modo a que as da mesma encomenda saiam sempre
    juntas no lote, mesmo que no original apareçam separadas por folhas de
    outra encomenda, e pela mesma sequência de encomendas da pilha principal
    ('ordem') — assim juntar as duas pilhas é uma passagem linear, não uma
    procura.

    As folhas sem número de onde herdar ficam todas no mesmo grupo (chave
    None), no fim, e são assinaladas à parte no guia.
    """
    grupos = _por_encomenda(info, orfas)
    seguidas = [n for n in ordem if n in grupos]
    restantes = [n for n in grupos if n not in seguidas]
    return [i for n in seguidas + restantes for i in grupos[n]]


def agrupar_blocos(info, indices=None):
    """
    Agrupa páginas contíguas do mesmo papel, respeitando a ordem original.

    'indices' limita o agrupamento a um subconjunto de páginas. Duas páginas da
    mesmo papel que fiquem lado a lado depois de retirado o que estava pelo
    meio entram no mesmo bloco — é assim que os blocos se juntam quando as
    folhas de índice saem para o seu próprio lote.
    """
    if indices is None:
        indices = range(len(info))

    blocos = []
    for i in indices:
        gaveta = info[i]["gaveta"]
        if blocos and blocos[-1][0] == gaveta:
            blocos[-1][1].append(i)
        else:
            blocos.append([gaveta, [i]])
    return blocos


def _descricao_paginas(numeros):
    """
    Lista páginas do original de forma compacta, juntando as seguidas:
    [2] -> "2";  [3, 4] -> "3-4";  [2, 5, 10, 11] -> "2, 5, 10-11".
    """
    intervalos = []
    inicio = anterior = numeros[0]
    for n in numeros[1:]:
        if n == anterior + 1:
            anterior = n
            continue
        intervalos.append((inicio, anterior))
        inicio = anterior = n
    intervalos.append((inicio, anterior))

    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in intervalos)


def _frase_paginas(numeros):
    """A mesma lista, já com 'página'/'páginas' à frente, para texto corrido."""
    return f"{'página' if len(numeros) == 1 else 'páginas'} {_descricao_paginas(numeros)}"


def agrupar_por_gaveta(caminho_pdf):
    """Lê o PDF e devolve lista de (gaveta, [indices_0based]) respeitando a ordem original."""
    return agrupar_blocos(analisar_paginas(caminho_pdf))


def _sobreposicao_numero(texto, caixa):
    """
    Constrói em memória um PDF de uma página, com a 'caixa' dada (esquerda,
    baixo, direita, topo: a área visível da página onde vai ser fundido), com
    'texto' no topo sobre um retângulo branco, e devolve essa página pronta a
    fundir.

    As coordenadas partem da caixa e não de (0, 0): há PDFs cuja página não
    começa na origem, e aí um carimbo desenhado a 'altura - 11' ficava fora
    da folha.

    É escrito à mão porque o pypdf não desenha texto e não vale a pena arrastar
    uma biblioteca de geração de PDF só para carimbar um número. O texto é
    sempre do tipo "3452270_643175", logo não precisa de escapes.
    """
    esquerda, baixo, direita, topo = caixa
    largura_texto = len(texto) * _CARIMBO_TAMANHO * 0.6
    x = esquerda + _CARIMBO_X
    caixa_y = topo - _CARIMBO_ALTURA_CAIXA
    base_y = topo - _CARIMBO_BASE_DO_TOPO
    conteudo = (
        f"q\n1 1 1 rg\n"
        f"{x - 4:.1f} {caixa_y:.1f} {largura_texto + 8:.1f} {_CARIMBO_ALTURA_CAIXA} re f\n"
        f"0 0 0 rg\n"
        f"BT /F1 {_CARIMBO_TAMANHO} Tf {x:.1f} {base_y:.1f} Td ({texto}) Tj ET\nQ\n"
    ).encode("latin-1")

    objetos = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        (f"<</Type/Page/Parent 2 0 R"
         f"/MediaBox[{esquerda:.2f} {baixo:.2f} {direita:.2f} {topo:.2f}]"
         f"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>").encode("latin-1"),
        b"<</Length " + str(len(conteudo)).encode() + b">>\nstream\n" + conteudo + b"endstream",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold>>",
    ]

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    posicoes = []
    for numero, corpo in enumerate(objetos, start=1):
        posicoes.append(buffer.tell())
        buffer.write(f"{numero} 0 obj\n".encode() + corpo + b"\nendobj\n")

    inicio_xref = buffer.tell()
    buffer.write(f"xref\n0 {len(objetos) + 1}\n".encode())
    buffer.write(b"0000000000 65535 f \n")
    for posicao in posicoes:
        buffer.write(f"{posicao:010d} 00000 n \n".encode())
    buffer.write(
        f"trailer\n<</Size {len(objetos) + 1}/Root 1 0 R>>\n"
        f"startxref\n{inicio_xref}\n%%EOF\n".encode()
    )
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def ficheiros_gerados_em(pasta):
    """
    Nomes dos ficheiros de 'pasta' que este programa gerou (blocos, lote,
    guia, estado de impressão e restos temporários — ver _PADROES_GERADOS).
    Tudo o resto é do utilizador e nunca se apaga.
    """
    if not os.path.isdir(pasta):
        return []
    return sorted(
        nome for nome in os.listdir(pasta)
        if os.path.isfile(os.path.join(pasta, nome))
        and any(p.match(nome) for p in _PADROES_GERADOS)
    )


def _limpar_saida(pasta, log=print):
    """
    Remove da pasta de saída os ficheiros gerados por uma execução anterior.
    Qualquer outro ficheiro ou subpasta fica intacto, para nunca apagar
    trabalho do utilizador.

    É tudo ou nada. Um ficheiro aberto noutro programa (o Acrobat, por
    exemplo) não se deixa apagar; se ficasse para trás, misturava-se com os
    blocos novos e era impresso como se fosse deste PDF. Por isso primeiro
    tiram-se todos do caminho com um nome temporário; se algum falhar, os
    outros voltam ao nome que tinham e nada foi mexido.
    """
    afastados = []
    for nome in ficheiros_gerados_em(pasta):
        caminho = os.path.join(pasta, nome)
        afastado = os.path.join(pasta, f".{nome}.apagar")
        try:
            os.replace(caminho, afastado)
        except OSError as e:
            for original, tirado in reversed(afastados):
                try:
                    os.replace(tirado, original)
                except OSError:
                    pass
            raise RuntimeError(
                f"Não consegui apagar '{nome}', de uma separação anterior: está aberto "
                "noutro programa? Feche-o e separe outra vez. Nada foi escrito."
            ) from e
        afastados.append((caminho, afastado))

    for _, afastado in afastados:
        try:
            os.remove(afastado)
        except OSError:
            pass  # já não se confunde com um bloco; sai na próxima limpeza

    if afastados:
        log(f"Removidos {len(afastados)} ficheiro(s) de uma execucao anterior.")
    return len(afastados)


def _temporario(caminho):
    """Nome temporário de um ficheiro de saída: começa por ponto e não acaba em
    .pdf, por isso nenhuma hot folder o reconhece."""
    return os.path.join(os.path.dirname(caminho), f".{os.path.basename(caminho)}.tmp")


def _escrever_pdf(writer, caminho):
    """
    Escreve o PDF só com o nome temporário. O nome definitivo é dado depois,
    a todos os ficheiros de uma vez, por _publicar(), quando já estão todos
    escritos e verificados.

    Uma hot folder que vigie a pasta pode apanhar um ficheiro ainda a meio da
    escrita (os blocos chegam a ter dezenas de MB), rejeitá-lo e saltar o bloco
    inteiro — o que, na pilha impressa, aparece como uma série de folhas
    seguidas que simplesmente faltam. E se a separação falhar a meio, os
    blocos já escritos não podem ficar à vista como se estivesse tudo bem.
    """
    with open(_temporario(caminho), "wb") as f:
        writer.write(f)


def _publicar(caminhos):
    """Dá o nome definitivo aos ficheiros, pela ordem dada. Cada mudança de
    nome é atómica."""
    for caminho in caminhos:
        os.replace(_temporario(caminho), caminho)


def _desfazer(caminhos):
    """
    Apaga o que esta execução escreveu, temporário ou já publicado. Só é
    seguro porque _limpar_saida() já tirou da pasta tudo o que era de
    execuções anteriores. Devolve os nomes que não conseguiu apagar.
    """
    restos = []
    for caminho in caminhos:
        for c in (_temporario(caminho), caminho):
            try:
                if os.path.exists(c):
                    os.remove(c)
            except OSError:
                restos.append(os.path.basename(c))
    return restos


def _verificar_formato(info, reader):
    """
    Pára antes de escrever quando o PDF não tem a forma que a deteção conhece.
    Nestes casos o papel ou o carimbo podiam sair errados sem ninguém dar por
    isso, por isso é preferível não separar e dizer porquê.
    """
    if not info:
        raise RuntimeError("O PDF não tem páginas.")

    rodadas = [i + 1 for i, p in enumerate(reader.pages) if p.rotation % 360]
    if rodadas:
        raise RuntimeError(
            f"Há páginas rodadas no PDF ({_frase_paginas(rodadas)}). A deteção da etiqueta "
            "e do número de encomenda não é fiável em páginas rodadas; nada foi escrito."
        )

    if not any(p["estado"] == "visivel" for p in info):
        raise RuntimeError(
            "Não encontrei nenhum número de encomenda visível ('Encomenda 3452270_643175') "
            "em todo o PDF. O formato das folhas pode ter mudado; nada foi escrito."
        )

    sem_numero = [i + 1 for i, p in enumerate(info) if p["gaveta"] == 3 and p["estado"] != "visivel"]
    if sem_numero:
        raise RuntimeError(
            f"Há folhas com etiqueta de envio sem o número de encomenda visível "
            f"({_frase_paginas(sem_numero)}). Cada etiqueta começa uma encomenda, e as "
            "folhas de índice seguintes ficariam com o número da anterior; nada foi escrito."
        )


def _verificar_saida(ficheiros_gerados, n_paginas):
    """
    Relê cada ficheiro escrito e confirma que tem as folhas que devia e que,
    somados, dão o total do original. Se algo não bater, pára com erro: é
    preferível não imprimir nada a imprimir uma pilha com folhas em falta.
    """
    total = 0
    for bloco in ficheiros_gerados:
        n = len(PdfReader(bloco["caminho"]).pages)
        if n != bloco["folhas"]:
            raise RuntimeError(
                f"{bloco['nome']} ficou com {n} folhas em vez de {bloco['folhas']}. "
                "Separe o PDF outra vez antes de imprimir."
            )
        total += n
    if total != n_paginas:
        raise RuntimeError(
            f"Os ficheiros gerados somam {total} folhas, mas o original tem "
            f"{n_paginas}. Separe o PDF outra vez antes de imprimir."
        )


def gerar_blocos(entrada, pasta_saida, prefixo="", log=print, progresso=None, avisos=None):
    """
    Escreve os blocos e o guia de impressão em 'pasta_saida' e devolve a lista
    de blocos gerados, um dicionário por bloco com as chaves: caminho, nome,
    gaveta, pag_ini, pag_fim, folhas, paginas_txt, orfas.

    Os blocos seguem a ordem do original: começa um ficheiro novo sempre que o
    papel muda, e nenhuma página é reordenada.

    As folhas de índice (sem número visível) saem da sequência normal e formam
    o último ficheiro, a CONTINUAÇÃO-INDEX, para serem impressas de uma só
    vez em A4-Normal. Os blocos restantes são calculados já sem elas, por isso
    duas páginas do mesmo papel que ficassem separadas por uma folha de índice
    passam a sair no mesmo ficheiro.

    'log' recebe cada linha de texto (por omissão vai para a consola) e
    'progresso', se for dado, é chamado como progresso(n, total) a cada bloco
    escrito. Servem para o GUI acompanhar o trabalho sem depender do stdout.
    'avisos', se for uma lista, recebe os avisos que o operador tem de ver
    (vão também para o guia).

    É tudo ou nada: os ficheiros só recebem o nome definitivo depois de todos
    escritos e verificados, e se alguma coisa falhar pelo caminho a pasta
    fica sem ficheiros gerados.
    """
    info = analisar_paginas(entrada)
    reader = PdfReader(entrada)
    if len(reader.pages) != len(info):
        raise RuntimeError("O pdfplumber e o pypdf não leem o mesmo número de páginas; "
                           "nada foi escrito.")
    _verificar_formato(info, reader)
    orfas, restantes = separar_orfas(info)
    ordem = ordem_das_encomendas(info, restantes, orfas)
    orfas = agrupar_orfas_por_encomenda(info, orfas, ordem)
    blocos = agrupar_blocos(info, restantes)

    # Cada página do original tem de estar num e num só ficheiro. Verificado
    # antes de escrever o que quer que seja.
    usadas = sorted([i for _, indices in blocos for i in indices] + list(orfas))
    if usadas != list(range(len(info))):
        raise RuntimeError(
            "A separação não cobre todas as páginas do original exatamente uma vez; "
            "nada foi escrito."
        )

    # Só agora, com o PDF validado, se mexe na pasta de saída.
    os.makedirs(pasta_saida, exist_ok=True)
    _limpar_saida(pasta_saida, log=log)

    ficheiros_gerados = []
    escritos = []  # caminhos definitivos desta execução, pela ordem de publicação
    total = len(blocos) + (1 if orfas else 0)

    # Dois dígitos chegam quase sempre, mas com mais de 99 blocos "100_" ficaria
    # ordenado antes de "11_" e a hot folder imprimia fora de ordem.
    largura = max(2, len(str(total)))

    n_etiqueta = sum(1 for i in restantes if info[i]["gaveta"] == 3)
    n_normal = len(info) - n_etiqueta

    prefixo_norm = f"{prefixo}_" if prefixo else ""
    resumo = [f"Guia de impressão — {os.path.basename(entrada)}",
              f"Total de páginas: {len(reader.pages)}",
              f"Ficheiros a imprimir: {total}, pela ordem dos nomes",
              f"Conferência final — a pilha impressa tem de ter {len(info)} folhas: "
              f"{n_etiqueta} {PAPEL[3]} + {n_normal} {PAPEL[1]}"
              + (f" (das quais {len(orfas)} em {ROTULO_CONTINUACAO})" if orfas else ""),
              ""]

    def registar(nome, caminho, gaveta, indices, sao_orfas):
        """Junta o bloco à lista devolvida e devolve a frase com as páginas."""
        # No lote de índices as folhas da mesma encomenda juntam-se, por isso
        # a ordem pode não ser a do original; as páginas são descritas por
        # ordem crescente, porque aqui só interessa *quais* são.
        numeros = sorted(i + 1 for i in indices)
        ficheiros_gerados.append({
            "caminho": caminho,
            "nome": nome,
            "gaveta": gaveta,
            "pag_ini": numeros[0],
            "pag_fim": numeros[-1],
            "folhas": len(indices),
            "paginas_txt": _descricao_paginas(numeros),   # "2, 5, 10-11"
            "paginas_frase": _frase_paginas(numeros),     # "páginas 2, 5, 10-11"
            "encomendas": list(_por_encomenda(info, indices)),
            "orfas": sao_orfas,
        })
        return ficheiros_gerados[-1]["paginas_frase"]

    def conferencia(indices):
        """Lista, pela ordem por que saem da impressora, as encomendas de um
        bloco: número de encomenda e quantas folhas traz."""
        linhas = []
        for encomenda, paginas in _por_encomenda(info, indices).items():
            etiqueta = encomenda or "SEM NÚMERO"
            fls = "1 folha" if len(paginas) == 1 else f"{len(paginas)} folhas"
            linhas.append(f"    {etiqueta:18s} {fls}"
                          f"   ({_frase_paginas(sorted(p + 1 for p in paginas))} do original)")
        return linhas

    try:
        # ------------------------------------------------ blocos normais
        for n, (gaveta, indices) in enumerate(blocos, start=1):
            writer = PdfWriter()
            for idx in indices:
                writer.add_page(reader.pages[idx])

            nome = f"{prefixo_norm}{n:0{largura}d}_{PAPEL[gaveta]}.pdf"
            caminho = os.path.join(pasta_saida, nome)
            escritos.append(caminho)  # antes de escrever: um temporário a meio também sai
            _escrever_pdf(writer, caminho)

            frase = registar(nome, caminho, gaveta, indices, False)
            encomendas = ficheiros_gerados[-1]["encomendas"]
            linha = (f"{n:0{largura}d}. {nome}  ->  Papel {PAPEL[gaveta]}  ->  "
                     f"{len(indices)} folhas, {len(encomendas)} encomendas")
            resumo.append(linha)
            resumo.append(f"    ({frase} do original)")
            resumo.extend(conferencia(indices))
            resumo.append("")
            log(linha)

            if progresso:
                progresso(n, total)

        # ------------------------------------------------ lote das folhas de índice
        sem_encomenda = []
        if orfas:
            writer = PdfWriter()
            for idx in orfas:
                pagina = reader.pages[idx]
                numero = info[idx]["encomenda"]
                if numero:
                    # A folha não mostra o número: depois de impressa e separada da
                    # pilha não há como saber a que encomenda pertence. Leva
                    # carimbado o código do cabeçalho, encomenda_item id.
                    visivel = pagina.cropbox
                    pagina.merge_page(_sobreposicao_numero(
                        numero,
                        (float(visivel.left), float(visivel.bottom),
                         float(visivel.right), float(visivel.top)),
                    ))
                else:
                    sem_encomenda.append(idx + 1)
                writer.add_page(pagina)

            nome = f"{prefixo_norm}{NOME_LOTE_ORFAS}"
            caminho = os.path.join(pasta_saida, nome)
            escritos.append(caminho)
            _escrever_pdf(writer, caminho)

            frase = registar(nome, caminho, 1, orfas, True)
            encomendas = ficheiros_gerados[-1]["encomendas"]
            linha = (f"{len(blocos) + 1:0{largura}d}. {nome}  ->  Papel {PAPEL[1]} — "
                     f"{ROTULO_CONTINUACAO}  ->  {len(orfas)} folhas, "
                     f"{len(encomendas)} encomendas")
            resumo.append(linha)
            resumo.append(f"    ({frase} do original)")
            resumo.append("    Carimbadas no topo com o número de encomenda, pela mesma "
                          "sequência da pilha principal:")
            resumo.extend(conferencia(orfas))
            resumo.append("")
            log(linha)

            if progresso:
                progresso(total, total)

            log(f"\n{len(orfas)} folha(s) de {ROTULO_CONTINUACAO} carimbadas e reunidas em {nome} "
                f"({len(encomendas)} encomenda(s)).")

        if sem_encomenda:
            aviso = ("ATENÇÃO: páginas sem cabeçalho e sem encomenda anterior de onde herdar "
                     f"o número (ficaram por identificar): {', '.join(map(str, sem_encomenda))}")
            resumo.append("")
            resumo.append(aviso)
            log(f"\n{aviso}")
            if avisos is not None:
                avisos.append(aviso)

        # Verificam-se os temporários: ainda nada está à vista.
        _verificar_saida([dict(b, caminho=_temporario(b["caminho"])) for b in ficheiros_gerados],
                         len(reader.pages))
        log(f"Verificado: os {len(ficheiros_gerados)} ficheiros somam as {len(reader.pages)} "
            "folhas do original.")

        resumo_path = os.path.join(pasta_saida, f"{prefixo_norm}00_guia_impressao.txt")
        escritos.append(resumo_path)
        with open(_temporario(resumo_path), "w", encoding="utf-8") as f:
            f.write("\n".join(resumo))

        _publicar(escritos)
    except Exception as e:
        # Nada fica à vista a meio: um bloco solto na pasta era impresso como
        # se a separação estivesse completa.
        restos = _desfazer(escritos)
        if restos:
            raise RuntimeError(
                f"{e} — ATENÇÃO: não consegui apagar {', '.join(restos)}; "
                "apague-os à mão antes de imprimir."
            ) from e
        raise

    log(f"\n{len(ficheiros_gerados)} ficheiro(s) gerados em: {pasta_saida}")
    log("Copie/largue todos os ficheiros na hot folder de uma vez — "
        "a ordem alfabética dos nomes já garante a sequência certa de impressão.")
    return ficheiros_gerados


# --------------------------------------------------------------------------
# Impressão guiada
# --------------------------------------------------------------------------

def abrir_pdf(caminho):
    """Abre o PDF com o leitor predefinido do sistema (Acrobat Reader no Windows, se for o predefinido)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", caminho])
        else:
            import subprocess
            subprocess.run(["xdg-open", caminho])
        return True
    except Exception as e:
        print(f"Não consegui abrir o ficheiro automaticamente ({e}).")
        print(f"Abra manualmente: {caminho}")
        return False


def impressao_guiada(pasta_blocos):
    """
    Percorre os blocos gerados, pela ordem certa, abrindo cada PDF um a um.
    Antes de cada um, mostra claramente o papel a selecionar. Só avança
    para o seguinte depois do utilizador confirmar com Enter, para nunca
    haver risco de avançar cedo demais ou trocar a ordem.
    """
    if not os.path.isdir(pasta_blocos):
        print(f"ERRO: pasta '{pasta_blocos}' não encontrada.")
        return

    ficheiros = sorted(
        f for f in os.listdir(pasta_blocos)
        if f.lower().endswith(".pdf")
    )

    if not ficheiros:
        print(f"Não encontrei nenhum PDF em '{pasta_blocos}'.")
        return

    total = len(ficheiros)
    print("\n" + "=" * 60)
    print(" IMPRESSÃO GUIADA — siga a ordem indicada")
    print("=" * 60)
    print(f"Total de blocos a imprimir: {total}\n")

    for i, nome in enumerate(ficheiros, start=1):
        caminho = os.path.join(pasta_blocos, nome)
        etiqueta = any(t in nome.lower() for t in ("a4-etiqueta", "gaveta3"))
        papel = PAPEL[3] if etiqueta else PAPEL[1]

        print("-" * 60)
        print(f"BLOCO {i} de {total}: {nome}")
        print(f">>> SELECIONE O PAPEL {papel.upper()} <<<")
        print("-" * 60)

        resposta = _pergunta(
            "Prima Enter para abrir este PDF (ou 'p' + Enter para parar aqui)... "
        ).lower()

        if resposta == "p":
            print("\nImpressão guiada interrompida pelo utilizador.")
            return

        abrir_pdf(caminho)

        try:
            resposta = input(
                "\nDepois de imprimir e fechar o PDF, prima Enter para avançar, "
                "ou 'p' + Enter para parar aqui... "
            ).strip().lower()
        except (EOFError, OSError):
            break

        if resposta == "p":
            print("\nImpressão guiada interrompida pelo utilizador.")
            return

    print("\n" + "=" * 60)
    print(" Impressão guiada concluída.")
    print("=" * 60)


def _pausa_final():
    """Espera por Enter antes de fechar a janela; nunca rebenta se não houver terminal interativo."""
    try:
        input("\nPrima Enter para fechar...")
    except (EOFError, OSError):
        pass


# --------------------------------------------------------------------------
# Modo arrastar-e-largar (.exe)
# --------------------------------------------------------------------------

def _pergunta(mensagem, default=""):
    try:
        resposta = input(mensagem).strip()
        return resposta if resposta else default
    except (EOFError, OSError):
        return default


def _nome_seguro(texto, default="pdf"):
    """
    Normaliza um texto para poder ser usado como nome de pasta/ficheiro em
    Windows: substitui caracteres proibidos, colapsa espaços, corta espaços
    e pontos nas pontas e limita o comprimento.
    """
    limpo = re.sub(r'[\\/:*?"<>|]+', "_", texto or "")
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    limpo = limpo[:60].strip(" .")
    if limpo.split(".")[0].upper() in _NOMES_RESERVADOS:
        limpo = f"_{limpo}"
    return limpo if limpo else default


def _recolher_pdfs(caminhos):
    """
    A partir dos argumentos recebidos (podem ser ficheiros e/ou pastas),
    devolve a lista de PDFs a processar e a lista de entradas inválidas
    (para reportar sem travar o programa).
    """
    pdfs = []
    invalidos = []

    for caminho in caminhos:
        if os.path.isdir(caminho):
            encontrados = sorted(
                os.path.join(caminho, f)
                for f in os.listdir(caminho)
                if f.lower().endswith(".pdf")
            )
            if encontrados:
                pdfs.extend(encontrados)
            else:
                invalidos.append((caminho, "pasta sem ficheiros .pdf"))
        elif os.path.isfile(caminho):
            if caminho.lower().endswith(".pdf"):
                pdfs.append(caminho)
            else:
                invalidos.append((caminho, "não é um ficheiro .pdf"))
        else:
            invalidos.append((caminho, "não encontrado"))

    return pdfs, invalidos


def _pasta_saida_para(pdf, usadas, raiz=None):
    """
    Devolve a subpasta de saída dedicada a este PDF, dentro de 'raiz' (a hot
    folder escolhida na janela) ou, sem ela, de 'hot_folder_amador' ao lado do
    PDF. Garante que dois PDFs nunca partilham a mesma pasta — o que faria os
    blocos sobreporem-se uns aos outros.
    """
    if raiz is None:
        raiz = os.path.join(os.path.dirname(os.path.abspath(pdf)), "hot_folder_amador")
    base = _nome_seguro(os.path.splitext(os.path.basename(pdf))[0])

    pasta = os.path.join(raiz, base)
    n = 2
    while pasta.lower() in usadas:
        pasta = os.path.join(raiz, f"{base}_{n}")
        n += 1

    usadas.add(pasta.lower())
    return pasta


def modo_drag_and_drop(caminhos):
    """
    Modo usado quando o programa é compilado em .exe. Aceita um ou vários
    PDFs e/ou pastas arrastados de uma só vez. Cada PDF gera a sua própria
    subpasta dentro de "hot_folder_amador", ao lado do ficheiro original.
    Um ficheiro inválido é reportado mas não interrompe o processamento
    dos restantes.
    """
    print("=" * 60)
    print(" Processamento · Separador de Papel")
    print("=" * 60)

    pdfs, invalidos = _recolher_pdfs(caminhos)

    if invalidos:
        print("\nAlguns itens não foram processados:")
        for caminho, motivo in invalidos:
            print(f"  - {caminho}  ({motivo})")

    if not pdfs:
        print("\nNão encontrei nenhum PDF válido para processar.")
        print("Arraste um ou mais ficheiros PDF (ou uma pasta com PDFs) "
              "para cima do programa.")
        _pausa_final()
        sys.exit(1)

    print(f"\n{len(pdfs)} PDF(s) recebido(s):")
    for p in pdfs:
        print(f"  - {p}")

    prefixo = _nome_seguro(
        _pergunta(
            "\nPrefixo para os nomes dos ficheiros (opcional, Enter para ignorar): "
        ),
        default="",
    )

    usadas = set()
    resultados = []  # (pdf, pasta_saida, sucesso, erro)

    for pdf in pdfs:
        pasta_saida = _pasta_saida_para(pdf, usadas)

        print("\n" + "-" * 60)
        print(f"A processar: {pdf}")
        print(f"Saída: {pasta_saida}")
        print("-" * 60)

        try:
            gerar_blocos(pdf, pasta_saida, prefixo)
            resultados.append((pdf, pasta_saida, True, None))
        except Exception as e:
            print(f"\nERRO a processar este ficheiro: {e}")
            print("A avançar para o próximo, se houver.")
            resultados.append((pdf, pasta_saida, False, str(e)))

    # Resumo final
    ok = [r for r in resultados if r[2]]
    falhas = [r for r in resultados if not r[2]]

    print("\n" + "=" * 60)
    print(" RESUMO")
    print("=" * 60)
    print(f"Processados com sucesso: {len(ok)} de {len(resultados)}")
    for pdf, pasta_saida, _, _ in ok:
        print(f"  OK    {os.path.basename(pdf)}  ->  {pasta_saida}")
    if falhas:
        print(f"\nFalharam: {len(falhas)}")
        for pdf, _, _, erro in falhas:
            print(f"  ERRO  {os.path.basename(pdf)}  ({erro})")

    if ok:
        resposta = _pergunta(
            "\nQuer iniciar agora a impressão guiada, bloco a bloco, "
            "para cada PDF processado? (S/N): "
        ).lower()
        if resposta.startswith("s"):
            for pdf, pasta_saida, _, _ in ok:
                print(f"\n>>> Impressão guiada para: {os.path.basename(pdf)} <<<")
                impressao_guiada(pasta_saida)
        else:
            print("\nOk, pode abrir os ficheiros manualmente quando quiser, "
                  "pela ordem dos nomes (01, 02, 03, ...).")

    _pausa_final()


# --------------------------------------------------------------------------
# Entrada principal
# --------------------------------------------------------------------------

def main():
    # Modo .exe / drag-and-drop: o Explorador do Windows passa apenas
    # caminhos, nunca opções. Se não vier nenhuma opção, é este o modo.
    args_sem_flags = sys.argv[1:]
    if args_sem_flags and all(not a.startswith("-") for a in args_sem_flags):
        modo_drag_and_drop(args_sem_flags)
        return

    parser = argparse.ArgumentParser(description="Separa PDF em blocos por tipo de papel (A4-Normal / A4-Etiqueta), pela ordem do original.")
    parser.add_argument("entrada", help="PDF de entrada, ou pasta de blocos já gerada se usar --imprimir")
    parser.add_argument("--saida", default="hot_folder_amador", help="Pasta de saída / hot folder (por omissão: hot_folder_amador)")
    parser.add_argument("--prefixo", default="", help="Prefixo a colocar antes do número de cada bloco (ex: nome do dia/lote)")
    parser.add_argument("--imprimir", action="store_true", help="Em vez de gerar blocos, inicia a impressão guiada sobre uma pasta de blocos já existente (passar a pasta em 'entrada')")
    args = parser.parse_args()

    if args.imprimir:
        impressao_guiada(args.entrada)
        return

    gerar_blocos(args.entrada, args.saida, _nome_seguro(args.prefixo, default=""))


if __name__ == "__main__":
    main()
