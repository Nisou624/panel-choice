import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES
from typing import Callable, Optional
import os
class AdminWindow:
    """Fenêtre d'administration modernisée avec support des panels"""
   
    PANEL_INFO = {
        'certification': {'name': 'Certification', 'icon': '📜', 'color': '#28a745'},
        'entete': {'name': 'En-tête', 'icon': '📋', 'color': '#1f538d'},
        'interface_emp': {'name': 'Interface Employés', 'icon': '👥', 'color': '#17a2b8'},
        'autre': {'name': 'Autre', 'icon': '📦', 'color': '#6c757d'}
    }
   
    def __init__(self, root: ctk.CTkToplevel, db, file_handler, panel: str, on_changes: Callable):
        self.root = root
        self.db = db
        self.file_handler = file_handler
        self.panel = panel
        self.on_changes = on_changes
       
        self.panel_info = self.PANEL_INFO.get(panel, {
            'name': 'Inconnu',
            'icon': '📁',
            'color': '#6c757d'
        })
       
        self.root.title(f"Administration - {self.panel_info['name']}")
        self.root.geometry("1100x750")
       
        # Centrer la fenêtre
        self.center_window()
       
        # Créer l'interface
        self.create_widgets()
       
        # Charger les dossiers du panel
        self.load_folders()
   
    def center_window(self):
        """Centrer la fenêtre"""
        self.root.update_idletasks()
        width = 1100
        height = 750
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
   
    def create_widgets(self):
        """Créer les widgets"""
        # ============= EN-TÊTE =============
        header = ctk.CTkFrame(
            self.root,
            height=80,
            corner_radius=0,
            fg_color=(self.panel_info['color'], self.panel_info['color'])
        )
        header.pack(fill="x")
        header.pack_propagate(False)
       
        # Titre avec icône du panel
        title_label = ctk.CTkLabel(
            header,
            text=f"{self.panel_info['icon']} Gestion - {self.panel_info['name']}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.pack(side="left", padx=30, pady=20)
       
        # Bouton fermer
        close_button = ctk.CTkButton(
            header,
            text="✖️ Fermer",
            width=120,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#dc3545", "#b02a37"),
            hover_color=("#e04555", "#c03545"),
            command=self.root.destroy
        )
        close_button.pack(side="right", padx=30)
       
        # ============= ZONE DRAG & DROP =============
        dragdrop_container = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        dragdrop_container.pack(fill="x", padx=20, pady=20)
       
        dragdrop_frame = ctk.CTkFrame(
            dragdrop_container,
            height=160,
            corner_radius=15,
            fg_color=("#e7f3ff", "#1a3a52"),
            border_width=3,
            border_color=("#0066cc", "#0088ee")
        )
        dragdrop_frame.pack(fill="x")
        dragdrop_frame.pack_propagate(False)
       
        # Titre de la zone
        ctk.CTkLabel(
            dragdrop_frame,
            text="📦 Zone Drag & Drop - Import de Dossiers",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#0066cc", "#00aaff")
        ).pack(pady=(15, 10))
       
        # Zone de drop
        self.drop_zone = ctk.CTkLabel(
            dragdrop_frame,
            text="⬇️ Glissez-déposez un dossier ici pour l'importer\n\n"
                 "✅ Tous les fichiers (.docx, .pdf, .xlsx) seront importés\n"
                 "✅ L'arborescence complète sera conservée",
            font=ctk.CTkFont(size=13),
            fg_color=("#ffffff", "#2a4a5a"),
            corner_radius=10,
            height=90,
            cursor="hand2"
        )
        self.drop_zone.pack(fill="x", padx=20, pady=(0, 15))
       
        # Configuration du drag & drop
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
       
        # Clic pour sélectionner
        self.drop_zone.bind('<Button-1>', lambda e: self.import_folder())
       
        # ============= BARRE D'OUTILS =============
        toolbar = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        toolbar.pack(fill="x", padx=20, pady=(0, 15))
       
        # Boutons
        button_data = [
            ("➕ Nouveau Dossier", "#28a745", "#1e7e34", self.create_folder),
            ("📂 Importer Dossier", "#1f538d", "#14375e", self.import_folder),
            ("📄 Importer Fichiers", "#17a2b8", "#138496", self.import_files),
            ("🔄 Rafraîchir", "#6c757d", "#5a6268", self.load_folders)
        ]
       
        for text, fg_color, hover_color, command in button_data:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                width=160,
                height=45,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=fg_color,
                hover_color=hover_color,
                command=command
            )
            btn.pack(side="left", padx=5)
       
        # ============= LISTE DES DOSSIERS =============
        list_frame = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
       
        # Scrollable frame pour les dossiers
        self.folders_list = ctk.CTkScrollableFrame(
            list_frame,
            fg_color=("#f0f0f0", "#2b2b2b"),
            corner_radius=15
        )
        self.folders_list.pack(fill="both", expand=True)
   
    def load_folders(self):
        """Charger les dossiers du panel"""
        # Nettoyer la liste
        for widget in self.folders_list.winfo_children():
            widget.destroy()
       
        # Charger les dossiers racine du panel
        root_folders = self.db.get_subfolders(None, panel=self.panel)
       
        if not root_folders:
            ctk.CTkLabel(
                self.folders_list,
                text=f"📭 Aucun dossier dans {self.panel_info['name']}\n\nCommencez par créer ou importer un dossier",
                font=ctk.CTkFont(size=16),
                text_color=("gray50", "gray60")
            ).pack(expand=True, pady=100)
            return
       
        for folder in root_folders:
            self.insert_folder_card(self.folders_list, folder, level=0)
   
    def insert_folder_card(self, parent, folder: dict, level: int):
        """Insérer une carte de dossier"""
        # Frame principale de la carte
        card = ctk.CTkFrame(
            parent,
            fg_color=("#ffffff", "#1e1e1e"),
            corner_radius=10,
            border_width=1,
            border_color=("gray80", "gray30")
        )
        card.pack(fill="x", padx=(level * 30 + 10, 10), pady=5)
       
        # Frame intérieur
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)
       
        # Icône et info
        left_frame = ctk.CTkFrame(inner, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
       
        # Nom avec icône
        name_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        name_frame.pack(side="left")
       
        # Récupérer les sous-dossiers pour vérifier s'il y en a
        subfolders = self.db.get_subfolders(folder['id'])
        has_subfolders = len(subfolders) > 0
       
        if has_subfolders:
            # Ajouter le chevron d'expansion
            expanded = ctk.BooleanVar(value=True)
            chevron = ctk.CTkLabel(
                name_frame,
                text='▼',
                font=ctk.CTkFont(size=18),
                cursor="hand2"
            )
            chevron.pack(side="left", padx=(0, 5))
           
            # Créer le conteneur pour les sous-dossiers
            children_container = ctk.CTkFrame(parent, fg_color="transparent")
           
            # Binder le clic sur le chevron
            chevron.bind("<Button-1>", lambda e: self.toggle_expand(expanded, chevron, children_container, card))
           
            # Packer initialement le conteneur si développé
            if expanded.get():
                children_container.pack(fill="x", pady=0, after=card)
           
            # Insérer les sous-dossiers dans le conteneur
            for subfolder in subfolders:
                self.insert_folder_card(children_container, subfolder, level + 1)
       
        # Icône du dossier
        ctk.CTkLabel(
            name_frame,
            text="📁",
            font=ctk.CTkFont(size=24)
        ).pack(side="left", padx=(0, 10))
       
        info_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
        info_frame.pack(side="left")
       
        ctk.CTkLabel(
            info_frame,
            text=folder['name'],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        ).pack(anchor="w")
       
        file_count = self.db.count_files_in_folder(folder['id'], recursive=True)
        ctk.CTkLabel(
            info_frame,
            text=f"{file_count} fichier{'s' if file_count > 1 else ''} • ID: {folder['id']}",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w"
        ).pack(anchor="w")
       
        # Boutons d'action
        button_frame = ctk.CTkFrame(inner, fg_color="transparent")
        button_frame.pack(side="right")
       
        buttons_data = [
            ("➕", "#28a745", "#1e7e34", lambda f=folder: self.add_subfolder(f['id'])),
            ("✏️", "#ffc107", "#e0a800", lambda f=folder: self.rename_folder(f['id'])),
            ("📄", "#17a2b8", "#138496", lambda f=folder: self.manage_files(f['id'])),
            ("🗑️", "#dc3545", "#b02a37", lambda f=folder: self.delete_folder(f['id']))
        ]
       
        for text, fg_color, hover_color, command in buttons_data:
            ctk.CTkButton(
                button_frame,
                text=text,
                width=45,
                height=35,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=fg_color,
                hover_color=hover_color,
                command=command
            ).pack(side="left", padx=2)
   
    def toggle_expand(self, expanded_var: ctk.BooleanVar, chevron: ctk.CTkLabel, container: ctk.CTkFrame, card: ctk.CTkFrame):
        """Gérer l'expansion/réduction d'un dossier"""
        expanded = not expanded_var.get()
        expanded_var.set(expanded)
        chevron.configure(text='▼' if expanded else '▶')
        if expanded:
            container.pack(fill="x", pady=0, after=card)
        else:
            container.pack_forget()
   
    def on_drop(self, event):
        """Gérer le drop d'un dossier"""
        path = event.data
       
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
       
        path = path.strip()
       
        if not os.path.isdir(path):
            messagebox.showerror(
                "Erreur",
                "❌ Veuillez déposer un dossier, pas un fichier."
            )
            return
       
        folder_name = os.path.basename(path)
        response = messagebox.askyesno(
            "Confirmation",
            f"📁 Voulez-vous importer le dossier :\n\n{folder_name}\n\n"
            f"✅ Dans le panel: {self.panel_info['name']}\n"
            "✅ Tous les fichiers (.pdf, .docx, .xlsx)\n"
            "✅ L'arborescence complète",
            icon='question'
        )
       
        if response:
            self.import_folder_path(path)
   
    def import_folder_path(self, folder_path: str):
        try:
            # Compter les fichiers à importer d'abord
            total_files = self.file_handler.count_files_to_import(folder_path)
            if total_files == 0:
                messagebox.showwarning(
                    "Attention",
                    "⚠️ Aucun fichier valide à importer dans ce dossier"
                )
                return
           
            # Fenêtre de progression avec barre
            progress_window = ctk.CTkToplevel(self.root)
            progress_window.title("Importation en cours...")
            progress_window.geometry("600x300")  # Augmenté pour plus d'espace
            progress_window.transient(self.root)
            progress_window.grab_set()
           
            # Centrer
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - 300
            y = (progress_window.winfo_screenheight() // 2) - 150
            progress_window.geometry(f'600x300+{x}+{y}')
           
            # Titre
            ctk.CTkLabel(
                progress_window,
                text="⏳ Importation en cours...",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=("#1f538d", "#00aaff")
            ).pack(pady=20)
           
            # Barre de progression
            self.progress_bar = ctk.CTkProgressBar(
                progress_window,
                width=500,
                height=20,
                mode="determinate"
            )
            self.progress_bar.pack(pady=10)
            self.progress_bar.set(0)
           
            # Label statut
            self.status_label = ctk.CTkLabel(
                progress_window,
                text=f"Préparation... (0/{total_files} fichiers)",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray60")
            )
            self.status_label.pack(pady=10)
           
            # Infos supplémentaires
            ctk.CTkLabel(
                progress_window,
                text="✅ Tous les fichiers (.docx, .pdf, .xlsx)\n"
                    "✅ L'arborescence complète\n"
                    "✅ Les sous-dossiers automatiquement",
                font=ctk.CTkFont(size=12),
                text_color=("#28a745", "#4ade80")
            ).pack(pady=15)
           
            progress_window.update()
           
            # Callback de progression
            def progress_callback(current, total):
                progress = current / total
                self.progress_bar.set(progress)
                self.status_label.configure(text=f"Importation... ({current}/{total} fichiers)")
                progress_window.update_idletasks()
           
            # Importer dans le panel spécifique
            print(f"\n{'='*70}")
            print(f"🚀 IMPORT PANEL {self.panel}: {folder_path}")
            print(f"{'='*70}")
           
            count = self.file_handler.save_files_from_folder_with_panel(
                folder_path, self.db, None, self.panel, progress_callback=progress_callback, total=total_files
            )
           
            print(f"{'='*70}")
            print(f"✅ FIN: {count} fichiers")
            print(f"{'='*70}\n")
           
            progress_window.destroy()
           
            if count > 0:
                messagebox.showinfo(
                    "Succès",
                    f"✅ Importation réussie dans {self.panel_info['name']} !\n\n"
                    f"📊 {count} fichier(s) importé(s)\n"
                    f"📁 {os.path.basename(folder_path)}"
                )
            else:
                messagebox.showwarning(
                    "Attention",
                    f"⚠️ Aucun fichier importé\n\n"
                    f"Formats acceptés: PDF, Word, Excel"
                )
           
            self.load_folders()
            self.on_changes()
           
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Erreur", f"❌ Impossible d'importer:\n\n{e}")
            import traceback
            traceback.print_exc()
   
    def create_folder(self):
        """Créer un nouveau dossier dans le panel"""
        dialog = ctk.CTkInputDialog(
            text=f"Nom du dossier dans {self.panel_info['name']}:",
            title="Nouveau Dossier"
        )
        name = dialog.get_input()
       
        if name and name.strip():
            try:
                self.db.create_folder(name.strip(), None, self.panel)
                messagebox.showinfo("Succès", f"✅ Dossier créé dans {self.panel_info['name']}")
                self.load_folders()
                self.on_changes()
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible de créer:\n{e}")
   
    def add_subfolder(self, parent_id: int):
        """Ajouter un sous-dossier"""
        dialog = ctk.CTkInputDialog(
            text="Nom du sous-dossier:",
            title="Nouveau Sous-Dossier"
        )
        name = dialog.get_input()
       
        if name and name.strip():
            try:
                # Le panel est hérité automatiquement du parent
                self.db.create_folder(name.strip(), parent_id)
                messagebox.showinfo("Succès", "✅ Sous-dossier créé")
                self.load_folders()
                self.on_changes()
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible de créer:\n{e}")
   
    def rename_folder(self, folder_id: int):
        """Renommer un dossier"""
        folder = self.db.get_folder(folder_id)
        if not folder:
            messagebox.showerror("Erreur", "❌ Dossier introuvable")
            return
       
        dialog = ctk.CTkInputDialog(
            text="Nouveau nom:",
            title="Renommer le Dossier"
        )
        dialog.get_input() # Ouvrir le dialogue
        dialog._entry.delete(0, "end")
        dialog._entry.insert(0, folder['name'])
       
        new_name = dialog.get_input()
       
        if new_name and new_name.strip():
            try:
                self.db.update_folder(folder_id, new_name.strip())
                messagebox.showinfo("Succès", "✅ Dossier renommé")
                self.load_folders()
                self.on_changes()
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible de renommer:\n{e}")
   
    def delete_folder(self, folder_id: int):
        """Supprimer un dossier"""
        folder = self.db.get_folder(folder_id)
        if not folder:
            messagebox.showerror("Erreur", "❌ Dossier introuvable")
            return
       
        response = messagebox.askyesno(
            "Confirmation",
            f"⚠️ Supprimer '{folder['name']}' ?\n\n"
            "Tous les fichiers et sous-dossiers seront supprimés.",
            icon='warning'
        )
       
        if response:
            try:
                self.db.delete_folder(folder_id)
                messagebox.showinfo("Succès", "✅ Dossier supprimé")
                self.load_folders()
                self.on_changes()
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible de supprimer:\n{e}")
   
    def manage_files(self, folder_id: int):
        """Gérer les fichiers d'un dossier"""
        folder = self.db.get_folder(folder_id)
        if not folder:
            messagebox.showerror("Erreur", "❌ Dossier introuvable")
            return
       
        file_window = ctk.CTkToplevel(self.root)
        FileManagerWindow(file_window, self.db, self.file_handler, folder, self.on_changes)
   
    def import_folder(self):
        """Importer un dossier"""
        folder_path = filedialog.askdirectory(title="Sélectionner un dossier")
       
        if not folder_path:
            return
       
        response = messagebox.askyesno(
            "Confirmation",
            f"📁 Importer:\n\n{folder_path}\n\n"
            f"✅ Dans le panel: {self.panel_info['name']}\n"
            "✅ Tous les fichiers\n"
            "✅ Tous les sous-dossiers\n"
            "✅ Arborescence complète",
            icon='question'
        )
       
        if response:
            self.import_folder_path(folder_path)
   
    def import_files(self):
        """Importer des fichiers directement (NOUVEAU - SANS SÉLECTION DE DOSSIER OBLIGATOIRE)"""
       
        # Récupérer les dossiers existants
        folders = self.db.get_all_folders(panel=self.panel)
       
        # Créer une fenêtre de sélection
        selector = ctk.CTkToplevel(self.root)
        selector.title("Importer des fichiers")
        selector.geometry("500x600")
        selector.transient(self.root)
        selector.grab_set()
       
        # Centrer
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 250
        y = (selector.winfo_screenheight() // 2) - 300
        selector.geometry(f'500x600+{x}+{y}')
       
        # En-tête
        header = ctk.CTkFrame(
            selector,
            height=80,
            fg_color=(self.panel_info['color'], self.panel_info['color']),
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)
       
        ctk.CTkLabel(
            header,
            text=f"📄 Importer des fichiers",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(pady=25)
       
        # Instructions
        instructions = ctk.CTkFrame(
            selector,
            fg_color=("#e7f3ff", "#1a3a52"),
            corner_radius=15
        )
        instructions.pack(fill="x", padx=20, pady=20)
       
        ctk.CTkLabel(
            instructions,
            text=f"📌 Choisissez la destination dans {self.panel_info['name']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1f538d", "#2563a8")
        ).pack(pady=(15, 5))
       
        ctk.CTkLabel(
            instructions,
            text="Vous pouvez importer à la racine ou dans un dossier existant",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(pady=(0, 15))
       
        # Variable pour stocker la sélection
        selected_folder_id = [None] # None = racine
       
        # Frame scrollable pour les options
        scroll_frame = ctk.CTkScrollableFrame(
            selector,
            fg_color=("gray90", "gray20")
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
       
        # Option 1: Importer à la racine (NOUVEAU)
        root_option = ctk.CTkFrame(
            scroll_frame,
            fg_color=("#28a745", "#1e7e34"),
            corner_radius=10,
            border_width=2,
            border_color="white"
        )
        root_option.pack(fill="x", pady=10)
       
        root_btn = ctk.CTkButton(
            root_option,
            text=f"🏠 Importer à la racine de {self.panel_info['name']}",
            height=60,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color=("gray80", "gray40"),
            text_color="white",
            command=lambda: [
                selected_folder_id.__setitem__(0, None),
                selector.destroy(),
                self.select_and_import_files(None)
            ]
        )
        root_btn.pack(fill="x", padx=10, pady=10)
       
        # Séparateur
        if folders:
            ctk.CTkLabel(
                scroll_frame,
                text="━━━━━━━ ou dans un dossier existant ━━━━━━━",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60")
            ).pack(pady=15)
           
            # Option 2: Dossiers existants
            for folder in folders:
                folder_card = ctk.CTkFrame(
                    scroll_frame,
                    fg_color=("#ffffff", "#2a2a2a"),
                    corner_radius=10,
                    border_width=1,
                    border_color=("gray80", "gray40")
                )
                folder_card.pack(fill="x", pady=5)
               
                folder_btn = ctk.CTkButton(
                    folder_card,
                    text=f"📁 {folder['name']}",
                    height=50,
                    font=ctk.CTkFont(size=13),
                    fg_color="transparent",
                    hover_color=("gray90", "gray30"),
                    text_color=("black", "white"),
                    anchor="w",
                    command=lambda fid=folder['id']: [
                        selected_folder_id.__setitem__(0, fid),
                        selector.destroy(),
                        self.select_and_import_files(fid)
                    ]
                )
                folder_btn.pack(fill="x", padx=10, pady=10)
       
        # Bouton annuler
        ctk.CTkButton(
            selector,
            text="❌ Annuler",
            width=200,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#dc3545", "#b02a37"),
            hover_color=("#e04555", "#c03545"),
            command=selector.destroy
        ).pack(pady=(0, 20))
   
    def select_and_import_files(self, folder_id: Optional[int]):
        """Sélectionner et importer les fichiers dans le dossier spécifié (ou racine si None)"""
       
        # Sélectionner les fichiers
        file_paths = filedialog.askopenfilenames(
            title="Sélectionner des fichiers à importer",
            filetypes=[
                ("Tous supportés", "*.pdf *.docx *.xlsx *.doc *.xls"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx *.doc"),
                ("Excel", "*.xlsx *.xls"),
                ("Tous", "*.*")
            ]
        )
       
        if not file_paths:
            return
       
        try:
            success_count = 0
            error_count = 0
           
            # Si folder_id est None, créer un dossier "Fichiers importés" à la racine
            if folder_id is None:
                from datetime import datetime
                folder_name = f"Fichiers importés - {datetime.now().strftime('%d-%m-%Y %H-%M')}"
                folder_id = self.db.create_folder(folder_name, None, self.panel)
                print(f"✅ Dossier créé pour l'import: {folder_name}")
           
            # Récupérer les infos du dossier
            folder = self.db.get_folder(folder_id)
            folder_name = folder['name'] if folder else "Racine"
           
            for file_path in file_paths:
                filename = os.path.basename(file_path)
               
                if self.file_handler.is_allowed_file(filename):
                    # Sauvegarder le fichier
                    success, dest_path = self.file_handler.save_file(
                        file_path,
                        filename,
                        folder_name
                    )
                   
                    if success:
                        self.db.add_file(folder_id, filename, dest_path)
                        success_count += 1
                        print(f"✅ Fichier importé: {filename}")
                    else:
                        error_count += 1
                        print(f"❌ Échec import: {filename}")
                else:
                    error_count += 1
                    print(f"⚠️ Extension non autorisée: {filename}")
           
            # Messages de résultat
            if error_count == 0:
                messagebox.showinfo(
                    "Succès",
                    f"✅ {success_count} fichier(s) importé(s) avec succès\n\n"
                    f"📁 Destination: {folder_name}\n"
                    f"📂 Panel: {self.panel_info['name']}"
                )
            else:
                messagebox.showwarning(
                    "Attention",
                    f"✅ {success_count} fichier(s) importé(s)\n"
                    f"⚠️ {error_count} fichier(s) non importé(s)\n\n"
                    f"Seuls les formats PDF, Word et Excel sont acceptés"
                )
           
            # Rafraîchir l'affichage
            self.load_folders()
            self.on_changes()
           
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible d'importer les fichiers:\n\n{e}")
            import traceback
            traceback.print_exc()
class FileManagerWindow:
    """Fenêtre de gestion des fichiers modernisée"""
   
    def __init__(self, root: ctk.CTkToplevel, db, file_handler, folder: dict, on_changes: Callable):
        self.root = root
        self.db = db
        self.file_handler = file_handler
        self.folder = folder
        self.on_changes = on_changes
       
        self.root.title(f"Fichiers - {folder['name']}")
        self.root.geometry("900x650")
       
        self.center_window()
        self.create_widgets()
        self.load_files()
   
    def center_window(self):
        """Centrer la fenêtre"""
        self.root.update_idletasks()
        width = 900
        height = 650
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
   
    def create_widgets(self):
        """Créer les widgets"""
        # En-tête
        header = ctk.CTkFrame(
            self.root,
            height=80,
            corner_radius=0,
            fg_color=("#17a2b8", "#138496")
        )
        header.pack(fill="x")
        header.pack_propagate(False)
       
        ctk.CTkLabel(
            header,
            text=f"📄 Fichiers - {self.folder['name']}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#ffffff", "#ffffff")
        ).pack(side="left", padx=30, pady=20)
       
        ctk.CTkButton(
            header,
            text="✖️ Fermer",
            width=120,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#dc3545", "#b02a37"),
            hover_color=("#e04555", "#c03545"),
            command=self.root.destroy
        ).pack(side="right", padx=30)
       
        # Toolbar
        toolbar = ctk.CTkFrame(self.root, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=15)
       
        buttons = [
            ("➕ Ajouter", "#28a745", "#1e7e34", self.add_files),
            ("🗑️ Supprimer", "#dc3545", "#b02a37", self.delete_file),
            ("👁️ Ouvrir", "#1f538d", "#14375e", self.open_file),
            ("🔄 Rafraîchir", "#6c757d", "#5a6268", self.load_files)
        ]
       
        for text, fg_color, hover_color, command in buttons:
            ctk.CTkButton(
                toolbar,
                text=text,
                width=140,
                height=45,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=fg_color,
                hover_color=hover_color,
                command=command
            ).pack(side="left", padx=5)
       
        # Liste des fichiers
        self.files_list = ctk.CTkScrollableFrame(
            self.root,
            fg_color=("#f0f0f0", "#2b2b2b"),
            corner_radius=15
        )
        self.files_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))
       
        self.selected_file_id = None
   
    def load_files(self):
        """Charger les fichiers"""
        for widget in self.files_list.winfo_children():
            widget.destroy()
       
        files = self.db.get_files_in_folder(self.folder['id'])
       
        if not files:
            ctk.CTkLabel(
                self.files_list,
                text="📭 Aucun fichier\n\nAjoutez des fichiers avec le bouton ci-dessus",
                font=ctk.CTkFont(size=16),
                text_color=("gray50", "gray60")
            ).pack(expand=True, pady=100)
            return
       
        for file in files:
            self.create_file_card(file)
   
    def create_file_card(self, file: dict):
        """Créer une carte de fichier"""
        extension = file['filename'].rsplit('.', 1)[-1].lower() if '.' in file['filename'] else ''
        icon = self.file_handler.get_file_icon(extension)
       
        card = ctk.CTkFrame(
            self.files_list,
            height=70,
            fg_color=("#ffffff", "#1e1e1e"),
            corner_radius=10,
            border_width=1,
            border_color=("gray80", "gray30")
        )
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)
       
        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=28),
            width=60
        ).pack(side="left", padx=20)
       
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10)
       
        ctk.CTkLabel(
            info_frame,
            text=file['filename'],
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(anchor="w")
       
        try:
            size = os.path.getsize(file['filepath']) if os.path.exists(file['filepath']) else 0
            size_formatted = self.format_file_size(size)
        except:
            size_formatted = "N/A"
       
        is_pdf = self.file_handler.is_pdf(file['filename'])
        type_text = f"{size_formatted} • {'🔒 PDF' if is_pdf else '💾 Téléchargeable'}"
       
        ctk.CTkLabel(
            info_frame,
            text=type_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w"
        ).pack(anchor="w")
       
        # Bouton sélectionner
        select_btn = ctk.CTkButton(
            card,
            text="✓ Sélectionner",
            width=130,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#1f538d", "#14375e"),
            hover_color=("#2563a8", "#1a4a7a"),
            command=lambda: self.select_file(file['id'], card)
        )
        select_btn.pack(side="right", padx=15)
       
        # Double-clic pour ouvrir
        card.bind('<Double-Button-1>', lambda e: self.open_file())
   
    def select_file(self, file_id: int, card: ctk.CTkFrame):
        """Sélectionner un fichier"""
        self.selected_file_id = file_id
       
        # Réinitialiser toutes les cartes
        for widget in self.files_list.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(border_color=("gray80", "gray30"), border_width=1)
       
        # Mettre en surbrillance la carte sélectionnée
        card.configure(border_color=("#1f538d", "#2563a8"), border_width=3)
   
    def add_files(self):
        """Ajouter des fichiers"""
        file_paths = filedialog.askopenfilenames(
            title="Sélectionner des fichiers",
            filetypes=[
                ("Tous supportés", "*.pdf *.docx *.xlsx *.doc *.xls"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx *.doc"),
                ("Excel", "*.xlsx *.xls"),
                ("Tous", "*.*")
            ]
        )
       
        if not file_paths:
            return
       
        try:
            success_count = 0
            error_count = 0
           
            for file_path in file_paths:
                filename = os.path.basename(file_path)
               
                if self.file_handler.is_allowed_file(filename):
                    success, dest_path = self.file_handler.save_file(
                        file_path,
                        filename,
                        self.folder['name']
                    )
                   
                    if success:
                        self.db.add_file(self.folder['id'], filename, dest_path)
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
           
            if error_count == 0:
                messagebox.showinfo(
                    "Succès",
                    f"✅ {success_count} fichier(s) ajouté(s)"
                )
            else:
                messagebox.showwarning(
                    "Attention",
                    f"✅ {success_count} ajouté(s)\n"
                    f"⚠️ {error_count} erreur(s)"
                )
           
            self.load_files()
            self.on_changes()
           
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible d'ajouter:\n{e}")
   
    def delete_file(self):
        """Supprimer le fichier sélectionné"""
        if not self.selected_file_id:
            messagebox.showwarning("Attention", "⚠️ Veuillez sélectionner un fichier")
            return
       
        file = self.db.get_file(self.selected_file_id)
        if not file:
            messagebox.showerror("Erreur", "❌ Fichier introuvable")
            return
       
        response = messagebox.askyesno(
            "Confirmation",
            f"⚠️ Supprimer :\n\n{file['filename']} ?",
            icon='warning'
        )
       
        if response:
            try:
                self.db.delete_file(self.selected_file_id)
                messagebox.showinfo("Succès", "✅ Fichier supprimé")
                self.selected_file_id = None
                self.load_files()
                self.on_changes()
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Impossible de supprimer:\n{e}")
   
    def open_file(self):
        """Ouvrir le fichier sélectionné"""
        if not self.selected_file_id:
            messagebox.showwarning("Attention", "⚠️ Veuillez sélectionner un fichier")
            return
       
        file = self.db.get_file(self.selected_file_id)
        if not file:
            messagebox.showerror("Erreur", "❌ Fichier introuvable")
            return
       
        if not os.path.exists(file['filepath']):
            messagebox.showerror("Erreur", "❌ Le fichier n'existe pas")
            return
       
        success = self.file_handler.open_file(file['filepath'])
        if not success:
            messagebox.showerror("Erreur", "❌ Impossible d'ouvrir le fichier")
   
    @staticmethod
    def format_file_size(size: int) -> str:
        """Formater la taille d'un fichier"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
