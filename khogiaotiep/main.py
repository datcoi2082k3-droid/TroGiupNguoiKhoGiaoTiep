import customtkinter
from gtts import gTTS
import os
import threading
import json
import time
import asyncio
import tempfile
import ctypes
import re
import math
import logging
from PIL import Image, ImageTk
from ai_service import AIService
from tkinter import filedialog

class CommunicationApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Stellar Clarity v9.0 [WIDE-CARD ARCHITECTURE] ---
        self.title("UNIBOT SUPER PREMIUM - VI/EN DUAL-SYSTEM")
        
        # Geometry Strategy
        self.geometry("1850x1050")
        self.after(0, lambda: self.state('zoomed'))
        customtkinter.set_appearance_mode("dark")
        
        # --- Premium Design Tokens ---
        self.COLORS = {
            "BG": "#05070a",
            "SIDEBAR": "#0a0c14",
            "CARD": "#111420",
            "ACCENT": "#818cf8",
            "DIVIDER": "#1e293b",
            "TEXT": "#f8fafc",
            "TEXT_MUTED": "#94a3b8",
            "LOG_COLOR": "#34d399",
            "MODE_COLORS": {
                "STANDARD": "#6366f1",
                "KIDS": "#f43f5e",
                "ELDERLY": "#10b981",
                "MEDICAL": "#e11d48"
            }
        }
        
        self.current_mode = "STANDARD"
        self.current_lang = "VI"
        self.glow_color = self.COLORS["MODE_COLORS"]["STANDARD"]
        self.data_file = "data.json"
        self.categories = self.load_data()
        self.mci = ctypes.windll.winmm.mciSendStringW
        self.audio_lock = threading.Lock()
        
        self.is_speaking = False
        self.frame_count = 0
        self.gesture_queue = []
        
        # --- Advanced Robot Engine ---
        self.source_images = {}
        self.current_pose = "resting"
        self.target_pose = "resting"
        self.transition_alpha = 1.0
        self.transition_step = 0.25
        self.prev_img_pil = None
        self.target_img_pil = None
        self.translation_cache = {}
        self.status_text = "Initializing AI Engine..."
        
        # Discover model BEFORE UI setup to avoid reference errors
        AIService.discover_model()
        
        self.setup_geometric_ui()
        self.load_all_assets()
        self.animate_loop()

    def setup_geometric_ui(self):
        self.configure(fg_color=self.COLORS["BG"])
        
        # Root Layout weights
        self.grid_columnconfigure(0, weight=0) # Sidebar Fixed
        self.grid_columnconfigure(1, weight=1) # Main Area Expansive
        self.grid_rowconfigure(0, weight=1)

        # 1. --- ARCHITECTURAL SIDEBAR ---
        self.sidebar = customtkinter.CTkFrame(self, width=280, fg_color=self.COLORS["SIDEBAR"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        branding = customtkinter.CTkFrame(self.sidebar, fg_color="transparent")
        branding.pack(pady=(40, 50))
        customtkinter.CTkLabel(branding, text="UNIBOT", text_color=self.COLORS["ACCENT"], font=customtkinter.CTkFont(size=34, weight="bold")).pack()
        customtkinter.CTkLabel(branding, text="CLARITY ENGINE v9.0", text_color=self.COLORS["TEXT_MUTED"], font=customtkinter.CTkFont(size=11, weight="bold")).pack()

        self.add_nav_label("USER MODES")
        self.mode_btns = {}
        for m, txt in [("STANDARD", "🏠 Tổng quan"), ("KIDS", "🎨 Trẻ em"), ("ELDERLY", "👓 Người già"), ("MEDICAL", "🏥 Y tế")]:
            b = customtkinter.CTkButton(self.sidebar, text=txt, height=60, anchor="w", font=customtkinter.CTkFont(size=15, weight="bold"), fg_color="transparent", text_color=self.COLORS["TEXT_MUTED"], hover_color="#1e1b4b", corner_radius=15, command=lambda m=m: self.change_mode(m))
            b.pack(fill="x", padx=15, pady=3)
            self.mode_btns[m] = b

        self.add_nav_label("SYSTEM LANGUAGES")
        self.lang_btns = {}
        for l, txt in [("VI", "🇻🇳 Tiếng Việt"), ("EN", "🇺🇸 English")]:
            b = customtkinter.CTkButton(self.sidebar, text=txt, height=60, anchor="w", font=customtkinter.CTkFont(size=14, weight="bold"), fg_color="transparent", text_color=self.COLORS["TEXT_MUTED"], hover_color="#064e3b", corner_radius=15, command=lambda l=l: self.change_lang(l))
            b.pack(fill="x", padx=15, pady=3)
            self.lang_btns[l] = b
        
        self.mode_btns["STANDARD"].configure(fg_color=self.COLORS["ACCENT"], text_color=self.COLORS["TEXT"])
        self.lang_btns["VI"].configure(fg_color="#0d9488", text_color=self.COLORS["TEXT"])

        # 2. --- DASHBOARD (ABSOLUTE 50/50 SPLIT) ---
        self.dashboard = customtkinter.CTkFrame(self, fg_color="transparent")
        self.dashboard.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # FORCING UNIFORMITY
        self.dashboard.grid_columnconfigure(0, weight=1, uniform="main_split") 
        self.dashboard.grid_columnconfigure(1, weight=1, uniform="main_split") 
        self.dashboard.grid_rowconfigure(0, weight=1)

        # --- LEFT: THE ROBOT HERO ---
        self.hero_container = customtkinter.CTkFrame(self.dashboard, fg_color="transparent")
        self.hero_container.grid(row=0, column=0, sticky="nsew")
        
        self.glow_canvas = customtkinter.CTkCanvas(self.hero_container, bg=self.COLORS["BG"], highlightthickness=0)
        self.glow_canvas.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
        
        self.avatar_label = customtkinter.CTkLabel(self.hero_container, text="")
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # Visual Divider
        customtkinter.CTkFrame(self.dashboard, width=1, fg_color=self.COLORS["DIVIDER"]).grid(row=0, column=0, sticky="nse")

        # --- RIGHT: THE COMMAND CENTER ---
        self.stack = customtkinter.CTkFrame(self.dashboard, fg_color="transparent")
        self.stack.grid(row=0, column=1, sticky="nsew", padx=(30, 0))
        self.stack.grid_rowconfigure(2, weight=1) # AAC Board fills the gap
        self.stack.grid_rowconfigure((0, 1, 3), weight=0)

        # AI Input Card
        self.input_card = customtkinter.CTkFrame(self.stack, fg_color=self.COLORS["CARD"], corner_radius=35, border_width=1, border_color="#1e293b")
        self.input_card.grid(row=0, column=0, sticky="ew", pady=(0, 25))
        
        self.entry = customtkinter.CTkTextbox(self.input_card, font=customtkinter.CTkFont(size=22), height=150, fg_color="#010307", text_color=self.COLORS["TEXT"], border_width=0, corner_radius=25)
        self.entry.pack(fill="both", expand=True, padx=30, pady=(30, 25))
        self.entry.bind("<<Modified>>", self.on_text_modified)
        
        btns = customtkinter.CTkFrame(self.input_card, fg_color="transparent")
        btns.pack(fill="x", padx=30, pady=(0, 30))
        self.btn_speak = customtkinter.CTkButton(btns, text="🔊 PHÁT ÂM NGAY", font=customtkinter.CTkFont(size=18, weight="bold"), height=70, fg_color=self.COLORS["ACCENT"], corner_radius=25, command=self.on_speak_click)
        self.btn_speak.pack(side="left", expand=True, fill="x", padx=(0, 15))
        self.btn_scan = customtkinter.CTkButton(btns, text="📸 QUÉT", width=120, font=customtkinter.CTkFont(size=16, weight="bold"), height=70, fg_color="#10b981", corner_radius=25, command=self.scan_logic)
        self.btn_scan.pack(side="right")

        # Prediction HUD (Dynamic Show/Hide)
        self.prediction_hud = customtkinter.CTkFrame(self.stack, fg_color=self.COLORS["CARD"], height=65, corner_radius=25, border_width=1, border_color="#1e293b")
        self.prediction_hud.grid_propagate(False) # Keep it solid
        
        self.chip_bar = customtkinter.CTkFrame(self.prediction_hud, fg_color="transparent")
        self.chip_bar.pack(fill="both", expand=True, padx=25, pady=5)
        self.prediction_chips = []

        # AAC Board Card
        self.board_card = customtkinter.CTkFrame(self.stack, fg_color=self.COLORS["CARD"], corner_radius=35, border_width=1, border_color="#1e293b")
        self.board_card.grid(row=2, column=0, sticky="nsew")
        self.tabs = customtkinter.CTkTabview(self.board_card, fg_color="transparent", segmented_button_selected_color=self.COLORS["ACCENT"], command=self.on_tab_change)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=15)
        
        # SOS Override
        self.btn_sos = customtkinter.CTkButton(self.stack, text="🚨 SOS EMERGENCY OVERRIDE", font=customtkinter.CTkFont(size=18, weight="bold"), height=75, fg_color="#e11d48", hover_color="#991b1b", corner_radius=25, command=lambda: self.speak_phrase("TÔI CẦN GIÚP ĐỠ KHẨN CẤP!"))
        self.btn_sos.grid(row=3, column=0, sticky="ew", pady=(25, 0))

        # --- 3. STATUS BAR (PREMIUM HUD) ---
        self.status_bar = customtkinter.CTkFrame(self, height=45, fg_color=self.COLORS["SIDEBAR"])
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        status_container = customtkinter.CTkFrame(self.status_bar, fg_color="transparent")
        status_container.pack(fill="both", expand=True)
        
        self.status_lbl = customtkinter.CTkLabel(status_container, text=f" ●  {self.status_text}", font=customtkinter.CTkFont(size=12, weight="bold"), text_color=self.COLORS["LOG_COLOR"])
        self.status_lbl.pack(side="left", padx=20)
        
        # Display active AI Model name for professional transparency
        self.model_lbl = customtkinter.CTkLabel(status_container, text=f"ENGINE: {getattr(AIService, 'MODEL_ID', 'CONNECTING...')}", font=customtkinter.CTkFont(size=10, weight="bold"), text_color=self.COLORS["TEXT_MUTED"])
        self.model_lbl.pack(side="right", padx=20)

        self.refresh_ui()

    def add_nav_label(self, text):
        lbl = customtkinter.CTkLabel(self.sidebar, text=text, font=customtkinter.CTkFont(size=11, weight="bold"), text_color="#1e293b")
        lbl.pack(fill="x", padx=25, pady=(25, 5), anchor="w")

    def change_mode(self, mode):
        for k, btn in self.mode_btns.items():
            btn.configure(fg_color="transparent", text_color=self.COLORS["TEXT_MUTED"])
        self.mode_btns[mode].configure(fg_color=self.COLORS["ACCENT"], text_color=self.COLORS["TEXT"])
        self.current_mode, self.glow_color = mode, self.COLORS["MODE_COLORS"].get(mode, self.COLORS["ACCENT"])
        self.refresh_ui()

    def change_lang(self, lang):
        for k, btn in self.lang_btns.items():
            btn.configure(fg_color="transparent", text_color=self.COLORS["TEXT_MUTED"])
        self.lang_btns[lang].configure(fg_color="#0d9488", text_color=self.COLORS["TEXT"])
        self.current_lang = lang
        self.update_status(f"Switching language to {lang}...", "#6366f1")
        threading.Thread(target=self.refresh_ui, daemon=True).start()

    def on_tab_change(self):
        tab = self.tabs.get()
        mapping = {"CƠ BẢN": "#6366f1", "THIẾT YẾU": "#10b981", "Y TẾ": "#e11d48", "CẢM XÚC": "#8b5cf6"}
        for k, v in mapping.items():
            if k in tab: self.glow_color = v

    def update_status(self, text, color=None):
        self.status_text = text
        self.after(0, lambda: self.status_lbl.configure(text=f" ●  {text}", text_color=color if color else self.COLORS["LOG_COLOR"]))

    def refresh_ui(self):
        # Premium Batch Translation Strategy
        local_categories = self.categories.copy()
        
        if self.current_lang != "VI":
            self.update_status(f"AI: Translating board to {self.current_lang}...", "#f59e0b")
            # Create a simple list of phrases to translate in batch
            batch_data = {"cats": list(local_categories.keys())}
            for cat, items in local_categories.items():
                batch_data[cat] = [i["phrase"] for i in items]
            
            translated_batch = AIService.translate_batch(batch_data, self.current_lang)
            
            # Map back to a new categories dict
            new_cats = {}
            translated_cat_names = translated_batch.get("cats", [])
            for i, (orig_cat, items) in enumerate(local_categories.items()):
                new_cat_name = translated_cat_names[i] if i < len(translated_cat_names) else orig_cat
                new_items = []
                translated_phrases = translated_batch.get(orig_cat, [])
                for j, item in enumerate(items):
                    new_phrase = translated_phrases[j] if j < len(translated_phrases) else item["phrase"]
                    new_items.append({"phrase": new_phrase, "icon": item["icon"]})
                new_cats[new_cat_name] = new_items
            local_categories = new_cats

        self.after(0, lambda: self._build_tabs(local_categories))

    def _build_tabs(self, local_categories):
        for tab in list(self.tabs._segmented_button._buttons_dict.keys()):
            try: self.tabs.delete(tab)
            except: pass
            
        for cat, items in local_categories.items():
            self.tabs.add(cat)
            scroll = customtkinter.CTkScrollableFrame(self.tabs.tab(cat), fg_color="transparent")
            scroll.pack(fill="both", expand=True)
            scroll.grid_columnconfigure((0, 1), weight=1) 
            
            for r, item in enumerate(items):
                phrase, icon = item["phrase"], item["icon"]
                # Pass translate=False because the phrase is already in the target language
                btn = customtkinter.CTkButton(scroll, text=f" {icon}   {phrase}", anchor="w", font=customtkinter.CTkFont(size=12, weight="bold"), height=70, fg_color="#181a25", border_width=1, border_color="#1e293b", hover_color=self.COLORS["ACCENT"], corner_radius=18, command=lambda p=phrase: self.speak_phrase(p, translate=False))
                btn.grid(row=r//2, column=r%2, padx=12, pady=10, sticky="nsew")
        self.update_status("AI Engine Online | System Ready", self.COLORS["LOG_COLOR"])

    # --- Logic ---
    def scan_logic(self):
        p = filedialog.askopenfilename()
        if p: threading.Thread(target=self._logic_scan_async, args=(p,), daemon=True).start()

    def _logic_scan_async(self, path):
        res = AIService.describe_object_intent(path, self.current_lang)
        self.after(0, lambda: self._logic_scan_done(res))

    def _logic_scan_done(self, text):
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", text)
        self.speak_phrase(text)

    def load_all_assets(self):
        for icon in ["resting", "speaking", "wave", "thanks", "thinking", "point", "heart", "sad", "eat"]:
            f = f"avatar{'' if icon=='resting' else '_'+icon}.png"
            if os.path.exists(f): self.source_images[icon] = Image.open(f).convert("RGBA")
        self.prev_img_pil = self.source_images.get("resting")
        self.target_img_pil = self.source_images.get("resting")

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f: return json.load(f)
        return {}

    def on_text_modified(self, event=None):
        if self.entry.edit_modified():
            t = self.entry.get("1.0", "end-1c").strip()
            if len(t) > 2: threading.Thread(target=self._logic_ai, args=(t,), daemon=True).start()
            self.entry.edit_modified(False)

    def _logic_ai(self, text):
        preds = AIService.get_contextual_prediction(text, self.current_lang)
        if preds: self.after(0, lambda: self.update_chips(preds))

    def update_chips(self, preds):
        for c in self.prediction_chips: c.destroy()
        self.prediction_chips = []
        if not preds:
            self.prediction_hud.grid_remove()
            return
        self.prediction_hud.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        for p in preds:
            c = customtkinter.CTkButton(self.chip_bar, text=p, font=customtkinter.CTkFont(size=14, weight="bold"), height=38, fg_color="#13141f", border_width=1, border_color=self.COLORS["ACCENT"], corner_radius=18, command=lambda v=p: self.apply_chip(v))
            c.pack(side="left", padx=8)
            self.prediction_chips.append(c)

    def apply_chip(self, val):
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", val)
        self.on_speak_click()

    def animate_loop(self):
        self.frame_count += 1
        cw = self.glow_canvas.winfo_width()
        ch = self.glow_canvas.winfo_height()
        if cw < 300: cw, ch = 850, 850 
        
        self.glow_canvas.delete("glow")
        amp = 40 * math.sin(self.frame_count * 0.1)
        base_r = min(cw, ch) * 0.38
        for i in range(4):
            r = base_r + amp - (i * 45)
            self.glow_canvas.create_oval(cw/2-r, ch/2-r, cw/2+r, ch/2+r, outline=self.glow_color, width=4-i, tags="glow")

        if self.transition_alpha < 1.0:
            self.transition_alpha = min(1.0, self.transition_alpha + self.transition_step)
            blended = Image.blend(self.prev_img_pil if self.prev_img_pil else self.target_img_pil, self.target_img_pil, self.transition_alpha)
            img_size = int(min(cw, ch) * 0.85)
            resized = blended.resize((img_size, img_size), Image.Resampling.LANCZOS)
            img = customtkinter.CTkImage(light_image=resized, dark_image=resized, size=(img_size, img_size))
            self.avatar_label.configure(image=img)
        
        if self.is_speaking and self.transition_alpha >= 1.0:
            pose = self.gesture_queue[int((self.frame_count//12)%len(self.gesture_queue))] if self.gesture_queue else ("speaking" if self.frame_count%10<5 else "resting")
            if pose != self.current_pose: self.start_transition(pose)
        
        float_y = math.sin(self.frame_count*0.07)*25
        self.avatar_label.place(relx=0.5, rely=0.5 + (float_y/1000), anchor="center")
        self.after(30, self.animate_loop)

    def start_transition(self, pose):
        if pose in self.source_images:
            self.prev_img_pil = Image.blend(self.prev_img_pil if self.prev_img_pil else self.target_img_pil, self.target_img_pil, self.transition_alpha)
            self.target_img_pil, self.current_pose, self.transition_alpha = self.source_images[pose], pose, 0.0

    def on_speak_click(self):
        t = self.entry.get("1.0", "end-1c").strip()
        if t: self.speak_phrase(t)

    def speak_phrase(self, text, translate=True):
        # Only translate if requested (e.g. from the input box)
        processed_text = text
        if translate and self.current_lang != "VI":
            processed_text = AIService.translate_phrase(text, self.current_lang)
        
        # Update entry box for feedback
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", processed_text)
        
        # Update status
        self.update_status(f"AI: Speaking '{processed_text}'...", self.COLORS["ACCENT"])
        
        self.gesture_queue = [v for k,v in {r"chào|hi|hello":"wave", r"cảm ơn|thanks":"thanks", r"đau|buồn":"sad", r"ăn|uống":"eat"}.items() if re.search(k, processed_text.lower())]
        self.is_speaking = True
        threading.Thread(target=self._play, args=(processed_text,), daemon=True).start()

    def _play(self, text):
        with self.audio_lock:
            try:
                # 1. Determine Accent
                lang_code = "vi" if self.current_lang == "VI" else "en"
                
                # 2. Premium Voices: Attempt Edge-TTS (US/UK/VI Neural)
                voice_map = {
                    "VI": "vi-VN-HoaiMyNeural",
                    "EN": "en-US-GuyNeural"
                }
                voice = voice_map.get(self.current_lang, "vi-VN-HoaiMyNeural")
                
                # FORCE lang_code to ensure gTTS fallback also uses correct accent
                lang_code = "en" if self.current_lang == "EN" else "vi"
                
                # ENCODING DEFENSE: Move audio to a safe ASCII-only temp folder
                temp_name = f"unibot_s_{int(time.time())}.mp3"
                p = os.path.join(tempfile.gettempdir(), temp_name)
                
                try:
                    import edge_tts
                    # Create an event loop for the async call
                    communicate = edge_tts.Communicate(text, voice)
                    asyncio.run(communicate.save(p))
                    logging.info(f"Edge-TTS Speak success: {text} ({voice}) at {p}")
                except Exception as e:
                    logging.warning(f"Edge-TTS failed/missing, fallback to gTTS: {e}")
                    # Fallback to gTTS
                    gTTS(text=text, lang=lang_code).save(p)
                    logging.info(f"gTTS fallback success: {text} ({lang_code}) at {p}")

                # 3. Audio Execution (MCI Windows)
                # Ensure MCI is COMPLETELY clear before opening the NEW path
                self.mci('close s', None, 0, 0)
                # Use ONLY short paths or quoted absolute paths that MCI understands
                self.mci(f'open "{p}" type mpegvideo alias s', None, 0, 0)
                self.mci('play s wait', None, 0, 0)
                self.mci('close s', None, 0, 0)
                
                self.is_speaking, self.gesture_queue = False, []
                self.start_transition("resting")
                self.update_status("AI Engine Online | System Ready")
                if os.path.exists(p): os.remove(p)
                
            except Exception as e: 
                self.is_speaking = False
                logging.error(f"Speech Master Failure: {e}")
                self.update_status(f"Error: {e}", "#e11d48")

if __name__ == "__main__":
    app = CommunicationApp()
    app.mainloop()
