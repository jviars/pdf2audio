import PyPDF2
import pyttsx3
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk
import threading
import time


# Just a basic project used to get better at Python. As always, feel free to do what you'd like with this.

class PDFAudioBookConverter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("PDF to AudioBook Converter")
        self.window.geometry("600x400")
        
        # Initialize TTS engine
        self.engine = pyttsx3.init()
        
        # Configure voice settings
        self.engine.setProperty('rate', 150)    # Speaking rate
        self.engine.setProperty('volume', 0.9)  # Volume (0-1)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        ttk.Label(main_frame, text="Select PDF File:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path, width=50).grid(row=1, column=0, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=1, column=1)
        
        # Voice settings
        ttk.Label(main_frame, text="Voice Settings:").grid(row=2, column=0, sticky=tk.W, pady=(20,5))
        
        # Speed control
        ttk.Label(main_frame, text="Speed:").grid(row=3, column=0, sticky=tk.W)
        self.speed_var = tk.IntVar(value=150)
        speed_scale = ttk.Scale(main_frame, from_=50, to=300, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # Volume control
        ttk.Label(main_frame, text="Volume:").grid(row=5, column=0, sticky=tk.W)
        self.volume_var = tk.DoubleVar(value=0.9)
        volume_scale = ttk.Scale(main_frame, from_=0, to=1, variable=self.volume_var, orient=tk.HORIZONTAL)
        volume_scale.grid(row=6, column=0, sticky=(tk.W, tk.E))
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=8, column=0, sticky=tk.W)
        
        # Detailed status label
        self.detailed_status_var = tk.StringVar(value="")
        ttk.Label(main_frame, textvariable=self.detailed_status_var).grid(row=9, column=0, sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save Audio", command=self.save_audio, state=tk.DISABLED)
        self.save_button.grid(row=0, column=2, padx=5)
        
        # Initialize conversion state
        self.is_converting = False
        self.current_text = ""
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            
    def extract_text(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = []
                total_pages = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    if not self.is_converting:
                        return None
                    page_text = page.extract_text()
                    text.append(page_text)
                    progress = ((i + 1) / total_pages) * 30  # First 30% of progress
                    self.progress_var.set(progress)
                    self.status_var.set(f"Extracting text")
                    self.detailed_status_var.set(f"Page {i+1}/{total_pages}")
                    self.window.update()
                
                return text
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            return None
            
    def start_conversion(self):
        if not self.file_path.get():
            self.status_var.set("Please select a PDF file first")
            return
            
        self.is_converting = True
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.save_button.configure(state=tk.DISABLED)
        
        # Start conversion in a separate thread
        threading.Thread(target=self.convert_pdf_to_audio, daemon=True).start()
        
    def convert_pdf_to_audio(self):
        # Update engine properties based on current settings
        self.engine.setProperty('rate', self.speed_var.get())
        self.engine.setProperty('volume', self.volume_var.get())
        
        # Extract text
        pages = self.extract_text(self.file_path.get())
        if pages:
            self.current_text = "\n".join(pages)
            total_pages = len(pages)
            
            try:
                # Convert to speech page by page
                for i, page_text in enumerate(pages):
                    if not self.is_converting:
                        break
                        
                    self.status_var.set("Converting to speech")
                    self.detailed_status_var.set(f"Processing page {i+1}/{total_pages}")
                    
                    # Calculate progress (30-100%)
                    progress = 30 + ((i + 1) / total_pages) * 70
                    self.progress_var.set(progress)
                    
                    # Convert page to speech
                    self.engine.say(page_text)
                    self.engine.runAndWait()
                    
                    # Update UI
                    self.window.update()
                
                if self.is_converting:
                    self.progress_var.set(100)
                    self.status_var.set("Conversion completed!")
                    self.detailed_status_var.set(f"Processed {total_pages} pages")
                    self.save_button.configure(state=tk.NORMAL)
            except Exception as e:
                self.status_var.set(f"Error during conversion: {str(e)}")
                self.detailed_status_var.set("An error occurred")
        
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.is_converting = False
        
    def stop_conversion(self):
        self.is_converting = False
        self.engine.stop()
        self.status_var.set("Conversion stopped")
        self.detailed_status_var.set("Stopped by user")
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        
    def save_audio(self):
        if not self.current_text:
            self.status_var.set("No audio to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("Saving audio file...")
                self.detailed_status_var.set("Please wait...")
                self.engine.save_to_file(self.current_text, filename)
                self.engine.runAndWait()
                self.status_var.set("Audio file saved successfully!")
                self.detailed_status_var.set(f"Saved to: {filename}")
            except Exception as e:
                self.status_var.set(f"Error saving audio: {str(e)}")
                self.detailed_status_var.set("Failed to save audio file")
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = PDFAudioBookConverter()
    app.run()
