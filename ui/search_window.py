import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional, List, Dict, Any
import os

class SearchWindow:
    """Fenêtre de recherche optimisée avec plus d'espace pour les résultats"""
    
    def __init__(self, root: ctk.CTkToplevel, db, file_handler, on_file_select: Callable):
        self.root = root
        self.db = db
        self.file_handler = file_handler
        self.on_file_select = on_file_select
        
        self.root.title("🔍 Recherche de Fichiers")
        self.root.geometry("1100x750")  # ✅ Augmenté la hauteur
        
        self.center_window()
        self.create_widgets()
        
        # Effectuer une recherche initiale (tous les fichiers)
        self.search_files()
    
    def center_window(self):
        """Centrer la fenêtre"""
        self.root.update_idletasks()
        width = 1100
        height = 750
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Créer les widgets avec design optimisé"""
        # ============= EN-TÊTE COMPACT =============
        header = ctk.CTkFrame(
            self.root,
            height=70,  # ✅ Réduit de 80 à 70
            corner_radius=0,
            fg_color=("#1f538d", "#14375e")
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Titre et bouton sur la même ligne
        ctk.CTkLabel(
            header,
            text="🔍 Recherche de Fichiers",
            font=ctk.CTkFont(size=22, weight="bold"),  # ✅ Réduit de 24 à 22
            text_color=("#ffffff", "#ffffff")
        ).pack(side="left", padx=30, pady=20)
        
        ctk.CTkButton(
            header,
            text="✖️ Fermer",
            width=100,  # ✅ Réduit de 120 à 100
            height=40,  # ✅ Réduit de 45 à 40
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#dc3545", "#b02a37"),
            hover_color=("#e04555", "#c03545"),
            command=self.root.destroy
        ).pack(side="right", padx=30)
        
        # ============= ZONE DE RECHERCHE COMPACTE =============
        search_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        search_container.pack(fill="x", padx=15, pady=12)  # ✅ Réduit padding
        
        search_frame = ctk.CTkFrame(
            search_container,
            fg_color=("#f0f8ff", "#1a2a3a"),
            corner_radius=12,  # ✅ Réduit de 15 à 12
            border_width=2,
            border_color=("#1f538d", "#2563a8")
        )
        search_frame.pack(fill="x")
        
        # Titre compact
        title_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(10, 8))  # ✅ Padding réduit
        
        ctk.CTkLabel(
            title_frame,
            text="🎯 Recherche Simple",
            font=ctk.CTkFont(size=16, weight="bold"),  # ✅ Réduit de 18 à 16
            text_color=("#1f538d", "#2563a8")
        ).pack(side="left")
        
        # Boutons principaux à droite du titre
        main_buttons = ctk.CTkFrame(title_frame, fg_color="transparent")
        main_buttons.pack(side="right")
        
        ctk.CTkButton(
            main_buttons,
            text="🔍 Rechercher",
            width=110,  # ✅ Réduit
            height=35,  # ✅ Réduit
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#28a745", "#1e7e34"),
            hover_color=("#32b349", "#229143"),
            command=self.search_files
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            main_buttons,
            text="🧹 Effacer",
            width=110,  # ✅ Réduit
            height=35,  # ✅ Réduit
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#ffc107", "#e0a800"),
            hover_color=("#ffcd39", "#efb810"),
            command=self.clear_filters
        ).pack(side="left", padx=5)
        
        # Frame des critères - LAYOUT HORIZONTAL COMPACT
        criteria_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        criteria_frame.pack(fill="x", padx=20, pady=(0, 10))  # ✅ Padding réduit
        
        # LIGNE UNIQUE pour nom et extension
        row = ctk.CTkFrame(criteria_frame, fg_color="transparent")
        row.pack(fill="x", pady=5)
        
        # Nom du fichier - 60% de largeur
        name_container = ctk.CTkFrame(row, fg_color="transparent")
        name_container.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        name_label_frame = ctk.CTkFrame(name_container, fg_color="transparent")
        name_label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            name_label_frame,
            text="📄 Nom:",  # ✅ Texte raccourci
            font=ctk.CTkFont(size=13, weight="bold"),  # ✅ Réduit
            anchor="w"
        ).pack(side="left")
        
        self.filename_entry = ctk.CTkEntry(
            name_container,
            height=36,  # ✅ Réduit de 40 à 36
            font=ctk.CTkFont(size=13),
            placeholder_text="Nom du fichier..."  # ✅ Texte raccourci
        )
        self.filename_entry.pack(fill="x", pady=(3, 0))
        
        # Extension - 30% de largeur
        ext_container = ctk.CTkFrame(row, fg_color="transparent")
        ext_container.pack(side="left")
        
        ctk.CTkLabel(
            ext_container,
            text="📋 Type:",  # ✅ Texte raccourci
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack()
        
        self.extension_combo = ctk.CTkComboBox(
            ext_container,
            width=180,  # ✅ Réduit de 200 à 180
            height=36,  # ✅ Réduit
            font=ctk.CTkFont(size=12),  # ✅ Réduit
            values=[
                "Tous",
                "PDF",
                "Word",
                "Excel",
                "Texte",
                "Image"
            ]  # ✅ Noms raccourcis
        )
        self.extension_combo.pack(pady=(3, 0))
        self.extension_combo.set("Tous")
        
        # Raccourcis compacts - LIGNE UNIQUE
        shortcuts_frame = ctk.CTkFrame(criteria_frame, fg_color="transparent")
        shortcuts_frame.pack(fill="x", pady=(8, 0))  # ✅ Padding réduit
        
        ctk.CTkLabel(
            shortcuts_frame,
            text="🚀 Filtres rapides:",
            font=ctk.CTkFont(size=11, weight="bold")  # ✅ Réduit
        ).pack(side="left", padx=(0, 10))
        
        shortcuts = [
            ("📕 PDF", lambda: self.set_filter("PDF")),
            ("📘 Word", lambda: self.set_filter("Word")),
            ("📗 Excel", lambda: self.set_filter("Excel")),
            ("🌐 Tous", lambda: self.clear_filters())
        ]
        
        for text, command in shortcuts:
            ctk.CTkButton(
                shortcuts_frame,
                text=text,
                width=85,  # ✅ Réduit
                height=30,  # ✅ Réduit de 35 à 30
                font=ctk.CTkFont(size=11),  # ✅ Réduit
                fg_color=("#6c757d", "#5a6268"),
                hover_color=("#7c858d", "#6a7278"),
                command=command
            ).pack(side="left", padx=3)
        
        # ============= RÉSULTATS - ESPACE MAXIMISÉ =============
        results_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        results_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))  # ✅ Padding optimisé
        
        # En-tête des résultats compact
        results_header = ctk.CTkFrame(
            results_container,
            height=45,  # ✅ Réduit de 50 à 45
            fg_color=("#e7f3ff", "#1a3a52"),
            corner_radius=8  # ✅ Réduit
        )
        results_header.pack(fill="x", pady=(0, 8))  # ✅ Padding réduit
        results_header.pack_propagate(False)
        
        self.results_label = ctk.CTkLabel(
            results_header,
            text="🔍 Résultats - 0 fichier(s)",  # ✅ Texte raccourci
            font=ctk.CTkFont(size=15, weight="bold"),  # ✅ Réduit
            text_color=("#1f538d", "#2563a8")
        )
        self.results_label.pack(pady=12)  # ✅ Centré
        
        # Liste des résultats - ESPACE MAXIMISÉ
        self.results_list = ctk.CTkScrollableFrame(
            results_container,
            fg_color=("gray95", "gray15"),
            corner_radius=12  # ✅ Réduit
        )
        self.results_list.pack(fill="both", expand=True)
        
        # Liaison des événements
        self.filename_entry.bind('<KeyRelease>', lambda e: self.auto_search())
        self.extension_combo.configure(command=lambda _: self.auto_search())
    
    def set_filter(self, extension_type: str):
        """Définir un filtre rapide"""
        self.extension_combo.set(extension_type)
        self.search_files()
    
    def clear_filters(self):
        """Effacer tous les filtres"""
        self.filename_entry.delete(0, "end")
        self.extension_combo.set("Tous")
        self.search_files()
    
    def auto_search(self):
        """Recherche automatique lors de la saisie"""
        # Petite temporisation pour éviter trop de recherches
        self.root.after(300, self.search_files)
    
    def search_files(self):
        """Effectuer la recherche avec les critères actuels"""
        try:
            # Récupérer les critères
            filename = self.filename_entry.get().strip()
            extension_type = self.extension_combo.get()
            
            # Convertir le type en extension
            extension_map = {
                "Tous": "",
                "PDF": "pdf",
                "Word": "docx",
                "Excel": "xlsx",
                "Texte": "txt",
                "Image": "png"
            }
            
            extension = extension_map.get(extension_type, "")
            
            # Effectuer la recherche
            results = self.db.search_files(
                filename=filename,
                extension=extension
            )
            
            # Afficher les résultats
            self.display_results(results)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de la recherche:\n{e}")
            print(f"Erreur recherche: {e}")
    
    def display_results(self, files: List[Dict[str, Any]]):
        """Afficher les résultats de la recherche"""
        # Nettoyer
        for widget in self.results_list.winfo_children():
            widget.destroy()
        
        # Mettre à jour le compteur
        count = len(files)
        self.results_label.configure(text=f"🔍 Résultats - {count} fichier(s)")
        
        if count == 0:
            # Message d'état vide compact
            empty_frame = ctk.CTkFrame(self.results_list, fg_color="transparent")
            empty_frame.pack(expand=True, pady=50)
            
            ctk.CTkLabel(
                empty_frame,
                text="📭",
                font=ctk.CTkFont(size=60)  # ✅ Réduit
            ).pack()
            
            ctk.CTkLabel(
                empty_frame,
                text="Aucun fichier trouvé",
                font=ctk.CTkFont(size=16, weight="bold"),  # ✅ Réduit
                text_color=("gray50", "gray60")
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                empty_frame,
                text="Modifiez vos critères de recherche",
                font=ctk.CTkFont(size=12),  # ✅ Réduit
                text_color=("gray50", "gray60")
            ).pack()
            return
        
        # Afficher chaque fichier avec hauteur réduite
        for file in files:
            self.create_file_result_card(file)
    
    def create_file_result_card(self, file: Dict[str, Any]):
        """Créer une carte de résultat compacte pour un fichier"""
        extension = file['filename'].rsplit('.', 1)[-1].lower() if '.' in file['filename'] else ''
        icon = self.file_handler.get_file_icon(extension)
        is_pdf = extension == 'pdf'
        
        # Frame de la carte - HAUTEUR RÉDUITE
        card = ctk.CTkFrame(
            self.results_list,
            height=75,  # ✅ Réduit de 90 à 75
            fg_color=("white", "gray20"),
            corner_radius=8,  # ✅ Réduit
            border_width=1,
            border_color=("gray80", "gray40")
        )
        card.pack(fill="x", pady=3, padx=5)  # ✅ Padding réduit
        card.pack_propagate(False)
        
        # Icône compacte
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=28),  # ✅ Réduit de 32
            width=65  # ✅ Réduit
        )
        icon_label.pack(side="left", padx=12)  # ✅ Padding réduit
        
        # Informations du fichier
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=8, pady=10)  # ✅ Padding réduit
        
        # Nom du fichier - une seule ligne avec ellipsis si trop long
        name_label = ctk.CTkLabel(
            info_frame,
            text=file['filename'],
            font=ctk.CTkFont(size=13, weight="bold"),  # ✅ Réduit
            anchor="w"
        )
        name_label.pack(fill="x")
        
        # Dossier parent et type sur la même ligne
        folder = self.db.get_folder(file['folder_id'])
        folder_name = folder['name'] if folder else "Dossier supprimé"
        
        type_indicator = "🔒 PDF" if is_pdf else "💾 DOCX/XLSX"
        
        meta_text = f"📁 {folder_name[:30]}{'...' if len(folder_name) > 30 else ''} • {type_indicator}"
        
        meta_label = ctk.CTkLabel(
            info_frame,
            text=meta_text,
            font=ctk.CTkFont(size=10),  # ✅ Réduit
            text_color=("gray50", "gray60"),
            anchor="w"
        )
        meta_label.pack(fill="x")
        
        # Boutons d'action compacts
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(side="right", padx=10)  # ✅ Padding réduit
        
        # Bouton Ouvrir compact
        action_text = "👁️ Voir" if is_pdf else "📥 Ouvrir"  # ✅ Texte raccourci
        open_btn = ctk.CTkButton(
            button_frame,
            text=action_text,
            width=80,  # ✅ Réduit de 100
            height=28,  # ✅ Réduit de 35
            font=ctk.CTkFont(size=11, weight="bold"),  # ✅ Réduit
            fg_color=("#1f538d", "#14375e"),
            hover_color=("#2563a8", "#1a4a7a"),
            command=lambda f=file: self.open_file(f)
        )
        open_btn.pack(side="left", padx=3)  # ✅ Padding réduit
        
        # Bouton Localiser compact
        locate_btn = ctk.CTkButton(
            button_frame,
            text="📍",  # ✅ Icône seule
            width=35,  # ✅ Bouton icône compact
            height=28,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#28a745", "#1e7e34"),
            hover_color=("#32b349", "#229143"),
            command=lambda f=file: self.locate_file(f)
        )
        locate_btn.pack(side="left", padx=3)
        
        # Double-clic pour ouvrir
        card.bind('<Double-Button-1>', lambda e, f=file: self.open_file(f))
        
        # Hover effect
        def on_enter(e):
            card.configure(border_color=("#1f538d", "#2563a8"), border_width=2)
        
        def on_leave(e):
            card.configure(border_color=("gray80", "gray40"), border_width=1)
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
    
    def open_file(self, file: Dict[str, Any]):
        """Ouvrir un fichier avec le bon viewer"""
        if not os.path.exists(file['filepath']):
            messagebox.showerror("Erreur", "❌ Le fichier n'existe plus")
            return
        
        extension = file['filename'].rsplit('.', 1)[-1].lower() if '.' in file['filename'] else ''
        
        # Si c'est un PDF, utiliser le viewer intégré
        if extension == 'pdf':
            try:
                from .pdf_viewer import PDFViewer
                pdf_window = ctk.CTkToplevel(self.root)
                PDFViewer(pdf_window, file['filepath'], file['filename'])
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible d'ouvrir le PDF:\n{e}")
        else:
            # Pour les autres fichiers, utiliser le gestionnaire de fichiers
            success = self.file_handler.open_file(file['filepath'])
            if not success:
                messagebox.showerror("Erreur", "❌ Impossible d'ouvrir le fichier")
    
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
