import os
import re
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime

# ================== TEMA ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ================== CORES ==================
BG_MAIN = "#0B0B0B"
BG_CARD = "#121212"
RED = "#C1121F"
GREEN = "#00E676"
ORANGE = "#FFA726"
TEXT = "#EDEDED"
SUBTEXT = "#AAAAAA"
BLUE = "#1F6AA5"

# ================== APP ==================
class RenomeadorDatas(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Renomeador Inteligente de Datas • BR")
        self.geometry("1120x800")
        self.configure(fg_color=BG_MAIN)

        self.pasta = ""
        self.resultados = []

        # CORRIGIDO
        self.regex_data = re.compile(r'_(\d{8})(?=_)')
        self.regex_matricula = re.compile(r'^(\d{7,8})_')

        self.criar_layout()
        self.configurar_tags()

    # ================== UI ==================
    def criar_layout(self):

        header = ctk.CTkFrame(self, fg_color=BG_MAIN)
        header.pack(fill="x", pady=(15, 5))

        ctk.CTkLabel(
            header,
            text="Renomeador Inteligente de Datas",
            font=("Segoe UI", 26, "bold"),
            text_color=RED
        ).pack()

        ctk.CTkLabel(
            header,
            text="Simular • Converter • Zerar datas com segurança",
            font=("Segoe UI", 14),
            text_color=SUBTEXT
        ).pack(pady=(0, 10))

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="x", padx=30, pady=15)

        botoes = ctk.CTkFrame(card, fg_color="transparent")
        botoes.pack(pady=10)

        ctk.CTkButton(
            botoes,
            text="📂 Selecionar Pasta",
            fg_color=RED,
            hover_color="#8E0E16",
            command=self.selecionar_pasta,
            width=200
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            botoes,
            text="👁️ Simular",
            fg_color="#2A2A2A",
            command=self.iniciar_simulacao,
            width=160
        ).grid(row=0, column=1, padx=8)

        ctk.CTkButton(
            botoes,
            text="🧹 Zerar Datas",
            fg_color=ORANGE,
            hover_color="#FB8C00",
            command=self.iniciar_zerar_datas,
            width=180
        ).grid(row=0, column=2, padx=8)

        ctk.CTkButton(
            botoes,
            text="✅ Renomear",
            fg_color=BLUE,
            command=self.iniciar_renomeacao,
            width=180
        ).grid(row=0, column=3, padx=8)

        # DIA LIMITE
        self.entry_dia = ctk.CTkEntry(
            card,
            width=150,
            placeholder_text="Dia limite"
        )
        self.entry_dia.insert(0, "20")
        self.entry_dia.pack(pady=(5, 10))

        self.progress = ctk.CTkProgressBar(card, width=800)
        self.progress.pack(pady=(5, 2))
        self.progress.set(0)

        self.lbl_status = ctk.CTkLabel(
            card,
            text="",
            text_color=SUBTEXT
        )
        self.lbl_status.pack(pady=(0, 10))

        self.combo_filtro = ctk.CTkComboBox(
            card,
            values=[
                "Todos",
                "Convertidos",
                "Já estavam corretos",
                "Datas zeradas",
                "Ajustados",
                "Com erro"
            ],
            command=self.aplicar_filtro,
            width=260
        )

        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(pady=(0, 10))

        self.log = ctk.CTkTextbox(
            self,
            fg_color="#0E0E0E",
            text_color=TEXT,
            font=("Consolas", 13),
            corner_radius=10
        )

        self.log.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        self.log.configure(state="disabled")

    def configurar_tags(self):

        t = self.log._textbox

        t.tag_config("ok", foreground=GREEN)
        t.tag_config("erro", foreground=RED)
        t.tag_config("sub", foreground=SUBTEXT)
        t.tag_config("normal", foreground=TEXT)
        t.tag_config("warn", foreground=ORANGE)

    # ================== AÇÕES ==================
    def selecionar_pasta(self):

        pasta = filedialog.askdirectory()

        if pasta:
            self.pasta = pasta
            self._limpar()

            self._log(
                f"Pasta selecionada:\n{pasta}\n",
                "sub"
            )

    def iniciar_simulacao(self):

        if not self.pasta:
            messagebox.showwarning(
                "Atenção",
                "Selecione uma pasta primeiro."
            )
            return

        threading.Thread(
            target=self.simular,
            daemon=True
        ).start()

    def iniciar_zerar_datas(self):

        if not self.pasta:
            messagebox.showwarning(
                "Atenção",
                "Selecione uma pasta primeiro."
            )
            return

        threading.Thread(
            target=self.zerar_datas,
            daemon=True
        ).start()

    def iniciar_renomeacao(self):

        threading.Thread(
            target=self.renomear,
            daemon=True
        ).start()

    # ================== LÓGICA ==================
    def simular(self):

        self.resultados.clear()
        self.progress.set(0)
        self._limpar()

        try:
            limite = int(self.entry_dia.get())
        except:
            limite = 20

        arquivos = os.listdir(self.pasta)
        total = len(arquivos)

        hoje = datetime.today().date()
        ano_atual = hoje.year

        for i, arq in enumerate(arquivos, start=1):

            path = os.path.join(self.pasta, arq)

            if not os.path.isfile(path):
                continue

            novo = arq
            status = "ERRO"
            data = None

            # ===== MATRÍCULA =====
            m = self.regex_matricula.match(novo)

            if m and len(m.group(1)) == 7:
                novo = novo.replace(
                    m.group(1),
                    m.group(1).zfill(8),
                    1
                )

            match = self.regex_data.search(novo)

            if match:

                data = match.group(1)

                # ===== BR =====
                try:

                    dia = int(data[:2])
                    mes = int(data[2:4])
                    ano = int(data[4:8])

                    data_br = datetime(
                        ano,
                        mes,
                        dia
                    ).date()

                    if data_br <= hoje:
                        status = "BR"

                except:
                    pass

                # ===== US =====
                if status != "BR":

                    try:

                        ano = int(data[:4])
                        mes = int(data[4:6])
                        dia = int(data[6:8])

                        data_us = datetime(
                            ano,
                            mes,
                            dia
                        ).date()

                        if (
                            1900 <= ano <= ano_atual
                            and data_us <= hoje
                        ):

                            # CORRIGIDO
                            novo = self.regex_data.sub(
                                f"_{dia:02d}{mes:02d}{ano}",
                                novo
                            )

                            status = "CONVERTIDO"

                    except:
                        status = "ERRO"

            # ===== AJUSTE DE COMPETÊNCIA =====
            match2 = self.regex_data.search(novo)

            if match2:

                data2 = match2.group(1)

                try:

                    dia = int(data2[:2])
                    mes = int(data2[2:4])
                    ano = int(data2[4:8])

                    if dia <= limite:

                        if mes == 1:
                            mes = 12
                            ano -= 1
                        else:
                            mes -= 1

                        nova_data = f"{limite:02d}{mes:02d}{ano}"

                        # CORRIGIDO
                        novo = self.regex_data.sub(
                            f"_{nova_data}",
                            novo
                        )

                        if status != "ERRO":
                            status = "AJUSTADO"

                except:
                    pass

            novo = re.sub(r'_+', '_', novo)

            self.resultados.append({
                "arquivo": arq,
                "novo": novo,
                "status": status,
                "data": data
            })

            self.progress.set(i / total)

            self.lbl_status.configure(
                text=f"Simulando: {i:,} / {total:,}"
            )

        self.aplicar_filtro("Todos")

    def zerar_datas(self):

        self.resultados.clear()
        self.progress.set(0)
        self._limpar()

        arquivos = os.listdir(self.pasta)
        total = len(arquivos)

        for i, arq in enumerate(arquivos, start=1):

            path = os.path.join(self.pasta, arq)

            if not os.path.isfile(path):
                continue

            novo = arq
            status = "SEM DATA"

            match = self.regex_data.search(arq)

            if match and match.group(1) != "00000000":

                novo = self.regex_data.sub(
                    "_00000000",
                    arq
                )

                novo = re.sub(r'_+', '_', novo)

                status = "ZERADO"

            self.resultados.append({
                "arquivo": arq,
                "novo": novo,
                "status": status,
                "data": match.group(1) if match else None
            })

            self.progress.set(i / total)

            self.lbl_status.configure(
                text=f"Zerando datas: {i:,} / {total:,}"
            )

        self.aplicar_filtro("Todos")

    def aplicar_filtro(self, filtro):

        self._limpar()

        for r in self.resultados:

            if (
                filtro == "Convertidos"
                and r["status"] != "CONVERTIDO"
            ):
                continue

            if (
                filtro == "Já estavam corretos"
                and r["status"] != "BR"
            ):
                continue

            if (
                filtro == "Datas zeradas"
                and r["status"] != "ZERADO"
            ):
                continue

            if (
                filtro == "Ajustados"
                and r["status"] != "AJUSTADO"
            ):
                continue

            if (
                filtro == "Com erro"
                and r["status"] != "ERRO"
            ):
                continue

            if r["status"] == "CONVERTIDO":

                self._log(
                    "🟢 CONVERTIDO",
                    "ok"
                )

                self._log(
                    f"ANTES: {r['arquivo']}",
                    "normal"
                )

                self._log(
                    f"DEPOIS: {r['novo']}\n",
                    "ok"
                )

            elif r["status"] == "BR":

                self._log(
                    "🔵 JÁ ESTAVA NO PADRÃO BR",
                    "sub"
                )

                self._log(
                    f"Arquivo: {r['arquivo']}\n",
                    "normal"
                )

            elif r["status"] == "ZERADO":

                self._log(
                    "🟠 DATA ZERADA",
                    "warn"
                )

                self._log(
                    f"ANTES: {r['arquivo']}",
                    "normal"
                )

                self._log(
                    f"DEPOIS: {r['novo']}\n",
                    "normal"
                )

            elif r["status"] == "AJUSTADO":

                self._log(
                    "🟣 AJUSTADO PARA COMPETÊNCIA",
                    "warn"
                )

                self._log(
                    f"ANTES: {r['arquivo']}",
                    "normal"
                )

                self._log(
                    f"DEPOIS: {r['novo']}\n",
                    "ok"
                )

            elif r["status"] == "ERRO":

                self._log(
                    "🔴 ERRO DE DATA",
                    "erro"
                )

                self._log(
                    f"Arquivo: {r['arquivo']}\n",
                    "normal"
                )

    def renomear(self):

        alvos = [
            r for r in self.resultados
            if r["arquivo"] != r["novo"]
        ]

        if not alvos:
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"{len(alvos)} arquivos serão renomeados.\nDeseja continuar?"
        ):
            return

        for i, r in enumerate(alvos, start=1):

            origem = os.path.join(
                self.pasta,
                r["arquivo"]
            )

            destino = os.path.join(
                self.pasta,
                r["novo"]
            )

            if os.path.exists(destino):

                self._log(
                    f"⚠️ JÁ EXISTE: {r['novo']}",
                    "erro"
                )

                continue

            os.rename(origem, destino)

            self.progress.set(i / len(alvos))

            self.lbl_status.configure(
                text=f"Renomeando: {i:,} / {len(alvos):,}"
            )

        self.lbl_status.configure(
            text="Renomeação concluída"
        )

    # ================== UTIL ==================
    def _log(self, texto, tag):

        self.log.configure(state="normal")

        self.log._textbox.insert(
            "end",
            texto + "\n",
            tag
        )

        self.log.configure(state="disabled")

        self.log.see("end")

    def _limpar(self):

        self.log.configure(state="normal")

        self.log.delete("1.0", "end")

        self.log.configure(state="disabled")


# ================== START ==================
if __name__ == "__main__":
    RenomeadorDatas().mainloop()