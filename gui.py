import os
import sys
import json
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class PipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Augmented Investment Pipeline Assessor")
        self.root.geometry("750x700")
        self.root.minsize(650, 600)
        
        # Center the window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
        self.log_queue = queue.Queue()
        self.active_process = None
        self.run_thread = None
        
        self.setup_styles()
        self.create_widgets()
        
        # Start checking the log queue
        self.root.after(100, self.check_queue)
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('vista' if os.name == 'nt' else 'clam')
        
        # Custom frame and label configurations
        self.style.configure("TFrame", background="#f5f5f7")
        self.style.configure("TLabel", background="#f5f5f7", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1d1d1f")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"))
        
        # Button styles
        self.style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), foreground="#0071e3")
        self.style.configure("Secondary.TButton", font=("Segoe UI", 10))
        
        self.root.configure(background="#f5f5f7")
        
    def create_widgets(self):
        # Main Container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="AI-Augmented Investment Pipeline Assessor", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Input Section Frame
        inputs_frame = ttk.LabelFrame(main_frame, text=" Pipeline Parameters ", padding="15")
        inputs_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Grid Configuration for Inputs
        inputs_frame.columnconfigure(1, weight=1)
        
        # Topic
        ttk.Label(inputs_frame, text="Topic Query:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.topic_var = tk.StringVar(value="AI agents for SMBs")
        self.topic_entry = ttk.Entry(inputs_frame, textvariable=self.topic_var, font=("Segoe UI", 10))
        self.topic_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=5)
        
        # Count Spinner (Max 15)
        ttk.Label(inputs_frame, text="Startup Count (Max 15):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.count_var = tk.IntVar(value=5)
        self.count_spinner = ttk.Spinbox(inputs_frame, from_=1, to=15, textvariable=self.count_var, width=10, font=("Segoe UI", 10))
        self.count_spinner.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Min Points
        ttk.Label(inputs_frame, text="Min HN Points:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(15, 10))
        self.min_pts_var = tk.IntVar(value=10)
        self.min_pts_spinner = ttk.Spinbox(inputs_frame, from_=0, to=1000, textvariable=self.min_pts_var, width=10, font=("Segoe UI", 10))
        self.min_pts_spinner.grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # API Keys Frame (Optional runtime override)
        keys_frame = ttk.LabelFrame(main_frame, text=" API Credentials (Optional) ", padding="15")
        keys_frame.pack(fill=tk.X, pady=(0, 15))
        keys_frame.columnconfigure(1, weight=1)
        
        # OpenAI Key
        ttk.Label(keys_frame, text="OpenAI API Key:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.openai_key_var = tk.StringVar()
        self.openai_key_entry = ttk.Entry(keys_frame, textvariable=self.openai_key_var, show="*", font=("Segoe UI", 10))
        self.openai_key_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # Gemini Key
        ttk.Label(keys_frame, text="Gemini API Key:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.gemini_key_var = tk.StringVar()
        self.gemini_key_entry = ttk.Entry(keys_frame, textvariable=self.gemini_key_var, show="*", font=("Segoe UI", 10))
        self.gemini_key_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # Security Notice
        notice_label = ttk.Label(
            keys_frame, 
            text="* Note: API keys provided here are held in memory only for this session and will not be saved to disk. If left blank, keys are read from your local .env file.", 
            foreground="#636366",
            font=("Segoe UI", 8, "italic")
        )
        notice_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Action Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons
        self.btn_dry_run = ttk.Button(btn_frame, text="Test Connection (Dry Run)", command=self.start_dry_run, style="Secondary.TButton")
        self.btn_dry_run.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_run = ttk.Button(btn_frame, text="Run Full Pipeline", command=self.start_pipeline_run, style="Run.TButton")
        self.btn_run.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_open_folder = ttk.Button(btn_frame, text="Open Outputs Folder", command=self.open_outputs_folder, style="Secondary.TButton")
        self.btn_open_folder.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_clear_cache = ttk.Button(btn_frame, text="Clear Cache", command=self.clear_cache, style="Secondary.TButton")
        self.btn_clear_cache.pack(side=tk.RIGHT)
        
        # Log Panel Frame
        log_frame = ttk.LabelFrame(main_frame, text=" Live Execution Logs ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrolled Text Box for Logs (Terminal Look)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            background="#1e1e1e", 
            foreground="#d4d4d4", 
            insertbackground="white",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))

    def write_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def set_running_state(self, running=True):
        state = tk.DISABLED if running else tk.NORMAL
        self.btn_run.config(state=state)
        self.btn_dry_run.config(state=state)
        self.btn_clear_cache.config(state=state)
        self.topic_entry.config(state=state)
        self.count_spinner.config(state=state)
        self.min_pts_spinner.config(state=state)
        self.openai_key_entry.config(state=state)
        self.gemini_key_entry.config(state=state)

    def start_dry_run(self):
        self.run_pipeline_subprocess(dry_run=True)

    def start_pipeline_run(self):
        self.run_pipeline_subprocess(dry_run=False)

    def run_pipeline_subprocess(self, dry_run=False):
        topic = self.topic_var.get().strip()
        count = self.count_var.get()
        min_pts = self.min_pts_var.get()
        
        gui_openai_key = self.openai_key_var.get().strip()
        gui_gemini_key = self.gemini_key_var.get().strip()
        
        if not topic:
            messagebox.showerror("Validation Error", "Please enter a topic query.")
            return
            
        if count > 15:
            messagebox.showwarning("Count Limited", "For safety, the maximum count has been restricted to 15 startups.")
            self.count_var.set(15)
            count = 15
            
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.set_running_state(True)
        
        cmd = [sys.executable, "pipeline.py", "--topic", topic, "--count", str(count), "--min-pts", str(min_pts)]
        if dry_run:
            cmd.append("--dry-run")
            self.status_var.set("Running Dry Run Sourcing Test...")
            self.write_log("Starting Sourcing connection test (Dry Run)...\n")
        else:
            self.status_var.set("Running Full Pipeline (Sourcing -> Scraping -> LLM Analysis)...")
            self.write_log("Launching Full Investment Pipeline...\n")
            
        # Launch thread to read subprocess stdout in background
        self.run_thread = threading.Thread(
            target=self.subprocess_runner_thread, 
            args=(cmd, gui_openai_key, gui_gemini_key),
            daemon=True
        )
        self.run_thread.start()

    def subprocess_runner_thread(self, cmd, gui_openai_key, gui_gemini_key):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Set up the environment passing any GUI-pasted keys
            env = os.environ.copy()
            if gui_openai_key:
                env["OPENAI_API_KEY"] = gui_openai_key
            if gui_gemini_key:
                env["GEMINI_API_KEY"] = gui_gemini_key

            self.active_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo,
                env=env
            )
            
            for line in iter(self.active_process.stdout.readline, ""):
                self.log_queue.put(line)
                
            self.active_process.stdout.close()
            return_code = self.active_process.wait()
            self.log_queue.put(("EXIT_CODE", return_code))
        except Exception as e:
            self.log_queue.put(f"System Error starting pipeline: {str(e)}\n")
            self.log_queue.put(("EXIT_CODE", -1))

    def check_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "EXIT_CODE":
                    exit_code = item[1]
                    self.set_running_state(False)
                    self.active_process = None
                    if exit_code == 0:
                        self.status_var.set("Pipeline Completed Successfully")
                        self.write_log("\n[Pipeline Completed Successfully]\n")
                    else:
                        self.status_var.set(f"Pipeline Failed (Exit Code: {exit_code})")
                        self.write_log(f"\n[Pipeline Exited with Code {exit_code}. Check errors.log for details.]\n")
                else:
                    self.write_log(item)
                self.log_queue.task_done()
        except queue.Empty:
            pass
        
        # Schedule next queue check
        self.root.after(100, self.check_queue)

    def open_outputs_folder(self):
        output_dir = os.path.abspath("./outputs")
        os.makedirs(output_dir, exist_ok=True)
        try:
            if os.name == 'nt':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', output_dir])
            else:
                subprocess.Popen(['xdg-open', output_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def clear_cache(self):
        cache_path = os.path.abspath("./data/2_analyzed.json")
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete("1.0", tk.END)
                self.log_text.config(state=tk.DISABLED)
                self.write_log("Cached analyzed results cleared (data/2_analyzed.json removed).\n")
                self.status_var.set("Cache Cleared")
                messagebox.showinfo("Success", "Analysis cache cleared successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cache: {e}")
        else:
            messagebox.showinfo("Cache Empty", "No analysis cache found to clear.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PipelineGUI(root)
    root.mainloop()
