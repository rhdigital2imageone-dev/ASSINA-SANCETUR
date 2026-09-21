import os
import re
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

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
        self.regex_codigo_epi_nome = re.compile(r'_(\d{2})_(\d{1,6})_(\d{8})(?=_)')
        self.regex_periodo_pdf = re.compile(
            r'(?:Per.{0,2}odo|Compet.{0,2}ncia)\s*:\s*'
            r'(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})',
            re.IGNORECASE
        )
        self.regex_codigo_epi_pdf = re.compile(
            r'\bTipo\s+\d+\s+C.{0,2}d\.?\s*IO\s*(\d+)\b',
            re.IGNORECASE
        )
        self.regex_data_br = re.compile(r'\d{2}/\d{2}/\d{4}')

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
                "EPI",
                "Folha Ponto",
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
    def _ler_texto_pdf(self, caminho):

        if PdfReader is None:
            raise RuntimeError(
                "Biblioteca pypdf ausente. Instale as dependencias do projeto."
            )

        leitor = PdfReader(caminho)
        if leitor.is_encrypted:
            raise ValueError("PDF protegido por senha.")

        return "\n".join(
            pagina.extract_text() or ""
            for pagina in leitor.pages
        )

    def _data_validada(self, texto):

        return datetime.strptime(texto, "%d/%m/%Y").date()

    def _classificar_pdf(self, caminho):

        texto = self._ler_texto_pdf(caminho)
        codigos_epi = set(self.regex_codigo_epi_pdf.findall(texto))
        periodos = self.regex_periodo_pdf.findall(texto)

        if codigos_epi and periodos:
            raise ValueError("PDF contem campos de EPI e de folha-ponto.")

        if codigos_epi:
            if len(codigos_epi) != 1:
                raise ValueError("Mais de um codigo EPI foi encontrado.")

            cabecalho_data = re.search(r'DATA\s+ENTREGA\b', texto, re.IGNORECASE)
            if not cabecalho_data:
                raise ValueError("Campo DATA ENTREGA nao encontrado.")

            bloco_entrega = texto[cabecalho_data.end():]
            fim_tabela = re.search(r'\bdeclaro\b', bloco_entrega, re.IGNORECASE)
            if fim_tabela:
                bloco_entrega = bloco_entrega[:fim_tabela.start()]
            else:
                bloco_entrega = bloco_entrega[:300]

            datas_entrega = self.regex_data_br.findall(bloco_entrega)
            datas_unicas = set(datas_entrega)
            if len(datas_unicas) != 1:
                raise ValueError(
                    "A ficha deve conter uma unica data de entrega identificavel."
                )

            data_entrega = self._data_validada(datas_unicas.pop())
            return "EPI", codigos_epi.pop(), data_entrega

        if periodos:
            finais = set()
            for inicio_txt, fim_txt in periodos:
                inicio = self._data_validada(inicio_txt)
                fim = self._data_validada(fim_txt)
                if inicio > fim:
                    raise ValueError("O periodo da folha-ponto esta invertido.")
                finais.add(fim)

            if len(finais) != 1:
                raise ValueError("Datas finais divergentes nos campos do PDF.")

            return "FOLHA PONTO", None, finais.pop()

        raise ValueError("Nao identificado como EPI nem como folha-ponto.")

    def _ajustar_matricula(self, nome):

        matricula = self.regex_matricula.match(nome)
        if matricula and len(matricula.group(1)) == 7:
            return nome.replace(
                matricula.group(1),
                matricula.group(1).zfill(8),
                1
            )
        return nome

    def _preparar_pdf(self, caminho, nome):

        tipo, codigo_epi, data_documento = self._classificar_pdf(caminho)
        nome = self._ajustar_matricula(nome)
        data_nova = data_documento.strftime("%d%m%Y")

        if tipo == "EPI":
            match = self.regex_codigo_epi_nome.search(nome)
            if not match:
                raise ValueError("Padrao de nome de arquivo EPI nao reconhecido.")

            nome = self.regex_codigo_epi_nome.sub(
                lambda m: f"_{m.group(1)}_{codigo_epi}_{data_nova}",
                nome,
                count=1
            )
        else:
            if not self.regex_data.search(nome):
                raise ValueError("Data no nome do arquivo nao encontrada.")
            nome = self.regex_data.sub(f"_{data_nova}", nome, count=1)

        return nome, tipo, data_documento

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
            tipo_documento = None
            pasta_destino = None
            erro = None

            if arq.lower().endswith(".pdf"):
                try:
                    novo, tipo_documento, data = self._preparar_pdf(path, arq)
                    pasta_destino = tipo_documento
                    status = "AJUSTADO" if novo != arq else "BR"
                except Exception as exc:
                    erro = str(exc)
            else:
                novo = self._ajustar_matricula(novo)
                match = self.regex_data.search(novo)

                if match:
                    data = match.group(1)
                    try:
                        dia, mes, ano = int(data[:2]), int(data[2:4]), int(data[4:8])
                        data_br = datetime(ano, mes, dia).date()
                        if data_br <= hoje:
                            status = "BR"
                    except ValueError:
                        try:
                            ano, mes, dia = int(data[:4]), int(data[4:6]), int(data[6:8])
                            data_us = datetime(ano, mes, dia).date()

                            if 1900 <= ano <= ano_atual and data_us <= hoje:
                                novo = self.regex_data.sub(
                                    f"_{dia:02d}{mes:02d}{ano}", novo, count=1
                                )
                                status = "CONVERTIDO"
                        except ValueError:
                            status = "ERRO"

                    match2 = self.regex_data.search(novo)
                    if match2:
                        data2 = match2.group(1)
                        try:
                            dia, mes, ano = int(data2[:2]), int(data2[2:4]), int(data2[4:8])
                            datetime(ano, mes, dia)
                            if dia <= limite:
                                mes -= 1
                                if mes == 0:
                                    mes = 12
                                    ano -= 1
                                novo = self.regex_data.sub(
                                    f"_{limite:02d}{mes:02d}{ano}", novo, count=1
                                )
                                if status != "ERRO":
                                    status = "AJUSTADO"
                        except ValueError:
                            pass

            novo = re.sub(r'_+', '_', novo)

            self.resultados.append({
                "arquivo": arq,
                "novo": novo,
                "status": status,
                "data": data,
                "tipo_documento": tipo_documento,
                "pasta_destino": pasta_destino,
                "erro": erro
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

            if filtro == "EPI" and r.get("tipo_documento") != "EPI":
                continue

            if filtro == "Folha Ponto" and r.get("tipo_documento") != "FOLHA PONTO":
                continue

            if (
                filtro == "Com erro"
                and r["status"] != "ERRO"
            ):
                continue

            if r.get("tipo_documento") in ("EPI", "FOLHA PONTO"):

                nome_tipo = r["tipo_documento"]
                self._log(f"DOCUMENTO IDENTIFICADO: {nome_tipo}", "ok")
                self._log(f"ANTES: {r['arquivo']}", "normal")
                self._log(
                    f"DEPOIS: {r['novo']}\nPASTA: {nome_tipo}\n",
                    "ok"
                )

            elif r["status"] == "CONVERTIDO":

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

                self._log("ERRO AO ANALISAR DOCUMENTO", "erro")
                self._log(
                    f"Arquivo: {r['arquivo']}\nMotivo: {r.get('erro') or 'Data invalida.'}\n",
                    "normal"
                )

    def renomear(self):

        alvos = [
            r for r in self.resultados
            if r["status"] != "ERRO"
            and (
                r["arquivo"] != r["novo"]
                or r.get("pasta_destino")
            )
        ]

        if not alvos:
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"{len(alvos)} arquivos serao renomeados e organizados.\nDeseja continuar?"
        ):
            return

        for i, r in enumerate(alvos, start=1):
            origem = os.path.join(self.pasta, r["arquivo"])
            pasta_destino = self.pasta

            if r.get("pasta_destino"):
                pasta_destino = os.path.join(
                    self.pasta,
                    r["pasta_destino"]
                )
                os.makedirs(pasta_destino, exist_ok=True)

            destino = os.path.join(pasta_destino, r["novo"])

            if os.path.exists(destino):
                self._log(f"JA EXISTE: {destino}", "erro")
                continue

            try:
                os.rename(origem, destino)
            except OSError as exc:
                self._log(
                    f"ERRO AO MOVER {r['arquivo']}: {exc}\n",
                    "erro"
                )
                continue

            self.progress.set(i / len(alvos))
            self.lbl_status.configure(
                text=f"Organizando: {i:,} / {len(alvos):,}"
            )

        self.lbl_status.configure(text="Renomeacao concluida")

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
