"""
SCFV v6 — Repositorio Base de Datos con Cifrado SQLCipher
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-26
Propósito: Gestionar la conexión a SQLite con soporte para SQLCipher (AES-256).
"""

import sqlite3
import os
from typing import Optional


class Database:
    """
    Gestor de conexión a SQLite con soporte para SQLCipher.
    """

    def __init__(self, db_path: str, passphrase: Optional[str] = None):
        self.db_path = db_path
        self.passphrase = passphrase
        self.connection = None

    def connect(self) -> sqlite3.Connection:
        if self.connection:
            return self.connection

        # Para base en memoria, no crear directorio
        if self.db_path != ':memory:':
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

        # Intentar SQLCipher primero
        try:
            import ctypes
            sqlite3.enable_load_extension(True)
            self.connection = sqlite3.connect(self.db_path)
            # Cargar extensión SQLCipher (Termux: libsqlcipher.so)
            self.connection.execute("SELECT load_extension('libsqlcipher.so')")
            sqlite3.enable_load_extension(False)
        except Exception as e:
            # Fallback a SQLite plano si no hay SQLCipher
            print(f"⚠️ SQLCipher no disponible: {e}. Usando SQLite plano (sin cifrado).")
            self.connection = sqlite3.connect(self.db_path)

        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA foreign_keys = ON")

        if self.passphrase:
            try:
                self.connection.execute(f"PRAGMA key = '{self.passphrase}'")
            except Exception:
                print("⚠️ No se pudo establecer la clave de cifrado. La base no está cifrada.")

        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_schema(self, schema_path: str):
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        conn = self.connect()
        conn.executescript(sql)
        conn.commit()
