# ui/panel_view.py (modifications pour import direct)
import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Callable, Optional, List, Dict, Any
import os
import threading

class PanelView(ctk.CTkFrame):
    """Vue d'un panel avec import direct optimisé"""
    
    def __init__(self, parent, db, file_handler, panel: str, 
                 folder_id: Optional[int] = None,
                 on_folder_open: Callable = None,
                 notification_manager = None):
        super().__init__(parent)
        
        self.db = db
        self.file_handler = file_handler
        self.panel = panel
        self.folder_id = folder_id
        self.on_folder_open = on_folder_open
        self.notification_manager = notification_manager
        
        # Mapping des panels
        self.panel_names = {
            'certification': 'Certification',
            'entete': 'En-tête',
            'interface_emp': 'Interface Employés',
            'autre': 'Autre'
        }
        
        self.create_widgets()
        self.refresh_content()
    
    def create_widgets(self):
        """Créer l'interface du panel"""
        # En-tête du panel
        header = ctk.CTkFrame(self, fg_color=("#f0f8ff", "#1a2a3a"), corner_radius=15)
        header.pack(fill="x", pady=(0, 20))
        
        # Titre et informations
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=15)
        
        panel_name = self.panel_names.get(self.panel, self.panel)
        
        if self.folder_id is None:
            title_text = f"📁 {panel_name}"
            subtitle_text = "Racine du panel"
        else:
            folder = self.db.get_folder(self.folder_id)
            title_text = f"📂 {folder['name'] if folder else 'Dossier Inconnu'}"
            subtitle_text = f"Dans {panel_name}"
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#2563a8")
        )
        title_label.pack(side="left")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text=subtitle_text,
            font=ctk.CTkFont(size=14),
            text_color=("#666666", "#999999")
        )
        subtitle_label.pack(side="left", padx=(10, 0))
        
        # Boutons d'action
        action_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        action_frame.pack(side="right")
        
        # NOUVEAU: Bouton Import Direct
        self.import_direct_button = ctk.CTkButton(
            action_frame,
            text="⚡ Import Direct",
            width=140,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#FF6B35", "#E55A2B"),
            hover_color=("#FF7A45", "#F5632F"),
            command=self.import_files_direct
        )
        self.import_direct_button.pack(side="left", padx=5)
        
        # Bouton Import Dossier (ancien comportement)
        self.import_folder_button = ctk.CTkButton(
            action_frame,
            text="📁 Import Dossier",
            width=140,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#28a745", "#1e7e34"),
            hover_color=("#32b349", "#229143"),
            command=self.import_folder
        )
        self.import_folder_button.pack(side="left", padx=5)
        
        # Bouton Nouveau Dossier
        self.new_folder_button = ctk.CTkButton(
            action_frame,
            text="➕ Nouveau",
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#1f538d", "#14375e"),
            hover_color=("#2563a8", "#1a4a7a"),
            command=self.create_new_folder
        )
        self.new_folder_button.pack(side="left", padx=5)
        
        # Zone de contenu avec scroll
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=("white", "gray10"),
            corner_radius=15
        )
        self.content_frame.pack(fill="both", expand=True)
    
    def import_files_direct(self):
        """Import direct de fichiers sans créer de dossier parent"""
        try:
            # Boîte de dialogue pour choisir fichiers ou dossier
            choice = messagebox.askyesnocancel(
                "Import Direct",
                "Choisissez le mode d'import:\n\n" +
                "• OUI = Importer des fichiers individuels\n" +
                "• NON = Importer un dossier complet\n" +
                "• ANNULER = Annuler l'opération",
                icon='question'
            )
            
            if choice is None:  # Annuler
                return
            elif choice:  # Fichiers individuels
                file_paths = filedialog.askopenfilenames(
                    title="Sélectionner les fichiers à importer directement",
                    filetypes=[
                        ("Fichiers autorisés", "*.pdf *.docx *.xlsx *.doc *.xls"),
                        ("PDF", "*.pdf"),
                        ("Word", "*.docx *.doc"),
                        ("Excel", "*.xlsx *.xls"),
                        ("Tous les fichiers", "*.*")
                    ]
                )
                
                if not file_paths:
                    return
                
                # Créer une fenêtre de progression
                progress_window = self.create_progress_window("Import direct de fichiers")
                
                # Démarrer l'import dans un thread
                threading.Thread(
                    target=self._import_files_worker,
                    args=(file_paths, progress_window, True),
                    daemon=True
                ).start()
                
            else:  # Dossier complet
                folder_path = filedialog.askdirectory(
                    title="Sélectionner le dossier à importer directement"
                )
                
                if not folder_path:
                    return
                
                # Créer une fenêtre de progression
                progress_window = self.create_progress_window("Import direct de dossier")
                
                # Démarrer l'import dans un thread
                threading.Thread(
                    target=self._import_files_worker,
                    args=([folder_path], progress_window, False),
                    daemon=True
                ).start()
                
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de l'import direct:\n{e}")
    
    def import_folder(self):
        """Import traditionnel avec création d'un dossier parent"""
        try:
            folder_path = filedialog.askdirectory(
                title="Sélectionner le dossier à importer"
            )
            
            if not folder_path:
                return
            
            # Créer une fenêtre de progression
            progress_window = self.create_progress_window("Import de dossier avec structure")
            
            # Démarrer l'import dans un thread
            threading.Thread(
                target=self._import_folder_traditional_worker,
                args=(folder_path, progress_window),
                daemon=True
            ).start()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur lors de l'import de dossier:\n{e}")
    
    def create_progress_window(self, title: str):
        """Créer une fenêtre de progression"""
        progress_window = ctk.CTkToplevel(self)
        progress_window.title(title)
        progress_window.geometry("400x200")
        progress_window.transient(self.winfo_toplevel())
        progress_window.grab_set()
        
        # Centrer la fenêtre
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - 200
        y = (progress_window.winfo_screenheight() // 2) - 100
        progress_window.geometry(f'400x200+{x}+{y}')
        
        # Contenu
        ctk.CTkLabel(
            progress_window,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        progress_label = ctk.CTkLabel(
            progress_window,
            text="Préparation...",
            font=ctk.CTkFont(size=12)
        )
        progress_label.pack(pady=10)
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=300)
        progress_bar.pack(pady=20)
        progress_bar.set(0)
        
        status_label = ctk.CTkLabel(
            progress_window,
            text="",
            font=ctk.CTkFont(size=10)
        )
        status_label.pack()
        
        return {
            'window': progress_window,
            'label': progress_label,
            'bar': progress_bar,
            'status': status_label
        }
    
    def _import_files_worker(self, paths: List[str], progress_window: dict, individual_files: bool):
        """Worker pour l'import direct de fichiers"""
        try:
            total_imported = 0
            total_files = 0
            
            # Compter le nombre total de fichiers
            for path in paths:
                if individual_files or os.path.isfile(path):
                    if self.file_handler.is_allowed_file(os.path.basename(path)):
                        total_files += 1
                else:
                    total_files += self.file_handler._count_files_recursive(path)
            
            current_count = 0
            
            def update_progress(current, total):
                nonlocal current_count
                current_count = current
                try:
                    progress = current / max(total, 1)
                    progress_window['bar'].set(progress)
                    progress_window['label'].configure(text=f"Importation: {current}/{total} fichiers")
                    progress_window['status'].configure(text=f"Progression: {progress*100:.1f}%")
                except:
                    pass
            
            # Effectuer l'import
            if individual_files:
                # Import de fichiers individuels
                for file_path in paths:
                    if self.file_handler.is_allowed_file(os.path.basename(file_path)):
                        success = self._import_single_file_direct(file_path, update_progress, current_count, total_files)
                        if success:
                            total_imported += 1
                            current_count += 1
            else:
                # Import de dossiers
                for folder_path in paths:
                    imported = self.file_handler.save_files_from_folder_direct(
                        folder_path, 
                        self.db, 
                        self.panel, 
                        update_progress
                    )
                    total_imported += imported
            
            # Fermer la fenêtre de progression et rafraîchir
            self.after(0, lambda: self._finalize_import(progress_window, total_imported))
            
        except Exception as e:
            self.after(0, lambda: self._handle_import_error(progress_window, e))
    
    def _import_single_file_direct(self, file_path: str, progress_callback, current: int, total: int) -> bool:
        """Importer un fichier unique directement"""
        try:
            filename = os.path.basename(file_path)
            
            # Obtenir ou créer le dossier racine du panel
            root_folders = self.db.get_subfolders(parent_id=None, panel=self.panel)
            if not root_folders:
                root_folder_id = self.db.create_folder(
                    self.panel_names[self.panel], None, self.panel
                )
            else:
                root_folder_id = root_folders[0]['id']
            
            # Sauvegarder le fichier crypté
            success, dest_path = self.file_handler.save_file(file_path, filename, self.panel)
            
            if success:
                # Enregistrer dans la base de données
                target_folder_id = self.folder_id if self.folder_id else root_folder_id
                self.db.add_file(target_folder_id, filename, dest_path)
                
                if progress_callback:
                    progress_callback(current + 1, total)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur import fichier direct {file_path}: {e}")
            return False
    
    def _import_folder_traditional_worker(self, folder_path: str, progress_window: dict):
        """Worker pour l'import traditionnel avec dossier parent"""
        try:
            total_files = self.file_handler._count_files_recursive(folder_path)
            
            def update_progress(current, total):
                try:
                    progress = current / max(total, 1)
                    progress_window['bar'].set(progress)
                    progress_window['label'].configure(text=f"Importation: {current}/{total} fichiers")
                    progress_window['status'].configure(text=f"Progression: {progress*100:.1f}%")
                except:
                    pass
            
            # Effectuer l'import traditionnel
            total_imported = self.file_handler.save_files_from_folder_with_panel(
                folder_path,
                self.db,
                self.folder_id,
                self.panel,
                update_progress,
                total_files
            )
            
            # Fermer la fenêtre de progression et rafraîchir
            self.after(0, lambda: self._finalize_import(progress_window, total_imported))
            
        except Exception as e:
            self.after(0, lambda: self._handle_import_error(progress_window, e))
    
    def _finalize_import(self, progress_window: dict, total_imported: int):
        """Finaliser l'import"""
        try:
            progress_window['window'].destroy()
            
            if total_imported > 0:
                messagebox.showinfo(
                    "Import Réussi",
                    f"✅ {total_imported} fichier(s) importé(s) avec succès!"
                )
                
                if self.notification_manager:
                    self.notification_manager.show_app_notification(
                        "📥 Import Terminé",
                        f"{total_imported} fichier(s) importé(s)"
                    )
                
                # Rafraîchir l'affichage
                self.refresh_content()
            else:
                messagebox.showwarning(
                    "Import Vide",
                    "⚠️ Aucun fichier valide n'a été trouvé pour l'import."
                )
                
        except Exception as e:
            print(f"❌ Erreur finalisation import: {e}")
    
    def _handle_import_error(self, progress_window: dict, error):
        """Gérer les erreurs d'import"""
        try:
            progress_window['window'].destroy()
            messagebox.showerror("Erreur Import", f"❌ Erreur lors de l'import:\n{error}")
        except:
            pass
    
    def create_new_folder(self):
        """Créer un nouveau dossier"""
        try:
            dialog = ctk.CTkInputDialog(
                text="Nom du nouveau dossier:",
                title="Créer un Dossier"
            )
            folder_name = dialog.get_input()
            
            if folder_name and folder_name.strip():
                folder_id = self.db.create_folder(
                    folder_name.strip(), 
                    self.folder_id, 
                    self.panel
                )
                
                if self.notification_manager:
                    self.notification_manager.show_app_notification(
                        "📁 Dossier Créé",
                        f"Dossier '{folder_name}' créé"
                    )
                
                self.refresh_content()
                
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible de créer le dossier:\n{e}")
    
    def refresh_content(self):
        """Rafraîchir le contenu du panel"""
        try:
            # Nettoyer le contenu actuel
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Récupérer les dossiers et fichiers
            folders = self.db.get_subfolders(self.folder_id, self.panel)
            files = self.db.get_files_in_folder(self.folder_id) if self.folder_id else []
            
            if not folders and not files:
                # Affichage d'état vide
                empty_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                empty_frame.pack(expand=True, pady=50)
                
                ctk.CTkLabel(
                    empty_frame,
                    text="📁",
                    font=ctk.CTkFont(size=64)
                ).pack()
                
                ctk.CTkLabel(
                    empty_frame,
                    text="Dossier Vide",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=("gray50", "gray60")
                ).pack(pady=(10, 5))
                
                ctk.CTkLabel(
                    empty_frame,
                    text="Utilisez 'Import Direct' pour ajouter des fichiers",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray60")
                ).pack()
                return
            
            # Afficher les dossiers
            if folders:
                folders_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                folders_frame.pack(fill="x", pady=10)
                
                ctk.CTkLabel(
                    folders_frame,
                    text="📁 Dossiers",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(0, 10))
                
                # Grille de dossiers
                folders_grid = ctk.CTkFrame(folders_frame, fg_color="transparent")
                folders_grid.pack(fill="x", padx=10)
                
                for i, folder in enumerate(folders):
                    self.create_folder_card(folders_grid, folder, i)
            
            # Afficher les fichiers
            if files:
                files_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                files_frame.pack(fill="x", pady=10)
                
                ctk.CTkLabel(
                    files_frame,
                    text="📄 Fichiers",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(0, 10))
                
                # Liste des fichiers
                for file in files:
                    self.create_file_card(files_frame, file)
                    
        except Exception as e:
            print(f"❌ Erreur rafraîchissement contenu: {e}")
    
    def create_folder_card(self, parent, folder: Dict[str, Any], index: int):
        """Créer une carte pour un dossier"""
        row = index // 3
        col = index % 3
        
        card = ctk.CTkFrame(
            parent,
            width=200,
            height=100,
            fg_color=("white", "gray20"),
            corner_radius=10,
            border_width=1,
            border_color=("gray80", "gray40")
        )
        card.grid(row=row, col=col, padx=10, pady=5, sticky="ew")
        
        # Icône et nom
        ctk.CTkLabel(
            card,
            text="📁",
            font=ctk.CTkFont(size=32)
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            card,
            text=folder['name'][:20] + "..." if len(folder['name']) > 20 else folder['name'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1f538d", "#2563a8")
        ).pack()
        
        # Compteur de fichiers
        file_count = self.db.count_files_in_folder(folder['id'], recursive=True)
        ctk.CTkLabel(
            card,
            text=f"{file_count} fichier(s)",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        ).pack()
        
        # Événements
        card.bind('<Double-Button-1>', lambda e, f_id=folder['id']: self.open_folder(f_id))
        
        # Hover effect
        def on_enter(e):
            card.configure(border_color=("#1f538d", "#2563a8"), border_width=2)
        
        def on_leave(e):
            card.configure(border_color=("gray80", "gray40"), border_width=1)
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
    
    def create_file_card(self, parent, file: Dict[str, Any]):
        """Créer une carte pour un fichier"""
        # Récupérer le nom original pour les fichiers cryptés
        if hasattr(self.file_handler, 'get_original_filename'):
            display_name = self.file_handler.get_original_filename(file['filepath'])
        else:
            display_name = file['filename']
        
        extension = display_name.rsplit('.', 1)[-1].lower() if '.' in display_name else ''
        icon = self.file_handler.get_file_icon(extension)
        is_pdf = extension == 'pdf'
        
        card = ctk.CTkFrame(
            parent,
            height=70,
            fg_color=("white", "gray20"),
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray40")
        )
        card.pack(fill="x", padx=10, pady=3)
        card.pack_propagate(False)
        
        # Icône
        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=28),
            width=60
        ).pack(side="left", padx=10)
        
        # Informations du fichier
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Nom du fichier
        name_label = ctk.CTkLabel(
            info_frame,
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x")
        
        # Métadonnées
        size_text = self.file_handler.format_file_size(file.get('file_size', 0))
        type_text = "🔒 PDF (Lecture seule)" if is_pdf else "💾 Document (Téléchargeable)"
        
        meta_label = ctk.CTkLabel(
            info_frame,
            text=f"{type_text} • {size_text}",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
            anchor="w"
        )
        meta_label.pack(fill="x")
        
        # Boutons d'action
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(side="right", padx=10)
        
        # Bouton Ouvrir
        action_text = "👁️ Voir" if is_pdf else "📥 Ouvrir"
        open_btn = ctk.CTkButton(
            button_frame,
            text=action_text,
            width=80,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#1f538d", "#14375e"),
            hover_color=("#2563a8", "#1a4a7a"),
            command=lambda f=file: self.open_file(f)
        )
        open_btn.pack(pady=2)
        
        # Double-clic pour ouvrir
        card.bind('<Double-Button-1>', lambda e, f=file: self.open_file(f))
    
    def open_folder(self, folder_id: int):
        """Ouvrir un dossier"""
        if self.on_folder_open:
            self.on_folder_open(folder_id)
    
    def open_file(self, file: Dict[str, Any]):
        """Ouvrir un fichier"""
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
                pdf_window = ctk.CTkToplevel(self.winfo_toplevel())
                PDFViewer(pdf_window, file['filepath'], display_name)
            else:
                # Pour les autres fichiers, utiliser le gestionnaire de fichiers
                success = self.file_handler.open_file(file['filepath'])
                if not success:
                    messagebox.showerror("Erreur", "❌ Impossible d'ouvrir le fichier")
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Impossible d'ouvrir le fichier:\n{e}")

