import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import export_all
import extractor
import formatter
import search


class StoryToolsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        for font_name in tkfont.names(self):
            tkfont.nametofont(font_name, root=self).configure(family="Yu Mincho")
        self.title("アークナイツ ストーリーツール")
        self.geometry("2400x1200")
        self.minsize(700, 500)

        self.messages = queue.Queue()
        self.action_buttons = []
        self.json_files = []
        self.csv_files = []

        self._build_interface()
        self.after(100, self._process_messages)

    def _build_interface(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1000)

        self.tabs = ttk.Notebook(container)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        self._build_search_tab()
        self._build_export_tab()
        self._build_extract_tab()
        self._build_format_tab()

        activity_frame = ttk.LabelFrame(container, text="実行状況・検索結果", padding=8)
        activity_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        activity_frame.rowconfigure(0, weight=1)
        activity_frame.columnconfigure(0, weight=1)
        self.activity = tk.Text(activity_frame, height=10, wrap="none", state="disabled")
        self.activity.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            activity_frame, orient="vertical", command=self.activity.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.activity.configure(yscrollcommand=scrollbar.set)
        self.status = tk.StringVar(value="準備完了")
        ttk.Label(container, textvariable=self.status, anchor="w").grid(
            row=2, column=0, sticky="ew", pady=(6, 0)
        )

    def _add_path_row(self, parent, row, label, variable, browse_command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", padx=8, pady=5
        )
        ttk.Button(parent, text="参照...", command=browse_command).grid(
            row=row, column=2, pady=5
        )
        parent.columnconfigure(1, weight=1)

    def _directory_dialog(self, variable):
        selected = filedialog.askdirectory()
        if selected:
            variable.set(selected)

    def _file_dialog(self, variable, title, filetypes):
        selected = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
        if selected:
            variable.set(selected)

    def _build_export_tab(self):
        frame = ttk.Frame(self.tabs, padding=16)
        frame.columnconfigure(1, weight=1)
        self.tabs.add(frame, text="一括出力")

        self.export_input = tk.StringVar()
        self.export_output = tk.StringVar(
            value=str(Path(__file__).resolve().parent / "exported")
        )
        self._add_path_row(
            frame, 0, "入力フォルダー", self.export_input,
            lambda: self._directory_dialog(self.export_input),
        )
        self._add_path_row(
            frame, 1, "出力フォルダー", self.export_output,
            lambda: self._directory_dialog(self.export_output),
        )
        button = ttk.Button(frame, text="JSONストーリーをTXTに一括出力", command=self._export_all)
        button.grid(row=2, column=1, sticky="e", pady=(12, 0))
        self.action_buttons.append(button)

    def _file_list(self, parent, row, label, add_command, clear_command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="nw", pady=5)
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=row, column=1, sticky="nsew", padx=8, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        listbox = tk.Listbox(list_frame, height=7, selectmode="extended")
        listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=scrollbar.set)

        controls = ttk.Frame(parent)
        controls.grid(row=row, column=2, sticky="n", pady=5)
        ttk.Button(controls, text="追加...", command=add_command).pack(fill="x")
        ttk.Button(controls, text="クリア", command=clear_command).pack(fill="x", pady=(5, 0))
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)
        return listbox

    def _add_files(self, target, listbox, filetype_label, extension):
        selected = filedialog.askopenfilenames(
            title=f"{filetype_label}ファイルを選択",
            filetypes=[(filetype_label, f"*{extension}"), ("すべてのファイル", "*.*")],
        )
        for selected_path in selected:
            path = Path(selected_path)
            if path not in target:
                target.append(path)
                listbox.insert("end", str(path))

    @staticmethod
    def _clear_files(target, listbox):
        target.clear()
        listbox.delete(0, "end")

    def _build_extract_tab(self):
        frame = ttk.Frame(self.tabs, padding=16)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tabs.add(frame, text="JSONからCSV抽出")
        self.json_list = self._file_list(
            frame, 0, "JSONファイル",
            lambda: self._add_files(self.json_files, self.json_list, "JSON", ".json"),
            lambda: self._clear_files(self.json_files, self.json_list),
        )
        self.extract_output = tk.StringVar(
            value=str(Path(__file__).resolve().parent / "extracted")
        )
        self._add_path_row(
            frame, 1, "出力フォルダー", self.extract_output,
            lambda: self._directory_dialog(self.extract_output),
        )
        button = ttk.Button(frame, text="選択したJSONファイルを抽出", command=self._extract)
        button.grid(row=2, column=1, sticky="e", pady=(12, 0))
        self.action_buttons.append(button)

    def _build_format_tab(self):
        frame = ttk.Frame(self.tabs, padding=16)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tabs.add(frame, text="CSVをTXTに変換")
        self.csv_list = self._file_list(
            frame, 0, "CSVファイル",
            lambda: self._add_files(self.csv_files, self.csv_list, "CSV", ".csv"),
            lambda: self._clear_files(self.csv_files, self.csv_list),
        )
        self.save_combined = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="結合したTXTファイルも保存",
            variable=self.save_combined,
        ).grid(row=1, column=1, sticky="w", pady=5)
        self.combined_output = tk.StringVar(
            value=str(Path(__file__).resolve().parent / "combined.txt")
        )
        self._add_path_row(
            frame, 2, "結合TXTの保存先", self.combined_output,
            lambda: self._file_dialog(
                self.combined_output,
                "結合TXTファイルを保存",
                [("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            ),
        )
        button = ttk.Button(frame, text="選択したCSVファイルを変換", command=self._format)
        button.grid(row=3, column=1, sticky="e", pady=(12, 0))
        self.action_buttons.append(button)

    def _build_search_tab(self):
        frame = ttk.Frame(self.tabs, padding=16)
        frame.columnconfigure(1, weight=1)
        self.tabs.add(frame, text="TXTを検索")
        self.search_folder = tk.StringVar(
            value=str(Path(__file__).resolve().parent / "exported")
        )
        self.search_text = tk.StringVar()
        self.search_by = tk.StringVar()
        self._add_path_row(
            frame, 0, "検索フォルダー", self.search_folder,
            lambda: self._directory_dialog(self.search_folder),
        )
        ttk.Label(frame, text="人物").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.search_by).grid(
            row=1, column=1, sticky="ew", padx=8, pady=5
        )
        ttk.Label(frame, text="文章").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.search_text).grid(
            row=2, column=1, sticky="ew", padx=8, pady=5
        )
        ttk.Label(
            frame,
            text="どちらか一方、または両方を入力してください。検索結果は下に表示されます。",
        ).grid(row=3, column=1, sticky="w", pady=(6, 0))
        button = ttk.Button(frame, text="検索", command=self._search)
        button.grid(row=4, column=1, sticky="e", pady=(12, 0))
        self.action_buttons.append(button)

    def _start_task(self, label, task, clear_activity=False):
        if clear_activity:
            self.activity.configure(state="normal")
            self.activity.delete("1.0", "end")
            self.activity.configure(state="disabled")
        self.status.set(f"{label}中...")
        for button in self.action_buttons:
            button.configure(state="disabled")

        def log(message):
            self.messages.put(("log", str(message)))

        def run():
            try:
                task(log)
            except Exception as error:
                self.messages.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                self.messages.put(("done", label))

        threading.Thread(target=run, daemon=True).start()

    def _process_messages(self):
        try:
            while True:
                kind, message = self.messages.get_nowait()
                if kind in ("log", "error"):
                    self.activity.configure(state="normal")
                    prefix = "エラー: " if kind == "error" else ""
                    self.activity.insert("end", f"{prefix}{message}\n")
                    self.activity.see("end")
                    self.activity.configure(state="disabled")
                    if kind == "error":
                        self.status.set("失敗")
                        messagebox.showerror("処理に失敗しました", message, parent=self)
                elif kind == "done":
                    for button in self.action_buttons:
                        button.configure(state="normal")
                    if self.status.get() != "失敗":
                        self.status.set(f"{message}完了")
        except queue.Empty:
            pass
        self.after(100, self._process_messages)

    def _export_all(self):
        input_dir = Path(self.export_input.get())
        output_dir = Path(self.export_output.get())
        self._start_task(
            "一括出力",
            lambda log: export_all.export_directory(
                input_dir, output_dir, progress_callback=log
            ),
        )

    def _extract(self):
        if not self.json_files:
            messagebox.showwarning("ファイル未選択", "JSONファイルを1つ以上追加してください。", parent=self)
            return
        files = list(self.json_files)
        output_dir = Path(self.extract_output.get())

        def task(log):
            output_paths = [
                extractor.get_output_path(file, output_dir / file.with_suffix(".csv").name)
                for file in files
            ]
            output_paths = extractor.make_output_paths_unique(output_paths)
            output_dir.mkdir(parents=True, exist_ok=True)
            for file, output_path in zip(files, output_paths):
                extractor.save_csv(file, output_path, on_saved=log)

        self._start_task("CSV抽出", task)

    def _format(self):
        if not self.csv_files:
            messagebox.showwarning("ファイル未選択", "CSVファイルを1つ以上追加してください。", parent=self)
            return
        files = list(self.csv_files)
        save_combined = self.save_combined.get()
        combined_output = Path(self.combined_output.get())

        def task(log):
            combined_rows = []
            for file in files:
                output_path, rows = formatter.format_csv(file)
                combined_rows.extend(rows)
                log(f"保存しました: {output_path}")
            if save_combined:
                log(f"保存しました: {formatter.save_combined(combined_rows, combined_output)}")

        self._start_task("CSV変換", task)

    def _search(self):
        text = self.search_text.get() or None
        by_text = self.search_by.get() or None
        if text is None and by_text is None:
            messagebox.showwarning(
                "検索文字列が必要です",
                "文章または人物を入力してください。両方の指定もできます。",
                parent=self,
            )
            return

        parent_dir = Path(self.search_folder.get())

        def task(log):
            matches = 0
            for result in search.iter_matches(parent_dir, text, by_text):
                log(result)
                matches += 1
            if matches == 0:
                log("一致する結果はありません。")

        self._start_task("検索", task, clear_activity=True)


def main():
    app = StoryToolsApp()
    app.mainloop()


if __name__ == "__main__":
    main()