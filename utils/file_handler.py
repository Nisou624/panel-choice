# utils/file_handler.py
import os
import shutil
import subprocess
import platform
from typing import Tuple, Optional
from pathlib import Path
from cryptography.fernet import Fernet
import json
import base64

class FileHandler:
    """Gestionnaire de fichiers avec cryptage et structure invisible optimisée"""
    
    # Extensions autorisées
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.doc', '.xls'}
    
    # Icônes par extension
    FILE_ICONS = {
        'pdf': '📕',
        'docx': '📘',
        'doc': '📘',
        'xlsx': '📗',
        'xls': '📗',
        'txt': '📄',
        'default': '📄'
    }
    
    # Structure des panels
    PANEL_FOLDERS = {
        'certification': 'Certification',
        'entete': 'En-tête', 
        'interface_emp': 'Interface Employés',
        'autre': 'Autre'
    }
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.crypto_dir = os.path.join(upload_dir, ".encrypted")
        self.metadata_file = os.path.join(upload_dir, ".metadata.json")
        
        # Initialiser le cryptage
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        self.ensure_directory_structure()
        self.load_metadata()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Générer ou récupérer la clé de chiffrement"""
        key_file = os.path.join(self.upload_dir, ".encryption.key")
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except:
                pass
        
        # Créer nouvelle clé
        key = Fernet.generate_key()
        os.makedirs(self.upload_dir, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Masquer le fichier de clé sur Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_file, 0x02)
            except:
                pass
                
        print("🔑 Nouvelle clé de chiffrement générée")
        return key
    
    def ensure_directory_structure(self):
        """Créer la structure de dossiers invisibles"""
        # Dossier principal
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Dossier de fichiers cryptés
        os.makedirs(self.crypto_dir, exist_ok=True)
        
        # Dossiers pour chaque panel
        for panel_key, panel_name in self.PANEL_FOLDERS.items():
            panel_path = os.path.join(self.crypto_dir, panel_key)
            os.makedirs(panel_path, exist_ok=True)
        
        # Masquer les dossiers système sur Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.crypto_dir, 0x02)
                ctypes.windll.kernel32.SetFileAttributesW(self.metadata_file, 0x02)
            except:
                pass
        
        print("✅ Structure de dossiers invisibles créée")
    
    def load_metadata(self):
        """Charger les métadonnées des fichiers"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except:
            self.metadata = {}
    
    def save_metadata(self):
        """Sauvegarder les métadonnées"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde métadonnées: {e}")
    
    def get_file_icon(self, extension: str) -> str:
        """Récupérer l'icône correspondant à une extension"""
        return self.FILE_ICONS.get(extension.lower(), self.FILE_ICONS['default'])
    
    def is_allowed_file(self, filename: str) -> bool:
        """Vérifier si le fichier est autorisé"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS
    
    def encrypt_file(self, source_path: str) -> bytes:
        """Chiffrer un fichier"""
        try:
            with open(source_path, 'rb') as f:
                file_data = f.read()
            return self.fernet.encrypt(file_data)
        except Exception as e:
            print(f"❌ Erreur chiffrement: {e}")
            raise
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """Déchiffrer un fichier"""
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            print(f"❌ Erreur déchiffrement: {e}")
            raise
    
    def save_file(self, source_path: str, filename: str, panel: str = "interface_emp") -> Tuple[bool, str]:
        """
        Enregistrer un fichier crypté dans la structure invisible
        
        Args:
            source_path: Chemin source du fichier
            filename: Nom du fichier
            panel: Panel de destination
            
        Returns:
            Tuple (succès, chemin_crypté)
        """
        try:
            if not os.path.exists(source_path):
                print(f"❌ Fichier source introuvable: {source_path}")
                return False, ""
            
            if not self.is_allowed_file(filename):
                print(f"❌ Type de fichier non autorisé: {filename}")
                return False, ""
            
            # Générer un nom de fichier crypté unique
            import uuid
            import hashlib
            
            file_id = str(uuid.uuid4())
            original_hash = hashlib.sha256(filename.encode()).hexdigest()[:8]
            encrypted_filename = f"{file_id}_{original_hash}.enc"
            
            # Déterminer le dossier de destination
            panel_dir = os.path.join(self.crypto_dir, panel)
            dest_path = os.path.join(panel_dir, encrypted_filename)
            
            # Chiffrer et sauvegarder le fichier
            encrypted_data = self.encrypt_file(source_path)
            with open(dest_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Sauvegarder les métadonnées
            self.metadata[encrypted_filename] = {
                'original_name': filename,
                'panel': panel,
                'size': os.path.getsize(source_path),
                'created_at': os.path.getctime(source_path),
                'file_id': file_id
            }
            self.save_metadata()
            
            print(f"✅ Fichier crypté sauvegardé: {filename} -> {encrypted_filename}")
            return True, dest_path
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde cryptée: {e}")
            return False, ""
    
    def save_files_from_folder_direct(self, folder_path: str, db, panel: str = 'interface_emp', 
                                    progress_callback=None) -> int:
        """
        Importer des fichiers directement dans un panel sans créer de dossier parent
        
        Args:
            folder_path: Chemin du dossier à importer
            db: Instance de la base de données
            panel: Panel de destination
            progress_callback: Fonction de callback pour la progression
            
        Returns:
            Nombre total de fichiers importés
        """
        total_files = 0
        
        try:
            if not os.path.exists(folder_path):
                print(f"❌ Dossier introuvable: {folder_path}")
                return 0
            
            # Compter le nombre total de fichiers à importer
            total_count = self._count_files_recursive(folder_path)
            current_count = [0]  # Liste mutable pour partager entre fonctions
            
            print(f"📊 Import direct de {total_count} fichiers dans le panel {panel}")
            
            # Obtenir ou créer le dossier racine du panel
            root_folders = db.get_subfolders(parent_id=None, panel=panel)
            if not root_folders:
                # Créer le dossier racine du panel s'il n'existe pas
                root_folder_id = db.create_folder(self.PANEL_FOLDERS[panel], None, panel)
            else:
                root_folder_id = root_folders[0]['id']
            
            # Importer tous les fichiers directement
            if os.path.isfile(folder_path):
                # C'est un fichier unique
                total_files = self._import_single_file(
                    folder_path, db, root_folder_id, panel, progress_callback, total_count, current_count
                )
            else:
                # C'est un dossier - importer récursivement
                total_files = self._import_folder_contents_direct(
                    folder_path, db, root_folder_id, panel, progress_callback, total_count, current_count
                )
            
            print(f"✅ Import direct terminé: {total_files} fichier(s) dans {panel}")
            return total_files
            
        except Exception as e:
            print(f"❌ Erreur lors de l'import direct: {e}")
            import traceback
            traceback.print_exc()
            return total_files
    
    def _count_files_recursive(self, path: str) -> int:
        """Compter récursivement tous les fichiers valides"""
        count = 0
        try:
            if os.path.isfile(path):
                return 1 if self.is_allowed_file(os.path.basename(path)) else 0
            
            for root, dirs, files in os.walk(path):
                for filename in files:
                    if self.is_allowed_file(filename):
                        count += 1
            return count
        except:
            return 0
    
    def _import_single_file(self, file_path: str, db, folder_id: int, panel: str,
                          progress_callback, total: int, current_count: list) -> int:
        """Importer un fichier unique"""
        try:
            filename = os.path.basename(file_path)
            if not self.is_allowed_file(filename):
                return 0
            
            # Sauvegarder le fichier crypté
            success, dest_path = self.save_file(file_path, filename, panel)
            
            if success:
                # Enregistrer dans la base de données
                db.add_file(folder_id, filename, dest_path)
                current_count[0] += 1
                
                if progress_callback:
                    progress_callback(current_count[0], total)
                
                print(f"✅ Fichier importé: {filename}")
                return 1
            
            return 0
        except Exception as e:
            print(f"❌ Erreur import fichier {file_path}: {e}")
            return 0
    
    def _import_folder_contents_direct(self, folder_path: str, db, root_folder_id: int, panel: str,
                                     progress_callback, total: int, current_count: list) -> int:
        """Importer le contenu d'un dossier de manière directe et plate"""
        total_files = 0
        
        try:
            # Créer une structure plate des fichiers avec préfixes
            folder_name = os.path.basename(folder_path)
            
            for root, dirs, files in os.walk(folder_path):
                # Calculer le chemin relatif pour créer un préfixe
                relative_path = os.path.relpath(root, folder_path)
                if relative_path == ".":
                    prefix = ""
                else:
                    prefix = relative_path.replace(os.sep, "_") + "_"
                
                # Traiter chaque fichier
                for filename in files:
                    if self.is_allowed_file(filename):
                        file_path = os.path.join(root, filename)
                        
                        # Créer un nom avec préfixe pour éviter les conflits
                        if prefix:
                            prefixed_filename = f"{prefix}{filename}"
                        else:
                            prefixed_filename = filename
                        
                        # Sauvegarder le fichier crypté
                        success, dest_path = self.save_file(file_path, prefixed_filename, panel)
                        
                        if success:
                            # Enregistrer dans la base de données
                            db.add_file(root_folder_id, prefixed_filename, dest_path)
                            total_files += 1
                            current_count[0] += 1
                            
                            if progress_callback:
                                progress_callback(current_count[0], total)
                            
                            print(f"✅ Fichier importé: {prefixed_filename}")
            
            return total_files
            
        except Exception as e:
            print(f"❌ Erreur import dossier {folder_path}: {e}")
            return total_files
    
    def open_file(self, filepath: str) -> bool:
        """
        Ouvrir un fichier crypté en le déchiffrant temporairement
        
        Args:
            filepath: Chemin du fichier crypté
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not os.path.exists(filepath):
                print(f"❌ Fichier crypté introuvable: {filepath}")
                return False
            
            # Récupérer le nom original depuis les métadonnées
            encrypted_filename = os.path.basename(filepath)
            if encrypted_filename not in self.metadata:
                print(f"❌ Métadonnées introuvables pour: {encrypted_filename}")
                return False
            
            original_name = self.metadata[encrypted_filename]['original_name']
            
            # Créer un fichier temporaire déchiffré
            temp_dir = os.path.join(self.upload_dir, ".temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file = os.path.join(temp_dir, original_name)
            
            # Déchiffrer et sauvegarder temporairement
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.decrypt_file(encrypted_data)
            
            with open(temp_file, 'wb') as f:
                f.write(decrypted_data)
            
            # Ouvrir le fichier temporaire
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(temp_file)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', temp_file])
            else:  # Linux
                subprocess.run(['xdg-open', temp_file])
            
            # Programmer la suppression du fichier temporaire après 30 secondes
            import threading
            import time
            
            def cleanup_temp_file():
                time.sleep(30)
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🧹 Fichier temporaire supprimé: {original_name}")
                except:
                    pass
            
            cleanup_thread = threading.Thread(target=cleanup_temp_file, daemon=True)
            cleanup_thread.start()
            
            print(f"✅ Fichier déchiffré et ouvert: {original_name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du fichier crypté: {e}")
            return False
    
    def delete_file(self, filepath: str) -> bool:
        """
        Supprimer un fichier crypté et ses métadonnées
        
        Args:
            filepath: Chemin du fichier crypté à supprimer
            
        Returns:
            True si succès, False sinon
        """
        try:
            encrypted_filename = os.path.basename(filepath)
            
            # Supprimer le fichier physique
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"✅ Fichier crypté supprimé: {encrypted_filename}")
            
            # Supprimer les métadonnées
            if encrypted_filename in self.metadata:
                del self.metadata[encrypted_filename]
                self.save_metadata()
                print(f"✅ Métadonnées supprimées: {encrypted_filename}")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False
    
    def get_file_size(self, filepath: str) -> int:
        """Récupérer la taille d'un fichier crypté depuis les métadonnées"""
        try:
            encrypted_filename = os.path.basename(filepath)
            if encrypted_filename in self.metadata:
                return self.metadata[encrypted_filename].get('size', 0)
            return os.path.getsize(filepath) if os.path.exists(filepath) else 0
        except:
            return 0
    
    def format_file_size(self, size: int) -> str:
        """Formater la taille d'un fichier"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def is_pdf(self, filename: str) -> bool:
        """Vérifier si un fichier est un PDF"""
        return filename.lower().endswith('.pdf')
    
    def is_downloadable(self, filename: str) -> bool:
        """Vérifier si un fichier est téléchargeable (pas PDF)"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in {'.docx', '.xlsx', '.doc', '.xls'}
    
    def get_original_filename(self, encrypted_filepath: str) -> str:
        """Récupérer le nom original d'un fichier crypté"""
        try:
            encrypted_filename = os.path.basename(encrypted_filepath)
            if encrypted_filename in self.metadata:
                return self.metadata[encrypted_filename]['original_name']
            return encrypted_filename
        except:
            return os.path.basename(encrypted_filepath)

