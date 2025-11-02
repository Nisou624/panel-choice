# ui/search_window.py (version optimisée)
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional, List, Dict, Any
import os
import threading
import time

class SearchWindow:
    """Fenêtre de recherche ultra-rapide avec pagination et cache"""
    
    def __init__(self, root: ctk.CTkToplevel, db, file_handler, on_file_select: Callable):
        self.root = root
        self.db = db
        self.file_handler = file_handler
        self.on_file_select = on_file_select
        
        # Cache pour la recherche
        self.search_cache = {}
        self.current_results = []
        self.search_thread = None
        self.search_delay_timer = None
        
        self.root.title("🔍 Recherche Ultra-Rapide")
        self.root.geometry("1200x800")
        
        self.center_window()
        self.create_widgets()
        
        # Effectuer une recherche initiale en arrière-plan
        self.start_search_thread()
    
    def center_window(self):
        """Centrer la fenêtre"""
        self.root.update_idletasks()
        width = 1200
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Créer les widgets avec design optimisé"""
        # ============= EN-TÊTE COMPACT =============
        header = ctk.CTkFrame(
            self.root,
            height=65,
            corner_radius=0,
            fg_color=("#1f538d", "#14375e")
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Titre et bouton sur la même ligne
        ctk.CTkLabel(
            header,
            text="🔍 Recherche Ultra-Rapide",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#ffffff", "#ffffff")
        ).pack(side="left", padx=25, pady=18)
        
        # Indicateur de performance
        self.perf_label = ctk.CTkLabel(
            header,
            text="⚡ Prêt",
            font=ctk.CTkFont(size=11),
            text_color=("#90EE90", "#90EE90")
        )
        self.perf_label.pack(side="left", padx=10)
        
        ctk.CTkButton(
            header,
            text="✖️ Fermer",
            width=90,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#dc3545", "#b02a37"),
            hover_color=("#e04555", "#c03545"),
            command=self.root.destroy
        ).pack(side="right", padx=25)
        
        # ============= ZONE DE RECHERCHE ULTRA-COMPACTE =============
        search_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        search_container.pack(fill="x", padx=12, pady=8)
        
        search_frame = ctk.CTkFrame(
            search_container,
            fg_color=("#f8f9fa", "#1a2a3a"),
            corner_radius=10,
            border_width=1,
            border_color=("#1f538d", "#2563a8")
        )
        search_frame.pack(fill="x")
        
        # Une seule ligne pour tous les critères
        criteria_row = ctk.CTkFrame(search_frame, fg_color="transparent")
        criteria_row.pack(fill="x", padx=15, pady=12)
        
        # Champ de recherche principal - 50%
        search_container_inner = ctk.CTkFrame(criteria_row, fg_color="transparent")
        search_container_inner.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            search_container_inner,
            text="🔍",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(0, 5))
        
        self.filename_entry = ctk.CTkEntry(
            search_container_inner,
            height=32,
            font=ctk.CTkFont(size=12),
            placeholder_text="Recherche instantanée..."
        )
        self.filename_entry.pack(side="left", fill="x", expand=True)
        
        # Type de fichier - 25%
        type_container = ctk.CTkFrame(criteria_row, fg_color="transparent")
        type_container.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            type_container,
            text="📋",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 5))
        
        self.extension_combo = ctk.CTkComboBox(
            type_container,
            width=130,
            height=32,
            font=ctk.CTkFont(size=11),
            values=["Tous", "PDF", "Word", "Excel"]
        )
        self.extension_combo.pack(side="left")
        self.extension_combo.set("Tous")
        
        # Panel - 25%
        panel_container = ctk.CTkFrame(criteria_row, fg_color="transparent")
        panel_container.pack(side="left")
        
        ctk.CTkLabel(
            panel_container,
            text="📁",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 5))
        
        self.panel_combo = ctk.CTkComboBox(
            panel_container,
            width=140,
            height=32,
            font=ctk.CTkFont(size=11),
            values=["Tous", "Certification", "En-tête", "Interface Employés", "Autre"]
        )
        self.panel_combo.pack(side="left")
        self.panel_combo.set("Tous")
        
        # ============= RÉSULTATS AVEC PAGINATION =============
        results_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        results_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # En-tête des résultats avec statistiques
        results_header = ctk.CTkFrame(
            results_container,
            height=40,
            fg_color=("#e7f3ff", "#1a3a52"),
            corner_radius=8
        )
        results_header.pack(fill="x", pady=(0, 8))
        results_header.pack_propagate(False)
        
        self.results_label = ctk.CTkLabel(
            results_header,
            text="🔍 Chargement...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1f538d", "#2563a8")
        )
        self.results_label.pack(side="left", padx=15, pady=10)
        
        # Boutons de pagination
        pagination_frame = ctk.CTkFrame(results_header, fg_color="transparent")
        pagination_frame.pack(side="right", padx=15, pady=8)
        
        self.prev_button = ctk.CTkButton(
            pagination_frame,
            text="◀",
            width=30,
            height=25,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#6c757d", "#5a6268"),
            hover_color=("#7c858d", "#6a7278"),
            command=self.prev_page
        )
        self.prev_button.pack(side="left", padx=2)
        
        self.page_label = ctk.CTkLabel(
            pagination_frame,
            text="1/1",
            font=ctk.CTkFont(size=10),
            text_color=("#666", "#aaa")
        )
        self.page_label.pack(side="left", padx=8)
        
        self.next_button = ctk.CTkButton(
            pagination_frame,
            text="▶",
            width=30,
            height=25,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#6c757d", "#5a6268"),
            hover_color=("#7c858d", "#6a7278"),
            command=self.next_page
        )
        self.next_button.pack(side="left", padx=2)
        
        # Liste des résultats avec scroll optimisé
        self.results_list = ctk.CTkScrollableFrame(
            results_container,
            fg_color=("gray95", "gray15"),
            corner_radius=10
        )
        self.results_list.pack(fill="both", expand=True)
        
        # Variables de pagination
        self.current_page = 1
        self.results_per_page = 20
        self.total_pages = 1
        
        # Liaison des événements avec temporisation
        self.filename_entry.bind('<KeyRelease>', lambda e: self.schedule_search())
        self.extension_combo.configure(command=lambda _: self.schedule_search())
        self.panel_combo.configure(command=lambda _: self.schedule_search())
    
    def schedule_search(self):
        """Programmer une recherche avec délai pour éviter trop de requêtes"""
        # Annuler le timer précédent s'il existe
        if self.search_delay_timer:
            self.root.after_cancel(self.search_delay_timer)
        
        # Programmer la recherche dans 300ms
        self.search_delay_timer = self.root.after(300, self.start_search_thread)
    
    def start_search_thread(self):
        """Démarrer la recherche dans un thread séparé"""
        # Annuler le thread précédent s'il existe
        if self.search_thread and self.search_thread.is_alive():
            return  # La recherche précédente est encore en cours
        
        self.search_thread = threading.Thread(target=self.search_files_threaded, daemon=True)
        self.search_thread.start()
    
    def search_files_threaded(self):
        """Effectuer la recherche dans un thread séparé"""
        try:
            start_time = time.time()
            
            # Récupérer les critères de recherche
            filename = self.filename_entry.get().strip()
            extension_type = self.extension_combo.get()
            panel_type = self.panel_combo.get()
            
            # Créer une clé de cache
            cache_key = f"{filename}_{extension_type}_{panel_type}"
            
            # Vérifier le cache
            if cache_key in self.search_cache:
                results = self.search_cache[cache_key]
                search_time = 0.001  # Cache hit
            else:
                # Convertir les types
                extension_map = {
                    "Tous": "",
                    "PDF": "pdf",
                    "Word": "docx",
                    "Excel": "xlsx"
                }
                
                panel_map = {
                    "Tous": None,
                    "Certification": "certification",
                    "En-tête": "entete",
                    "Interface Employés": "interface_emp",
                    "Autre": "autre"
                }
                
                extension = extension_map.get(extension_type, "")
                panel = panel_map.get(panel_type)
                
                # Effectuer la recherche ultra-rapide
                results = self.db.search_files_fast(
                    filename=filename,
                    extension=extension,
                    panel=panel,
                    limit=200
                )
                
                # Mettre en cache si moins de 200 résultats
                if len(results) < 200:
                    self.search_cache[cache_key] = results
                
                search_time = time.time() - start_time
            
            # Mettre à jour l'interface dans le thread principal
            self.root.after(0, lambda: self.update_results(results, search_time))
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_search_error(e))
    
    def update_results(self, results: List[Dict[str, Any]], search_time: float):
        """Mettre à jour les résultats dans l'interface"""
        try:
            self.current_results = results
            self.current_page = 1
            self.total_pages = max(1, (len(results) + self.results_per_page - 1) // self.results_per_page)
            
            # Mettre à jour l'indicateur de performance
            if search_time < 0.1:
                perf_text = f"⚡ Ultra-rapide ({search_time:.3f}s)"
                perf_color = "#90EE90"
            elif search_time < 0.5:
                perf_text = f"🚀 Rapide ({search_time:.3f}s)"
                perf_color = "#FFD700"
            else:
                perf_text = f"⏱️ Normal ({search_time:.3f}s)"
                perf_color = "#FFA500"
            
            self.perf_label.configure(text=perf_text, text_color=(perf_color, perf_color))
            
            # Afficher la première page
            self.display_current_page()
            
        except Exception as e:
            print(f"❌ Erreur mise à jour résultats: {e}")
    
    def handle_search_error(self, error):
        """Gérer les erreurs de recherche"""
        print(f"❌ Erreur recherche: {error}")
        self.perf_label.configure(text="❌ Erreur", text_color=("#FF6B6B", "#FF6B6B"))
        self.results_label.configure(text="❌ Erreur de recherche")
    
    def display_current_page(self):
        """Afficher la page courante des résultats"""
        try:
            # Nettoyer la liste
            for widget in self.results_list.winfo_children():
                widget.destroy()
            
            # Calculer les indices de la page
            start_idx = (self.current_page - 1) * self.results_per_page
            end_idx = min(start_idx + self.results_per_page, len(self.current_results))
            
            page_results = self.current_results[start_idx:end_idx]
            
            # Mettre à jour les labels
            total_count = len(self.current_results)
            self.results_label.configure(
                text=f"🔍 Résultats: {total_count} fichier(s) • Page {self.current_page}/{self.total_pages}"
            )
            self.page_label.configure(text=f"{self.current_page}/{self.total_pages}")
            
            # Activer/désactiver les boutons de pagination
            self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
            self.next_button.configure(state="normal" if self.current_page < self.total_pages else "disabled")
            
            if total_count == 0:
                # Message d'état vide
                self.create_empty_state()
                return
            
            # Afficher chaque fichier de la page
            for file in page_results:
                self.create_file_result_card_optimized(file)
                
        except Exception as e:
            print(f"❌ Erreur affichage page: {e}")
    
    def create_empty_state(self):
        """Créer l'état vide optimisé"""
        empty_frame = ctk.CTkFrame(self.results_list, fg_color="transparent")
        empty_frame.pack(expand=True, pady=40)
        
        ctk.CTkLabel(
            empty_frame,
            text="🔍",
            font=ctk.CTkFont(size=48)
        ).pack()
        
        ctk.CTkLabel(
            empty_frame,
            text="Aucun fichier trouvé",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray50", "gray60")
        ).pack(pady=(8, 3))
        
        ctk.CTkLabel(
            empty_frame,
            text="Essayez avec d'autres mots-clés",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack()
    
    def create_file_result_card_optimized(self, file: Dict[str, Any]):
        """Créer une carte de résultat ultra-optimisée"""
        try:
            # Récupérer le nom original pour les fichiers cryptés
            if hasattr(self.file_handler, 'get_original_filename'):
                display_name = self.file_handler.get_original_filename(file['filepath'])
            else:
                display_name = file['filename']
            
            extension = display_name.rsplit('.', 1)[-1].lower() if '.' in display_name else ''
            icon = self.file_handler.get_file_icon(extension)
            is_pdf = extension == 'pdf'
            
            # Frame de la carte ultra-compacte
            card = ctk.CTkFrame(
                self.results_list,
                height=65,
                fg_color=("white", "gray20"),
                corner_radius=6,
                border_width=1,
                border_color=("gray80", "gray40")
            )
            card.pack(fill="x", pady=2, padx=3)
            card.pack_propagate(False)
            
            # Icône compacte
            icon_label = ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=24),
                width=50
            )
            icon_label.pack(side="left", padx=8)
            
            # Informations sur deux lignes
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=8)
            
            # Ligne 1: Nom du fichier
            name_label = ctk.CTkLabel(
                info_frame,
                text=display_name[:60] + "..." if len(display_name) > 60 else display_name,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            name_label.pack(fill="x")
            
            # Ligne 2: Métadonnées compactes
            folder_name = file.get('folder_name', 'Dossier inconnu')
            panel_name = file.get('panel', 'interface_emp')
            
            panel_display = {
                'certification': 'Certification',
                'entete': 'En-tête',
                'interface_emp': 'Interface Emp.',
                'autre': 'Autre'
            }.get(panel_name, panel_name)
            
            size_text = self.file_handler.format_file_size(file.get('file_size', 0))
            type_indicator = "🔒" if is_pdf else "💾"
            
            meta_text = f"{type_indicator} {panel_display} • {folder_name[:20]}{'...' if len(folder_name) > 20 else ''} • {size_text}"
            
            meta_label = ctk.CTkLabel(
                info_frame,
                text=meta_text,
                font=ctk.CTkFont(size=9),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            meta_label.pack(fill="x")
            
            # Boutons d'action ultra-compacts
            button_frame = ctk.CTkFrame(card, fg_color="transparent")
            button_frame.pack(side="right", padx=8)
            
            # Bouton Ouvrir mini
            action_text = "👁️" if is_pdf else "📥"
            open_btn = ctk.CTkButton(
                button_frame,
                text=action_text,
                width=28,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#1f538d", "#14375e"),
                hover_color=("#2563a8", "#1a4a7a"),
                command=lambda f=file: self.open_file(f)
            )
            open_btn.pack(side="left", padx=1)
            
            # Bouton Localiser mini
            locate_btn = ctk.CTkButton(
                button_frame,
                text="📍",
                width=28,
                height=24,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#28a745", "#1e7e34"),
                hover_color=("#32b349", "#229143"),
                command=lambda f=file: self.locate_file(f)
            )
            locate_btn.pack(side="left", padx=1)
            
            # Double-clic pour ouvrir
            card.bind('<Double-Button-1>', lambda e, f=file: self.open_file(f))
            
            # Hover effect léger
            def on_enter(e):
                card.configure(border_color=("#1f538d", "#2563a8"), border_width=2)
            
            def on_leave(e):
                card.configure(border_color=("gray80", "gray40"), border_width=1)
            
            card.bind('<Enter>', on_enter)
            card.bind('<Leave>', on_leave)
            
        except Exception as e:
            print(f"❌ Erreur création carte: {e}")
    
    def prev_page(self):
        """Page précédente"""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_current_page()
    
    def next_page(self):
        """Page suivante"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.display_current_page()
    
    def open_file(self, file: Dict[str, Any]):
        """Ouvrir un fichier avec le bon viewer"""
        try:
            if not os.path.exists(file['filepath']):
                messagebox.showerror("Erreur", "❌ Le fichier n'existe plus")
                return
            
            # Récupérer le nom original pour les fichiers cryptés
            if hasattr(self.file_handler, 'get_original_filename'):
                display_name = self.file_handler.get_original_filename(file['filepath'])
            else:
                display_name = file['filename']
            
            extension = display_name.rsplit('.', 1)[-1].lower() if '.' in display_name else ''
            
            # Si c'est un PDF, utiliser le viewer intégré
            if extension == 'pdf':
                from .pdf_viewer import PDFViewer
                pdf_window = ctk.CTkToplevel(self.root)
                PDFViewer(pdf_window, file['filepath'], display_name)
            else:
                # Pour les autres fichiers, utiliser le gestionnaire de fichiers
                success = self.file_handler.open_file(file['filepath'])
                if not success:
                    messagebox.showerror("Erreur", "❌ Impossible d'ouvrir le fichier")
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible d'ouvrir le fichier:\n{e}")
    
    def locate_file(self, file: Dict[str, Any]):
        """Localiser un fichier dans son dossier"""
        try:
            # Fermer la fenêtre de recherche
            self.root.destroy()
            
            # Appeler le callback pour naviguer vers le dossier
            if self.on_file_select:
                self.on_file_select(file['folder_id'])
                
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible de localiser:\n{e}")

