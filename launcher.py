import tkinter as tk
from tkinter import filedialog, messagebox
import threading, os, sys
from reporting.main_logic import validate_excel
import matplotlib
os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), "mpl_cache")
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.use("Agg")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ReportApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Data Monitoring Report Builder")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        self.visit_files = []
        self.prev_file = []
        self.build_ui()

    def build_ui(self):

        tk.Label(
            self.root,
            text="Data Monitoring Excel Report Generator",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        self.status_label = tk.Label(
            self.root,
            text="Select required files to begin.",
            fg="blue"
        )
        self.status_label.pack(pady=3)

        tk.Button(
            self.root,
            text="Select Visit Files",
            width=20,
            command=self.select_visit_files
        ).pack(pady=3)

        tk.Button(
            self.root,
            text="Select Previous Report File",
            width=20,
            command=self.select_prev_files
        ).pack(pady=3)

        tk.Button(
            self.root,
            text="Generate Report",
            width=20,
            command=self.run_validation
        ).pack(pady=5)

    def select_visit_files(self):
        self.visit_files = filedialog.askopenfilenames(
            title="Select Visit Files",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )

        if not self.visit_files:
            self.status_label.config(text="No files selected.", fg="red")
            return

        self.status_label.config(
            text=f"{len(self.visit_files)} visit & {len(self.prev_file)} report files selected.",
            fg="green"
        )

    def select_prev_files(self):
        self.prev_file = filedialog.askopenfilenames(
            title="Select Validation, Notes, and Visit Files",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )

        if not self.prev_file:
            self.status_label.config(text="No files selected.", fg="red")
            return

        self.status_label.config(
            text=f"{len(self.visit_files)} visit & {len(self.prev_file)} report files selected.",
            fg="green"
        )

    def validate_selection(self):
        notes_file = resource_path("resources/Variables_Notes.xlsx")
        notes_files = [notes_file]
        visit_files = [
            f for f in self.visit_files
            if f not in notes_files
        ]
        prev_files = [f for f in self.prev_file]

        if len(prev_files) != 1:
            raise ValueError("Please select exactly ONE Validation file.")

        if len(notes_files) != 1:
            raise ValueError("Please select exactly ONE Variables_Notes file.")

        if len(visit_files) == 0:
            raise ValueError("Please select at least one Visit file.")

        return visit_files, prev_files[0], notes_files[0]

    def run_validation(self):

        if not self.visit_files:
            messagebox.showerror("Error", "Please select visit files first.")
            return

        if not self.prev_file:
            messagebox.showerror("Error", "Please select previous file first.")
            return

        try:
            visit_files, prev_file, info_file = self.validate_selection()
        except ValueError as e:
            messagebox.showerror("File Selection Error", str(e))
            return

        save_path = self.choose_save_location()
        if not save_path:
            # User cancelled
            self.update_status("Save cancelled.", "orange")
            return

        # Run in separate thread so GUI doesn't freeze
        thread = threading.Thread(
            target=self.process_report,
            args=(visit_files, prev_file, info_file, save_path)
        )
        thread.start()

    def process_report(self, visit_files, previous_file, info_file, save_path):

        try:
            self.update_status("Generating report...", "blue")

            validate_excel(visit_files, previous_file, info_file, save_path)

            self.update_status("Report generated successfully.", "green")

            messagebox.showinfo(
                "Success",
                f"Report saved to:\n{save_path}"
            )

        except Exception as e:
            self.update_status("Error occurred.", "red")
            messagebox.showerror("Processing Error", str(e))

    def update_status(self, text, color):
        self.status_label.config(text=text, fg=color)

    def choose_save_location(self):
        save_path = filedialog.asksaveasfilename(
            title="Save Report As",
            defaultextension=".xlsx",
            filetypes=[("Excel File", "*.xlsx")],
            initialfile="Data_Monitoring_Report.xlsx"
        )
        return save_path

if __name__ == "__main__":
    root = tk.Tk()
    app = ReportApp(root)
    root.mainloop()
