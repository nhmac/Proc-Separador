#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface gráfica do Processamento · Separador de Papel.

Toda a lógica (deteção da etiqueta, agrupamento em blocos, escrita dos
ficheiros) vive em separar_gavetas.py — este módulo só orquestra e mostra.
O aspeto é o da linha de apps "Processamento" (processamento_ui.py).

USO
    python3 separar_gavetas_gui.py [ficheiro.pdf]

Trabalha-se um PDF de cada vez: escolher -> separar -> imprimir -> apagar.
O PDF passado como argumento (ou largado em cima do .exe compilado) aparece
já escolhido.
"""

import os
import sys
import json
import queue
import threading
import traceback
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from pypdf import PdfReader

import separar_gavetas as motor
import processamento_ui as ui
from processamento_ui import COR


NOME_APP = "Processamento · Separador de Papel"
# Pasta da configuração em %APPDATA%. Não acompanha o NOME_APP: mudar o nome
# visível não pode fazer perder a hot folder já escolhida.
PASTA_CONFIG = "Separador de Papel"
# Nome anterior da aplicação: a configuração gravada com ele continua a ser
# lida, para não voltar a pedir a hot folder depois da mudança de nome.
NOME_APP_ANTIGO = "Separador de gavetas"

# Cores por papel (fundo, texto, borda). O A4-Etiqueta (autocolante) é o que
# custa dinheiro se for trocado, por isso é o que leva o destaque mais forte.
CORES_PAPEL = {
    3: (COR["etiqueta_fundo"], COR["etiqueta_texto"], COR["etiqueta_borda"]),
    1: (COR["accent_suave"], COR["accent_texto"], COR["accent_suave"]),
}
CORES_CONCLUIDO = (COR["sucesso_suave"], COR["sucesso_texto"], COR["sucesso"])


def descricao_gaveta(bloco):
    """Texto grande do painel: o que o operador tem de ler antes de imprimir."""
    papel = motor.PAPEL[bloco["gaveta"]].upper()
    if bloco.get("orfas"):
        return f"{papel} · {motor.ROTULO_CONTINUACAO}"
    return papel


def contar_folhas(pdf):
    """Folhas do PDF original, lidas aqui e não pelo motor: é esta contagem
    independente que confirma que a separação não perdeu nada. None se falhar."""
    try:
        return len(PdfReader(pdf).pages)
    except Exception:
        return None


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


# --------------------------------------------------------------------------
# Configuração (a hot folder escolhida), guardada entre sessões
# --------------------------------------------------------------------------

def caminho_config(nome=PASTA_CONFIG):
    """%APPDATA%\\<nome>\\config.json; sem APPDATA, ao lado do programa."""
    base = os.environ.get("APPDATA")
    if base:
        return os.path.join(base, nome, "config.json")
    programa = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    return os.path.join(os.path.dirname(programa), "config.json")


def ler_config():
    """Devolve o dicionário da configuração. Nunca levanta erro. Enquanto não
    houver configuração gravada com o nome atual, usa a do nome antigo; a
    próxima gravação já vai para o nome atual."""
    for caminho in (caminho_config(), caminho_config(NOME_APP_ANTIGO)):
        try:
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
        except (OSError, ValueError):
            continue
    return {}


def gravar_config(dados):
    """Grava a configuração. Falhar aqui nunca pode parar a aplicação."""
    try:
        caminho = caminho_config()
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# --------------------------------------------------------------------------
# Aplicação
# --------------------------------------------------------------------------

class Aplicacao:

    def __init__(self, root, caminhos_iniciais=()):
        self.root = root
        self.fila = queue.Queue()
        self.processando = False

        # Um PDF de cada vez: escolher -> separar -> imprimir -> apagar.
        self.pdf = None         # caminho absoluto do PDF escolhido
        self.trabalho = None    # {pdf, pasta, blocos, impressos, folhas_original, folhas_ficheiros}
        self.idx_bloco = 0
        self.abertos = set()    # blocos abertos nesta separação (caminho normalizado)
        self.concluido = False  # painel em modo "CONCLUÍDO" até se navegar
        self.erro = None        # motivo, se a última separação falhou
        self.avisos = []        # avisos do motor que o operador tem de ver
        self.hot_folder = ler_config().get("hot_folder") or None
        self.linhas = []        # widgets de cada bloco na lista, pela ordem dos blocos
        self._geracao = 0       # muda a cada lista nova: pára a criação de linhas de uma lista antiga

        ui.configurar_janela(root, NOME_APP, geometria="1120x720", minimo=(960, 600))
        self.f = ui.criar_fontes(root)
        # Com o pythonw ou o .exe não há consola: um erro num callback tem de
        # aparecer, senão a janela fica parada sem se perceber porquê.
        root.report_callback_exception = self._erro_inesperado
        root.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        self._construir_sidebar()
        self._construir_area_imprimir()

        if caminhos_iniciais:
            self._receber_argumentos(list(caminhos_iniciais))

    # -------------------------------------------------------------- sidebar

    def _construir_sidebar(self):
        s = ui.sidebar(self.root)
        ui.cabecalho_sidebar(s, self.f, "Separador de Papel", "Blocos por tipo de papel")

        ui.label_secao(s, self.f, "PDF").pack(anchor="w", padx=24, pady=(32, 8))
        self.btn_escolher = ui.botao_secundario(s, self.f, "Escolher PDF…", self._escolher_pdf)
        self.btn_escolher.pack(padx=24, fill="x")

        # O PDF escolhido: nome, folhas e o estado da separação.
        chip = ui.chip(s)
        chip.pack(padx=24, pady=(10, 0), fill="x")
        self.lbl_pdf = ctk.CTkLabel(chip, text="", font=self.f["corpo"], wraplength=210,
                                    justify="left", anchor="w")
        self.lbl_pdf.pack(anchor="w", fill="x", padx=12, pady=8)
        self.lbl_folhas_pdf = ctk.CTkLabel(chip, text="", font=self.f["pequeno"],
                                           text_color=COR["texto_sec"], anchor="w")
        self.lbl_estado_pdf = ctk.CTkLabel(chip, text="", font=self.f["pequeno_b"], wraplength=210,
                                           justify="left", anchor="w")
        self._limpar_chip_pdf()

        # Hot folder: escolhida uma vez e lembrada entre sessões. Cada PDF tem
        # a sua subpasta lá dentro, para um binder nunca sobrepor outro.
        ui.label_secao(s, self.f, "HOT FOLDER").pack(anchor="w", padx=24, pady=(28, 8))
        chip_hot = ui.chip(s)
        chip_hot.pack(padx=24, fill="x")
        self.lbl_hot = ctk.CTkLabel(chip_hot, text="", font=self.f["pequeno"], wraplength=210,
                                    justify="left", anchor="w")
        self.lbl_hot.pack(anchor="w", fill="x", padx=12, pady=(8, 0))
        self.btn_hot = ui.botao_link(chip_hot, self.f, "", self._escolher_hot_folder,
                                     hover_color=COR["card"])
        self.btn_hot.pack(anchor="w", padx=6, pady=(0, 6))
        self._mostrar_hot_folder()

        self.btn_separar = ui.botao_principal(s, self.f, "Separar", self._separar)
        self.btn_separar.pack(side="bottom", pady=24, padx=24, fill="x")

    def _limpar_chip_pdf(self):
        self.lbl_pdf.configure(text="Nenhum PDF escolhido", text_color=COR["texto_sec"])
        self.lbl_pdf.pack_configure(pady=8)
        self.lbl_folhas_pdf.pack_forget()
        self.lbl_estado_pdf.pack_forget()

    def _escrever_log(self, texto):
        """O registo técnico não aparece na janela: os erros vão para o
        estado do PDF e para um aviso no fim. Fica só na consola, quando
        existe (a correr por 'python'); com 'pythonw' ou o .exe o print não
        faz nada."""
        try:
            print(texto.rstrip("\n"))
        except (OSError, ValueError):
            pass

    def _estado(self, texto, tipo="idle"):
        ui.definir_estado(self.lbl_status, texto, tipo)

    # ------------------------------------------------------------ hot folder

    def _mostrar_hot_folder(self):
        self.lbl_hot.configure(text=self.hot_folder or "—",
                               text_color=COR["texto"] if self.hot_folder else COR["texto_sec"])
        self.btn_hot.configure(text="Alterar…" if self.hot_folder else "Escolher…")

    def _escolher_hot_folder(self):
        """Pede a pasta e guarda-a. Devolve True se ficou uma pasta escolhida."""
        inicial = self.hot_folder if self.hot_folder and os.path.isdir(self.hot_folder) else None
        pasta = filedialog.askdirectory(
            title="Escolher a hot folder", initialdir=inicial, mustexist=True, parent=self.root,
        )
        if not pasta:
            return False
        self.hot_folder = os.path.normpath(pasta)
        config = ler_config()
        config["hot_folder"] = self.hot_folder
        gravar_config(config)
        self._mostrar_hot_folder()
        return True

    def _garantir_hot_folder(self):
        """Antes de separar: sem pasta escolhida, ou se a guardada deixou de
        existir (um disco de rede desligado, por exemplo), pede-a outra vez."""
        if self.hot_folder and os.path.isdir(self.hot_folder):
            return True
        if self.hot_folder:
            messagebox.showwarning(
                NOME_APP,
                f"A hot folder guardada não está acessível:\n\n{self.hot_folder}\n\n"
                "Escolha outra pasta.",
                parent=self.root,
            )
        return self._escolher_hot_folder()

    def _escolher_pdf(self):
        caminho = filedialog.askopenfilename(
            title="Escolher o PDF de encomendas",
            filetypes=[("Ficheiros PDF", "*.pdf"), ("Todos os ficheiros", "*.*")],
            parent=self.root,
        )
        if caminho:
            self._definir_pdf(caminho)

    def _receber_argumentos(self, caminhos):
        """PDF largado em cima do programa. Só um de cada vez: com vários não se
        escolhe nenhum, para não separar o errado."""
        if len(caminhos) == 1:
            self._definir_pdf(caminhos[0])
            return
        linhas = "\n".join(f"• {c}" for c in caminhos[:10])
        if len(caminhos) > 10:
            linhas += f"\n… e mais {len(caminhos) - 10}"
        messagebox.showwarning(
            NOME_APP, f"Largue só um PDF de cada vez.\n\n{linhas}", parent=self.root
        )

    def _definir_pdf(self, caminho):
        """Põe 'caminho' como o PDF a separar, no lugar do anterior."""
        if self.processando:
            return
        if not (os.path.isfile(caminho) and caminho.lower().endswith(".pdf")):
            motivo = "é uma pasta, não um PDF" if os.path.isdir(caminho) else "não é um ficheiro PDF"
            messagebox.showwarning(
                NOME_APP, f"Não é possível usar:\n\n{caminho}\n\n({motivo})", parent=self.root
            )
            return
        self.pdf = os.path.abspath(caminho)
        folhas = contar_folhas(self.pdf)
        self.lbl_pdf.configure(text=os.path.basename(self.pdf), text_color=COR["texto"])
        self.lbl_pdf.pack_configure(pady=(8, 0))
        self.lbl_folhas_pdf.configure(text="? folhas" if folhas is None else plural(folhas, "folha", "folhas"))
        self.lbl_folhas_pdf.pack(anchor="w", fill="x", padx=12)
        self.lbl_estado_pdf.pack(anchor="w", fill="x", padx=12, pady=(2, 8))
        self._definir_estado_linha("Por separar")
        self._actualizar_vazio()

    def _definir_estado_linha(self, texto, erro=False, tipo="idle"):
        """Estado da separação do PDF escolhido, no chip da sidebar."""
        if self.pdf:
            if len(texto) > 160:
                texto = texto[:159] + "…"
            self.lbl_estado_pdf.configure(text=texto, text_color=ui.cor_estado("erro" if erro else tipo))

    def _activar_botoes(self, activos):
        ui.botao_ocupado(self.btn_separar, not activos, "Separar", "A separar…")
        estado = "normal" if activos else "disabled"
        for b in (self.btn_escolher, self.btn_hot):
            b.configure(state=estado)

    # ------------------------------------------------------------ separação

    def _separar(self):
        if self.processando:
            return
        if not self.pdf:
            messagebox.showinfo(NOME_APP, "Escolha primeiro o PDF.", parent=self.root)
            return
        if not self._confirmar_recomeco():
            return
        if not self._garantir_hot_folder():
            return  # sem hot folder não há onde escrever
        pasta = motor._pasta_saida_para(self.pdf, set(), raiz=self.hot_folder)
        if not self._confirmar_substituicao(pasta):
            return

        # O trabalho anterior sai já de cena: se esta separação falhar, a área
        # Imprimir não pode ficar a mostrar blocos que já não são os da pasta.
        self._esquecer_trabalho()
        self.erro = None
        self.avisos = []
        self.processando = True
        self._actualizar_vazio()
        self._activar_botoes(False)
        # O motor só dá progresso na escrita dos blocos: a análise é uma fase sem medida
        self.progresso.iniciar("A analisar as folhas…")
        self._estado(f"A separar {os.path.basename(self.pdf)}…", "ativo")
        self._definir_estado_linha("A separar…", tipo="ativo")

        threading.Thread(
            target=self._trabalhar, args=(self.pdf, pasta), daemon=True
        ).start()
        self.root.after(100, self._drenar_fila)

    def _confirmar_recomeco(self):
        """Separar outra vez com a impressão a meio recomeça do zero: pergunta."""
        trabalho = self.trabalho
        if not trabalho:
            return True
        feitos, total = len(trabalho["impressos"]), len(trabalho["blocos"])
        if not 0 < feitos < total:
            return True
        return messagebox.askyesno(
            NOME_APP,
            f"A impressão de «{os.path.basename(trabalho['pdf'])}» vai em {feitos} de "
            f"{plural(total, 'bloco', 'blocos')}.\n\n"
            "Separar outra vez recomeça do zero. Continuar?",
            icon="warning", parent=self.root,
        )

    def _confirmar_substituicao(self, pasta):
        """A subpasta ainda tem os ficheiros de uma separação que não foi
        apagada (o binder de outro dia, que tem o mesmo nome, por exemplo):
        pergunta antes de os substituir."""
        if self.trabalho and os.path.normcase(self.trabalho["pasta"]) == os.path.normcase(pasta):
            return True  # é a separação que está na área Imprimir; o recomeço já foi confirmado
        nomes = motor.ficheiros_gerados_em(pasta)
        if not nomes:
            return True
        try:
            quando = max(os.path.getmtime(os.path.join(pasta, n)) for n in nomes)
            data = f", de {datetime.fromtimestamp(quando):%d/%m %H:%M}"
        except OSError:
            data = ""
        return messagebox.askyesno(
            NOME_APP,
            f"Já existe na hot folder uma separação anterior "
            f"({plural(len(nomes), 'ficheiro', 'ficheiros')}{data}):\n\n{pasta}\n\n"
            "Substituir? Os ficheiros antigos são apagados.",
            icon="warning", parent=self.root,
        )

    def _trabalhar(self, pdf, pasta):
        """Corre fora do thread da UI: publica tudo na fila, não toca em widgets.
        O "fim" sai sempre, aconteça o que acontecer; sem ele a janela ficava
        à espera para sempre."""
        publicar = self.fila.put
        try:
            publicar(("log", "-" * 70))
            publicar(("log", f"A processar: {pdf}"))
            publicar(("log", f"Saída: {pasta}"))
            publicar(("log", "-" * 70))
            avisos = []
            blocos = motor.gerar_blocos(
                pdf, pasta, "",
                log=lambda t: publicar(("log", t)),
                progresso=lambda n, t: publicar(("progresso", n, t)),
                avisos=avisos,
            )
            # As duas contagens são feitas aqui, a partir dos PDFs no disco:
            # o original e cada um dos ficheiros acabados de gerar.
            publicar(("fase", "A conferir as folhas com o original…"))
            por_ficheiro = [contar_folhas(b["caminho"]) for b in blocos]
            folhas_ficheiros = None if None in por_ficheiro else sum(por_ficheiro)
            publicar(("ok", pdf, pasta, blocos, contar_folhas(pdf), folhas_ficheiros, avisos))
        except Exception as e:
            publicar(("log", f"ERRO: {e}"))
            publicar(("erro", str(e)))
        finally:
            publicar(("fim",))

    def _drenar_fila(self):
        terminou = False
        try:
            while True:
                msg = self.fila.get_nowait()
                try:
                    terminou = self._tratar_mensagem(msg) or terminou
                except Exception:
                    # Um erro aqui não pode parar a leitura da fila: o "fim"
                    # ainda tem de chegar para a janela voltar a responder.
                    self.erro = self.erro or "Erro inesperado ao receber o resultado da separação."
                    self._erro_inesperado(*sys.exc_info())
        except queue.Empty:
            pass

        if terminou:
            self._fim_do_trabalho()
        else:
            self.root.after(100, self._drenar_fila)

    def _tratar_mensagem(self, msg):
        """Trata uma mensagem do thread de trabalho. Devolve True no "fim"."""
        tipo = msg[0]
        if tipo == "log":
            self._escrever_log(msg[1])
        elif tipo == "progresso":
            _, n, total = msg
            self.progresso.atualizar(n / max(total, 1), f"Bloco {n} de {total}")
        elif tipo == "fase":
            self.progresso.fase(msg[1])
        elif tipo == "ok":
            self._receber_ok(*msg[1:])
        elif tipo == "erro":
            self.erro = msg[1]
            self._definir_estado_linha(f"✗ {msg[1]}", erro=True)
        return tipo == "fim"

    def _receber_ok(self, pdf, pasta, blocos, folhas_original, folhas_ficheiros, avisos):
        """Confere a soma das folhas dos ficheiros gerados com a do original,
        ambas contadas pela janela nos PDFs do disco, antes de deixar o
        trabalho seguir para a impressão."""
        def txt(n):
            return "?" if n is None else str(n)

        contagem = f"{txt(folhas_ficheiros)}/{txt(folhas_original)} folhas"
        if folhas_original is None or folhas_ficheiros != folhas_original:
            self._definir_estado_linha(f"✗ {contagem} — não imprimir", erro=True)
            self.erro = (
                f"Os ficheiros separados somam {txt(folhas_ficheiros)} folhas, mas o "
                f"original tem {txt(folhas_original)}. Este PDF não passa para a impressão."
            )
            return

        self._definir_estado_linha(
            f"OK · {plural(len(blocos), 'bloco', 'blocos')} · {contagem} ✓", tipo="ok"
        )
        self._registar_trabalho(pdf, pasta, blocos, folhas_original, folhas_ficheiros)
        self.avisos = list(avisos)

    def _fim_do_trabalho(self):
        self.processando = False
        self._actualizar_vazio()
        self._activar_botoes(True)
        self.progresso.concluir(not self.erro and bool(self.trabalho))

        # Sem consola na janela: o erro aparece aqui, por extenso.
        if self.erro or not self.trabalho:
            self._esquecer_trabalho()
            self._estado("O PDF não foi separado", "erro")
            messagebox.showerror(
                NOME_APP,
                f"O PDF não foi separado.\n\n{self.erro or 'Motivo desconhecido.'}",
                parent=self.root,
            )
            return

        # Primeiro mostrar, depois carregar: o scroll até ao bloco só é
        # certo com a lista já desenhada.
        self._mostrar_trabalho(True)
        self._carregar_trabalho()
        self._estado(f"{plural(len(self.trabalho['blocos']), 'bloco', 'blocos')} por imprimir", "ok")
        if self.avisos:
            messagebox.showwarning(NOME_APP, "\n\n".join(self.avisos), parent=self.root)

    # ------------------------------------------------------- área Imprimir

    def _construir_area_imprimir(self):
        m = ctk.CTkFrame(self.root, fg_color="transparent")
        m.grid(row=0, column=1, sticky="nsew", padx=28, pady=(24, 16))
        m.grid_columnconfigure(0, weight=1)
        m.grid_rowconfigure(2, weight=1)

        cabecalho = ctk.CTkFrame(m, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(cabecalho, text="Imprimir", font=self.f["titulo"], text_color=COR["texto"]).pack(side="left")
        self.lbl_status = ctk.CTkLabel(cabecalho, text="", font=self.f["corpo"])
        self.lbl_status.pack(side="right")
        self._estado("Pronto")

        # Progresso da separação: só aparece enquanto separa.
        self.progresso = ui.Progresso(m, self.f, self.root)
        self.progresso.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.progresso.grid_remove()

        self.vazio = ctk.CTkLabel(m, text="Escolha o PDF e carregue em Separar.", font=self.f["corpo"],
                                  text_color=COR["texto_sec"])
        self.vazio.grid(row=2, column=0)

        v = self.vista = ctk.CTkFrame(m, fg_color="transparent")
        v.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        v.grid_columnconfigure(0, weight=1)
        v.grid_rowconfigure(3, weight=1)
        v.grid_remove()

        topo = ctk.CTkFrame(v, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew")
        self.lbl_nome_pdf = ctk.CTkLabel(topo, text="", font=self.f["corpo"], text_color=COR["texto_sec"])
        self.lbl_nome_pdf.pack(side="left")
        ui.botao_link(topo, self.f, "Abrir pasta", self._abrir_pasta).pack(side="right")

        # Painel de destaque: o que o operador tem de ler antes de imprimir.
        self.painel = ui.card(v, corner_radius=12, border_width=2)
        self.painel.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.lbl_bloco = ctk.CTkLabel(self.painel, text="—", font=self.f["secao"])
        self.lbl_bloco.pack(pady=(18, 0))
        self.lbl_gaveta = ctk.CTkLabel(self.painel, text="—", font=self.f["display"])
        self.lbl_gaveta.pack(pady=(2, 2))
        self.lbl_detalhe = ctk.CTkLabel(self.painel, text="", font=self.f["corpo"], wraplength=620)
        self.lbl_detalhe.pack(pady=(0, 18))
        # Só aparece no painel CONCLUÍDO: fecha o ciclo deste PDF.
        self.btn_apagar = ui.botao_secundario(self.painel, self.f, "Apagar ficheiros", self._apagar_ficheiros,
                                              text_color=COR["erro"], width=200)

        accoes = ctk.CTkFrame(v, fg_color="transparent")
        accoes.grid(row=2, column=0, sticky="ew", pady=(12, 10))
        self.btn_abrir = ui.botao_principal(accoes, self.f, "Abrir", self._abrir_bloco, width=130,
                                            fg_color=COR["accent"], hover_color=COR["accent_hover"])
        self.btn_abrir.pack(side="left")
        self.btn_impresso = ui.botao_principal(accoes, self.f, "Impresso ▶", self._marcar_e_avancar, width=170)
        self.btn_impresso.pack(side="left", padx=(8, 0))
        ui.botao_link(accoes, self.f, "Desmarcar", self._desmarcar, text_color=COR["texto_sec"]).pack(side="right")

        # Lista dos blocos. Clicar numa linha escolhe o bloco; duplo clique abre-o.
        caixa = ui.card(v)
        caixa.grid(row=3, column=0, sticky="nsew")
        self.lista = ctk.CTkScrollableFrame(caixa, fg_color="transparent",
                                            scrollbar_button_color=COR["card_hover"],
                                            scrollbar_button_hover_color=COR["borda"])
        self.lista.pack(fill="both", expand=True, padx=4, pady=6)

        # Progresso em folhas, não em blocos: é o número que se confere na pilha.
        self.barra_folhas = ui.barra(v, COR["sucesso"])
        self.barra_folhas.set(0)
        self.barra_folhas.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.lbl_estado = ctk.CTkLabel(v, text="", font=self.f["corpo_b"], text_color=COR["texto"], anchor="w")
        self.lbl_estado.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        self.lbl_conferencia = ctk.CTkLabel(v, text="", font=self.f["pequeno"], anchor="w")
        self.lbl_conferencia.grid(row=6, column=0, sticky="ew")

    def _mostrar_trabalho(self, mostrar):
        """Alterna entre o empty state e a vista do trabalho separado."""
        if mostrar:
            self.vazio.grid_remove()
            self.vista.grid()
        else:
            self.vista.grid_remove()
            self._actualizar_vazio()
            self.vazio.grid()

    def _actualizar_vazio(self):
        if self.processando:
            texto = "A separar o PDF…"
        elif self.pdf:
            texto = "Carregue em Separar para dividir o PDF em blocos."
        else:
            texto = "Escolha o PDF e carregue em Separar."
        self.vazio.configure(text=texto)

    def _trabalho(self):
        return self.trabalho

    def _registar_trabalho(self, pdf, pasta, blocos, folhas_original, folhas_ficheiros):
        """Põe o PDF acabado de separar na área Imprimir. O "impresso" fica
        só em memória: é o progresso desta separação e mais nada."""
        self.trabalho = {
            "pdf": pdf,
            "pasta": pasta,
            "blocos": blocos,
            "impressos": set(),
            "folhas_original": folhas_original,
            "folhas_ficheiros": folhas_ficheiros,
        }
        self.lbl_nome_pdf.configure(text=os.path.basename(pdf))

    def _esquecer_trabalho(self):
        """Tira o trabalho da área Imprimir e volta ao empty state."""
        self.trabalho = None
        self.abertos.clear()
        self.concluido = False
        self.idx_bloco = 0
        self.btn_apagar.pack_forget()
        self._geracao += 1
        for linha in self.linhas:
            linha["frame"].destroy()
        self.linhas = []
        self.lbl_nome_pdf.configure(text="")
        self._mostrar_trabalho(False)

    def _carregar_trabalho(self):
        trabalho = self.trabalho
        if not trabalho:
            return

        self._geracao += 1
        for linha in self.linhas:
            linha["frame"].destroy()
        # As linhas criam-se uma vez; depois só se reconfiguram as que mudam.
        # Cada uma custa ~40 ms: as primeiras aparecem já, as restantes (só
        # quando há muitos blocos) vão sendo criadas sem prender a janela.
        self.linhas = []
        self._criar_linhas(self._geracao, 15)
        self._ir_para(0)

    def _criar_linhas(self, geracao, quantas=15):
        trabalho = self.trabalho
        if not trabalho or geracao != self._geracao:
            return
        blocos = trabalho["blocos"]
        inicio = len(self.linhas)
        for i in range(inicio, min(inicio + quantas, len(blocos))):
            self.linhas.append(self._criar_linha(i, blocos[i]))
            self._pintar_linha(i, i == self.idx_bloco, blocos[i]["nome"] in trabalho["impressos"])
        if len(self.linhas) < len(blocos):
            self.root.after(1, self._criar_linhas, geracao)

    def _criar_linha(self, i, bloco):
        fundo, texto, _ = CORES_PAPEL[bloco["gaveta"]]
        frame = ctk.CTkFrame(self.lista, corner_radius=6, border_width=1,
                             fg_color=COR["card"], border_color=COR["card"])
        frame.pack(fill="x", padx=(0, 6), pady=1)
        frame.grid_columnconfigure(2, weight=1)

        n = ctk.CTkLabel(frame, text=str(i + 1), font=self.f["mono"], width=36, height=22, anchor="e")
        n.grid(row=0, column=0, sticky="e", padx=(6, 10), pady=(8, 0))
        nome = ctk.CTkLabel(frame, text=bloco["nome"], font=self.f["mono"], anchor="w", height=22)
        nome.grid(row=0, column=1, sticky="w", pady=(8, 0))
        papel = ui.pill(frame, self.f, descricao_gaveta(bloco), fundo=fundo, cor=texto, height=22)
        papel.grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(8, 0))
        folhas = ctk.CTkLabel(frame, text=plural(bloco["folhas"], "folha", "folhas"), font=self.f["pequeno"],
                              anchor="e", height=22)
        folhas.grid(row=0, column=3, sticky="e", padx=(12, 0), pady=(8, 0))
        visto = ctk.CTkLabel(frame, text="", font=self.f["corpo_b"], text_color=COR["sucesso"], width=28,
                             height=22)
        visto.grid(row=0, column=4, padx=(4, 8), pady=(8, 0))
        paginas = ctk.CTkLabel(frame, text=f"{bloco['paginas_frase']} do original", font=self.f["pequeno"],
                               anchor="w", justify="left", wraplength=520)
        paginas.grid(row=1, column=1, columnspan=3, sticky="w", pady=(0, 8))

        # Só as linhas têm cliques: o espaço vazio da lista não abre nada por engano.
        for w in (frame, n, nome, papel, folhas, visto, paginas):
            w.bind("<Button-1>", lambda _e, i=i: self._ao_selecionar_bloco(i))
            w.bind("<Double-Button-1>", lambda _e, i=i: self._ao_duplo_clique(i))

        return {"frame": frame, "textos": (n, nome, folhas), "paginas": paginas, "visto": visto,
                "estado": None}

    def _pintar_linha(self, i, selecionada, feito):
        linha = self.linhas[i]
        if linha["estado"] == (selecionada, feito):
            return
        linha["estado"] = (selecionada, feito)
        linha["frame"].configure(fg_color=COR["card_hover"] if selecionada else COR["card"],
                                 border_color=COR["accent"] if selecionada else COR["card"])
        for lbl in linha["textos"]:
            lbl.configure(text_color=COR["texto_feito"] if feito else COR["texto"])
        linha["paginas"].configure(text_color=COR["texto_feito"] if feito else COR["texto_sec"])
        linha["visto"].configure(text="✓" if feito else "")

    def _mostrar_linha(self, i):
        """Faz scroll até à linha, se estiver fora de vista."""
        self.root.update_idletasks()
        canvas = self.lista._parent_canvas
        altura = self.lista.winfo_height()
        if altura <= 1 or not canvas.winfo_ismapped():
            return
        frame = self.linhas[i]["frame"]
        cima, baixo = frame.winfo_y() / altura, (frame.winfo_y() + frame.winfo_height()) / altura
        vista_cima, vista_baixo = canvas.yview()
        if cima < vista_cima:
            canvas.yview_moveto(cima)
        elif baixo > vista_baixo:
            canvas.yview_moveto(baixo - (vista_baixo - vista_cima))

    def _ir_para(self, indice):
        trabalho = self._trabalho()
        if not trabalho:
            return
        self.concluido = False
        self.idx_bloco = max(0, min(indice, len(trabalho["blocos"]) - 1))
        self._actualizar_vista()
        if self.idx_bloco < len(self.linhas):
            self._mostrar_linha(self.idx_bloco)

    def _ao_selecionar_bloco(self, indice):
        if indice != self.idx_bloco:
            self.idx_bloco = indice
            self.concluido = False
            self._actualizar_vista()

    def _ao_duplo_clique(self, indice):
        """Duplo clique numa linha abre esse bloco, como o botão Abrir."""
        if indice != self.idx_bloco or self.concluido:
            self._ir_para(indice)
        self._abrir_bloco()
        return "break"

    def _pintar_painel(self, fundo, texto, borda):
        self.painel.configure(fg_color=fundo, border_color=borda)
        for lbl in (self.lbl_bloco, self.lbl_gaveta, self.lbl_detalhe):
            lbl.configure(text_color=texto)

    def _actualizar_vista(self):
        trabalho = self._trabalho()
        if not trabalho:
            return
        blocos = trabalho["blocos"]
        impressos = trabalho["impressos"]

        for i, b in enumerate(blocos[:len(self.linhas)]):
            self._pintar_linha(i, i == self.idx_bloco, b["nome"] in impressos)

        # Progresso em folhas impressas e a conferência entre o original e a
        # soma dos ficheiros separados, ambos contados nos PDFs do disco.
        total = sum(b["folhas"] for b in blocos)
        feitas = sum(b["folhas"] for b in blocos if b["nome"] in impressos)
        original = trabalho["folhas_original"]
        separadas = trabalho["folhas_ficheiros"]
        self.barra_folhas.set(feitas / max(total, 1))
        self.lbl_estado.configure(
            text=f"{len(impressos)} de {len(blocos)} blocos · {feitas} de {total} folhas impressas"
        )
        self.lbl_conferencia.configure(
            text=f"\"{os.path.basename(trabalho['pdf'])}\" = {original} folhas  |  "
                 f"Contagem total blocos separados: {separadas} folhas "
                 f"{'✓' if original == separadas else '✗'}",
            text_color=COR["texto_sec"] if original == separadas else COR["erro"],
        )

        if self.concluido:
            return

        self.btn_apagar.pack_forget()
        bloco = blocos[self.idx_bloco]
        self._pintar_painel(*CORES_PAPEL[bloco["gaveta"]])

        self.lbl_bloco.configure(text=f"BLOCO {self.idx_bloco + 1} DE {len(blocos)}")
        self.lbl_gaveta.configure(text=descricao_gaveta(bloco))
        marca = "   ·   ✓ IMPRESSO" if bloco["nome"] in impressos else ""
        self.lbl_detalhe.configure(
            text=f"{plural(bloco['folhas'], 'folha', 'folhas')}   ·   "
                 f"{bloco['paginas_frase']} do original{marca}"
        )

    def _mostrar_concluido(self):
        """Painel verde no fim, com tudo marcado como impresso."""
        trabalho = self._trabalho()
        if not trabalho:
            return
        self.concluido = True
        self._actualizar_vista()
        self._pintar_painel(*CORES_CONCLUIDO)
        self.lbl_bloco.configure(text=f"TODOS OS {len(trabalho['blocos'])} BLOCOS IMPRESSOS")
        self.lbl_gaveta.configure(text="CONCLUÍDO")
        self.lbl_detalhe.configure(text="")
        self.btn_apagar.pack(pady=(0, 18))
        self._estado("Impressão concluída", "ok")

    def _abrir_bloco(self):
        trabalho = self._trabalho()
        if trabalho:
            caminho = trabalho["blocos"][self.idx_bloco]["caminho"]
            if motor.abrir_pdf(caminho):
                self.abertos.add(os.path.normcase(os.path.abspath(caminho)))

    def _abrir_pasta(self):
        trabalho = self._trabalho()
        if trabalho:
            motor.abrir_pdf(trabalho["pasta"])

    def _marcar_e_avancar(self):
        trabalho = self._trabalho()
        if not trabalho:
            return
        blocos = trabalho["blocos"]
        impressos = trabalho["impressos"]
        bloco = blocos[self.idx_bloco]

        # Um bloco marcado sem ter sido impresso é uma série de folhas seguidas
        # que falta na pilha e ninguém dá por isso até à montagem.
        aberto = os.path.normcase(os.path.abspath(bloco["caminho"])) in self.abertos
        if bloco["nome"] not in impressos and not aberto:
            if not messagebox.askyesno(
                NOME_APP,
                f"O bloco {self.idx_bloco + 1} ({bloco['nome']}, "
                f"{plural(bloco['folhas'], 'folha', 'folhas')}) "
                "ainda não foi aberto nesta sessão.\n\n"
                "Tem a certeza de que já está impresso?",
                icon="warning", parent=self.root,
            ):
                return

        impressos.add(bloco["nome"])

        seguinte = next((i for i in range(self.idx_bloco + 1, len(blocos))
                         if blocos[i]["nome"] not in impressos), None)
        if seguinte is not None:
            self._ir_para(seguinte)
            return

        # Chegou ao fim: nenhum bloco pode ter ficado para trás.
        em_falta = [i for i, b in enumerate(blocos) if b["nome"] not in impressos]
        if em_falta:
            self._actualizar_vista()
            linhas = "\n".join(
                f"  • {blocos[i]['nome']}  —  {plural(blocos[i]['folhas'], 'folha', 'folhas')} "
                f"({blocos[i]['paginas_frase']} do original)"
                for i in em_falta[:10]
            )
            if len(em_falta) > 10:
                linhas += f"\n  … e mais {len(em_falta) - 10}"
            messagebox.showwarning(
                NOME_APP,
                f"ATENÇÃO: faltam imprimir {plural(len(em_falta), 'bloco', 'blocos')}:\n\n{linhas}",
                parent=self.root,
            )
            self._ir_para(em_falta[0])
            return

        self._mostrar_concluido()

    def _desmarcar(self):
        trabalho = self._trabalho()
        if not trabalho:
            return
        trabalho["impressos"].discard(trabalho["blocos"][self.idx_bloco]["nome"])
        self.concluido = False
        self._actualizar_vista()

    def _apagar_ficheiros(self):
        """Fim do ciclo: apaga o que a separação gerou e volta ao início. Só
        toca nos ficheiros que o programa gera; o PDF original e qualquer outro
        ficheiro ficam onde estão."""
        trabalho = self.trabalho
        if not trabalho or self.processando:
            return
        pasta = trabalho["pasta"]
        original = os.path.normcase(os.path.abspath(trabalho["pdf"]))
        nomes = [n for n in motor.ficheiros_gerados_em(pasta)
                 if os.path.normcase(os.path.abspath(os.path.join(pasta, n))) != original]
        if not messagebox.askyesno(
            NOME_APP,
            f"Apagar {plural(len(nomes), 'ficheiro gerado', 'ficheiros gerados')} por esta "
            f"separação?\n\n{pasta}\n\nO PDF original não é apagado.",
            icon="warning", parent=self.root,
        ):
            return

        presos = []
        for nome in nomes:
            try:
                os.remove(os.path.join(pasta, nome))
            except OSError:
                presos.append(nome)
        if presos:
            linhas = "\n".join(f"• {n}" for n in presos)
            messagebox.showerror(
                NOME_APP,
                f"Não consegui apagar (estão abertos noutro programa?):\n\n{linhas}\n\n"
                "Feche-os e carregue outra vez em «Apagar ficheiros».",
                parent=self.root,
            )
            return
        try:
            os.rmdir(pasta)  # só sai se ficou vazia: o que não é nosso não se toca
        except OSError:
            pass

        self._esquecer_trabalho()
        self.pdf = None
        self._limpar_chip_pdf()
        self._actualizar_vazio()
        self._estado("Pronto")

    def _erro_inesperado(self, tipo, valor, tb):
        """Qualquer erro num callback da janela. Sem consola (pythonw / .exe)
        ficaria invisível; assim aparece num aviso e a janela continua viva."""
        self._escrever_log("".join(traceback.format_exception(tipo, valor, tb)))
        messagebox.showerror(
            NOME_APP, f"Erro inesperado:\n\n{tipo.__name__}: {valor}", parent=self.root,
        )

    # ---------------------------------------------------------------- fecho

    def _ao_fechar(self):
        if self.processando:
            if not messagebox.askyesno(
                NOME_APP,
                "Ainda há PDFs a ser processados. Fechar agora pode deixar ficheiros "
                "incompletos na pasta de saída.\n\nFechar mesmo assim?",
                parent=self.root,
            ):
                return
        self.root.destroy()


def main():
    ui.preparar()
    root = ctk.CTk()
    Aplicacao(root, sys.argv[1:])
    root.mainloop()


if __name__ == "__main__":
    main()
