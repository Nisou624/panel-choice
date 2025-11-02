# database.py (version optimisée)
import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import bcrypt
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    print("⚠️ cryptography non installé - chiffrement désactivé")
    CRYPTO_AVAILABLE = False

class Database:
    """Base de données optimisée avec recherche haute performance"""
    
    # Définition des panels disponibles
    PANELS = {
        'certification': 'Certification',
        'entete': 'En-tête',
        'interface_emp': 'Interface Employés',
        'autre': 'Autre'
    }
    
    def __init__(self, db_path: str = "portal.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        if CRYPTO_AVAILABLE:
            self.encryption_key = self._get_or_create_encryption_key()
            self.fernet = Fernet(self.encryption_key)
        else:
            self.encryption_key = None
            self.fernet = None
            
        self.connect()
        self.migrate_database()
        self.create_tables()
        self.create_search_indexes()
        self.create_default_admin()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Générer ou récupérer la clé de chiffrement"""
        if not CRYPTO_AVAILABLE:
            return b''
            
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            print("🔑 Clé de chiffrement générée")
            return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Chiffrer des données sensibles"""
        if not CRYPTO_AVAILABLE or not self.fernet:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Déchiffrer des données sensibles"""
        if not CRYPTO_AVAILABLE or not self.fernet:
            return encrypted_data
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data
    
    def connect(self):
        """Établir la connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # Optimisations SQLite pour la performance
            self.cursor.execute("PRAGMA journal_mode = WAL")
            self.cursor.execute("PRAGMA synchronous = NORMAL")
            self.cursor.execute("PRAGMA cache_size = 10000")
            self.cursor.execute("PRAGMA temp_store = MEMORY")
            
            print(f"✅ Connexion optimisée à la base de données: {self.db_path}")
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            raise
    
    def migrate_database(self):
        """Migration automatique de la base de données avec support panels"""
        try:
            # Vérifier si la table folders existe
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
            folders_exist = self.cursor.fetchone()
            
            if folders_exist:
                # Vérifier si la colonne panel existe
                self.cursor.execute("PRAGMA table_info(folders)")
                columns = [column[1] for column in self.cursor.fetchall()]
                
                if 'panel' not in columns:
                    print("🔄 Ajout de la colonne panel aux dossiers...")
                    self.cursor.execute("ALTER TABLE folders ADD COLUMN panel TEXT DEFAULT 'interface_emp'")
                    self.conn.commit()
            
            # Vérifier la table files
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            if self.cursor.fetchone():
                self.cursor.execute("PRAGMA table_info(files)")
                columns = [column[1] for column in self.cursor.fetchall()]
                
                # Ajouter file_size si elle n'existe pas
                if 'file_size' not in columns:
                    print("🔄 Ajout de la colonne file_size...")
                    self.cursor.execute("ALTER TABLE files ADD COLUMN file_size INTEGER DEFAULT 0")
                    
                    self.cursor.execute("SELECT id, filepath FROM files")
                    files = self.cursor.fetchall()
                    
                    for file_id, filepath in files:
                        try:
                            if os.path.exists(filepath):
                                size = os.path.getsize(filepath)
                                self.cursor.execute("UPDATE files SET file_size = ? WHERE id = ?", (size, file_id))
                        except Exception as e:
                            print(f"⚠️ Erreur calcul taille pour {filepath}: {e}")
                
                # Ajouter file_hash si elle n'existe pas
                if 'file_hash' not in columns:
                    print("🔄 Ajout de la colonne file_hash...")
                    self.cursor.execute("ALTER TABLE files ADD COLUMN file_hash TEXT DEFAULT ''")
                
                # Ajouter search_text pour la recherche full-text
                if 'search_text' not in columns:
                    print("🔄 Ajout de la colonne search_text pour recherche optimisée...")
                    self.cursor.execute("ALTER TABLE files ADD COLUMN search_text TEXT DEFAULT ''")
                    
                    # Populer search_text avec les noms de fichiers existants
                    self.cursor.execute("UPDATE files SET search_text = LOWER(filename)")
            
            # Vérifier la table admins pour bcrypt
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admins'")
            if self.cursor.fetchone():
                self.cursor.execute("PRAGMA table_info(admins)")
                admin_columns = [column[1] for column in self.cursor.fetchall()]
                
                if 'password' in admin_columns and 'password_hash' not in admin_columns:
                    print("🔄 Migration des mots de passe vers bcrypt...")
                    self.cursor.execute("ALTER TABLE admins ADD COLUMN password_hash TEXT")
                    
                    self.cursor.execute("SELECT id, password FROM admins WHERE password_hash IS NULL OR password_hash = ''")
                    admins = self.cursor.fetchall()
                    
                    for admin_id, old_password in admins:
                        if old_password:
                            password_hash = bcrypt.hashpw(old_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            self.cursor.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (password_hash, admin_id))
            
            self.conn.commit()
            print("✅ Migration automatique terminée")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la migration: {e}")
            self.conn.rollback()
    
    def create_tables(self):
        """Créer les tables nécessaires avec support des panels"""
        try:
            # Table admins avec hash bcrypt
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table folders avec panel
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER DEFAULT NULL,
                    panel TEXT DEFAULT 'interface_emp',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE
                )
            """)
            
            # Table files avec métadonnées et recherche optimisée
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT DEFAULT '',
                    search_text TEXT DEFAULT '',
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
                )
            """)
            
            self.conn.commit()
            print("✅ Tables créées avec succès")
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            raise
    
    def create_search_indexes(self):
        """Créer des index optimisés pour la recherche haute performance"""
        try:
            # Index principaux pour la recherche
            search_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_files_search_text ON files(search_text)",
                "CREATE INDEX IF NOT EXISTS idx_files_filename_lower ON files(LOWER(filename))",
                "CREATE INDEX IF NOT EXISTS idx_files_uploaded_at ON files(uploaded_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_files_size ON files(file_size)",
                "CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id)",
                "CREATE INDEX IF NOT EXISTS idx_folders_panel ON folders(panel)",
                "CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id)",
                "CREATE INDEX IF NOT EXISTS idx_folders_name_lower ON folders(LOWER(name))",
                
                # Index composite pour recherches complexes
                "CREATE INDEX IF NOT EXISTS idx_files_folder_filename ON files(folder_id, filename)",
                "CREATE INDEX IF NOT EXISTS idx_files_size_date ON files(file_size, uploaded_at)",
                "CREATE INDEX IF NOT EXISTS idx_folders_panel_parent ON folders(panel, parent_id)"
            ]
            
            for index_sql in search_indexes:
                self.cursor.execute(index_sql)
            
            # Créer une vue pour la recherche rapide
            self.cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_files_search AS
                SELECT 
                    f.id,
                    f.filename,
                    f.filepath,
                    f.file_size,
                    f.search_text,
                    f.uploaded_at,
                    f.folder_id,
                    fold.name as folder_name,
                    fold.panel,
                    fold.parent_id as folder_parent_id
                FROM files f
                INNER JOIN folders fold ON f.folder_id = fold.id
            """)
            
            self.conn.commit()
            print("✅ Index de recherche créés avec succès")
        except sqlite3.Error as e:
            print(f"⚠️ Erreur lors de la création des index: {e}")
    
    def create_default_admin(self):
        """Créer un compte admin par défaut avec bcrypt"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM admins WHERE email = ?", ('admin',))
            if self.cursor.fetchone()[0] == 0:
                password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                self.cursor.execute(
                    "INSERT INTO admins (email, password, password_hash) VALUES (?, ?, ?)",
                    ('admin', 'admin', password_hash)
                )
                self.conn.commit()
                print("✅ Admin par défaut créé avec hash bcrypt (admin/admin)")
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la création de l'admin: {e}")
    
    def authenticate_admin(self, email: str, password: str) -> bool:
        """Authentifier un administrateur avec bcrypt"""
        try:
            self.cursor.execute(
                "SELECT password, password_hash FROM admins WHERE email = ?",
                (email,)
            )
            result = self.cursor.fetchone()
            if result:
                if result['password_hash']:
                    return bcrypt.checkpw(password.encode('utf-8'), result['password_hash'].encode('utf-8'))
                elif result['password']:
                    return result['password'] == password
            return False
        except sqlite3.Error as e:
            print(f"❌ Erreur d'authentification: {e}")
            return False
    
    # ==================== GESTION DES DOSSIERS AVEC PANELS ====================
    
    def create_folder(self, name: str, parent_id: Optional[int] = None, panel: str = 'interface_emp') -> int:
        """Créer un nouveau dossier dans un panel spécifique"""
        try:
            # Si parent_id existe, hériter du panel du parent
            if parent_id is not None:
                parent = self.get_folder(parent_id)
                if parent:
                    panel = parent['panel']
            
            self.cursor.execute(
                "INSERT INTO folders (name, parent_id, panel) VALUES (?, ?, ?)",
                (name, parent_id, panel)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la création du dossier: {e}")
            raise
    
    def get_folder(self, folder_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un dossier par son ID"""
        try:
            self.cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération du dossier: {e}")
            return None
    
    def get_all_folders(self, panel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Récupérer tous les dossiers d'un panel spécifique"""
        try:
            if panel:
                self.cursor.execute("SELECT * FROM folders WHERE panel = ? ORDER BY name ASC", (panel,))
            else:
                self.cursor.execute("SELECT * FROM folders ORDER BY name ASC")
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération des dossiers: {e}")
            return []
    
    def get_subfolders(self, parent_id: Optional[int] = None, panel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Récupérer les sous-dossiers d'un dossier parent dans un panel"""
        try:
            if parent_id is None:
                if panel:
                    self.cursor.execute(
                        "SELECT * FROM folders WHERE parent_id IS NULL AND panel = ? ORDER BY name ASC",
                        (panel,)
                    )
                else:
                    self.cursor.execute(
                        "SELECT * FROM folders WHERE parent_id IS NULL ORDER BY name ASC"
                    )
            else:
                self.cursor.execute(
                    "SELECT * FROM folders WHERE parent_id = ? ORDER BY name ASC",
                    (parent_id,)
                )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération des sous-dossiers: {e}")
            return []
    
    def update_folder(self, folder_id: int, name: str) -> bool:
        """Renommer un dossier"""
        try:
            self.cursor.execute(
                "UPDATE folders SET name = ? WHERE id = ?",
                (name, folder_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la mise à jour du dossier: {e}")
            return False
    
    def delete_folder(self, folder_id: int) -> bool:
        """Supprimer un dossier et ses fichiers"""
        try:
            self.cursor.execute("SELECT filepath FROM files WHERE folder_id = ?", (folder_id,))
            files = self.cursor.fetchall()
            
            for file in files:
                try:
                    if os.path.exists(file['filepath']):
                        os.remove(file['filepath'])
                except Exception as e:
                    print(f"⚠️ Impossible de supprimer le fichier {file['filepath']}: {e}")
            
            self.cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la suppression du dossier: {e}")
            return False
    
    def get_folder_path(self, folder_id: int) -> List[Dict[str, Any]]:
        """Récupérer le chemin complet d'un dossier (breadcrumb)"""
        path = []
        current_id = folder_id
        
        while current_id is not None:
            folder = self.get_folder(current_id)
            if folder:
                path.insert(0, folder)
                current_id = folder['parent_id']
            else:
                break
        
        return path
    
    # ==================== GESTION DES FICHIERS ====================
    
    def add_file(self, folder_id: int, filename: str, filepath: str) -> int:
        """Ajouter un fichier à la base de données avec métadonnées et recherche optimisée"""
        try:
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            file_hash = self._calculate_file_hash(filepath)
            
            # Créer le texte de recherche optimisé
            search_text = self._create_search_text(filename)
            
            self.cursor.execute(
                "INSERT INTO files (folder_id, filename, filepath, file_size, file_hash, search_text) VALUES (?, ?, ?, ?, ?, ?)",
                (folder_id, filename, filepath, file_size, file_hash, search_text)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de l'ajout du fichier: {e}")
            raise
    
    def _create_search_text(self, filename: str) -> str:
        """Créer un texte de recherche optimisé pour un fichier"""
        # Normaliser le texte pour la recherche
        import re
        
        # Enlever l'extension et convertir en minuscules
        name_without_ext = os.path.splitext(filename)[0].lower()
        
        # Remplacer les caractères spéciaux par des espaces
        normalized = re.sub(r'[_\-\.\(\)\[\]{}]', ' ', name_without_ext)
        
        # Diviser en mots et rejoindre
        words = normalized.split()
        return ' '.join(words)
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculer le hash SHA256 d'un fichier"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"⚠️ Erreur calcul hash: {e}")
            return ""
    
    def get_files_in_folder(self, folder_id: int) -> List[Dict[str, Any]]:
        """Récupérer tous les fichiers d'un dossier"""
        try:
            self.cursor.execute(
                "SELECT * FROM files WHERE folder_id = ? ORDER BY uploaded_at DESC",
                (folder_id,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération des fichiers: {e}")
            return []
    
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un fichier par son ID"""
        try:
            self.cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération du fichier: {e}")
            return None
    
    def delete_file(self, file_id: int) -> bool:
        """Supprimer un fichier"""
        try:
            file = self.get_file(file_id)
            if file:
                try:
                    if os.path.exists(file['filepath']):
                        os.remove(file['filepath'])
                except Exception as e:
                    print(f"⚠️ Impossible de supprimer le fichier physique: {e}")
                
                self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                self.conn.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la suppression du fichier: {e}")
            return False
    
    # ==================== RECHERCHE ULTRA-RAPIDE ====================
    
    def search_files_fast(self, 
                         filename: str = "", 
                         extension: str = "",
                         panel: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recherche ultra-rapide de fichiers avec cache et index optimisés
        
        Args:
            filename: Nom du fichier à rechercher
            extension: Extension à filtrer
            panel: Panel à filtrer
            limit: Limite de résultats
            
        Returns:
            Liste des fichiers trouvés
        """
        try:
            conditions = []
            params = []
            
            # Utiliser la vue optimisée pour la recherche
            base_query = """
                SELECT 
                    id, filename, filepath, file_size, uploaded_at,
                    folder_id, folder_name, panel
                FROM v_files_search
            """
            
            # Recherche par nom - utiliser l'index de recherche
            if filename:
                search_terms = filename.lower().split()
                if len(search_terms) == 1:
                    # Recherche simple - utiliser l'index
                    conditions.append("search_text LIKE ?")
                    params.append(f"%{search_terms[0]}%")
                else:
                    # Recherche multiple - combiner les termes
                    term_conditions = []
                    for term in search_terms:
                        term_conditions.append("search_text LIKE ?")
                        params.append(f"%{term}%")
                    conditions.append("(" + " AND ".join(term_conditions) + ")")
            
            # Filtre par extension
            if extension:
                conditions.append("filename LIKE ?")
                params.append(f"%.{extension.lower()}")
            
            # Filtre par panel
            if panel:
                conditions.append("panel = ?")
                params.append(panel)
            
            # Construire la requête finale
            if conditions:
                query = base_query + " WHERE " + " AND ".join(conditions)
            else:
                query = base_query
            
            query += f" ORDER BY uploaded_at DESC LIMIT {limit}"
            
            # Exécuter la requête optimisée
            start_time = datetime.now()
            self.cursor.execute(query, params)
            results = [dict(row) for row in self.cursor.fetchall()]
            end_time = datetime.now()
            
            search_time = (end_time - start_time).total_seconds()
            print(f"🔍 Recherche rapide terminée en {search_time:.3f}s - {len(results)} résultats")
            
            return results
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la recherche rapide: {e}")
            return []
    
    def search_files(self, 
                    filename: str = "", 
                    extension: str = "",
                    date_from: Optional[datetime] = None,
                    date_to: Optional[datetime] = None,
                    folder_id: Optional[int] = None,
                    min_size: Optional[int] = None,
                    max_size: Optional[int] = None,
                    panel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche avancée de fichiers (rétrocompatibilité)"""
        
        # Pour les recherches simples, utiliser la version rapide
        if not any([date_from, date_to, folder_id, min_size, max_size]):
            return self.search_files_fast(filename, extension, panel)
        
        # Sinon, utiliser la recherche complète
        try:
            conditions = []
            params = []
            
            if filename:
                conditions.append("LOWER(filename) LIKE ?")
                params.append(f"%{filename.lower()}%")
            
            if extension:
                conditions.append("LOWER(filename) LIKE ?")
                params.append(f"%.{extension.lower()}")
            
            if date_from:
                conditions.append("uploaded_at >= ?")
                params.append(date_from.isoformat())
            
            if date_to:
                conditions.append("uploaded_at <= ?")
                params.append(date_to.isoformat())
            
            if folder_id is not None:
                folder_ids = self._get_all_subfolder_ids(folder_id)
                folder_ids.append(folder_id)
                placeholders = ','.join(['?'] * len(folder_ids))
                conditions.append(f"folder_id IN ({placeholders})")
                params.extend(folder_ids)
            
            # Filtre par panel
            if panel:
                conditions.append("folder_id IN (SELECT id FROM folders WHERE panel = ?)")
                params.append(panel)
            
            try:
                self.cursor.execute("PRAGMA table_info(files)")
                columns = [column[1] for column in self.cursor.fetchall()]
                
                if 'file_size' in columns:
                    if min_size is not None:
                        conditions.append("file_size >= ?")
                        params.append(min_size)
                    
                    if max_size is not None:
                        conditions.append("file_size <= ?")
                        params.append(max_size)
            except:
                pass
            
            query = "SELECT * FROM files"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY uploaded_at DESC"
            
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def _get_all_subfolder_ids(self, folder_id: int) -> List[int]:
        """Récupérer récursivement tous les IDs des sous-dossiers"""
        subfolder_ids = []
        subfolders = self.get_subfolders(folder_id)
        
        for subfolder in subfolders:
            subfolder_ids.append(subfolder['id'])
            subfolder_ids.extend(self._get_all_subfolder_ids(subfolder['id']))
        
        return subfolder_ids
    
    def count_files_in_folder(self, folder_id: int, recursive: bool = False) -> int:
        """Compter les fichiers dans un dossier"""
        try:
            if not recursive:
                self.cursor.execute(
                    "SELECT COUNT(*) as count FROM files WHERE folder_id = ?",
                    (folder_id,)
                )
                return self.cursor.fetchone()[0]
            else:
                count = self.count_files_in_folder(folder_id, recursive=False)
                subfolders = self.get_subfolders(folder_id)
                for subfolder in subfolders:
                    count += self.count_files_in_folder(subfolder['id'], recursive=True)
                return count
        except sqlite3.Error as e:
            print(f"❌ Erreur lors du comptage des fichiers: {e}")
            return 0
    
    def get_files_by_panel(self, panel: str) -> List[Dict[str, Any]]:
        """Récupérer tous les fichiers d'un panel spécifique"""
        try:
            self.cursor.execute("""
                SELECT f.* FROM files f
                INNER JOIN folders fold ON f.folder_id = fold.id
                WHERE fold.panel = ?
                ORDER BY f.uploaded_at DESC
            """, (panel,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération des fichiers du panel: {e}")
            return []
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion à la base de données fermée")

