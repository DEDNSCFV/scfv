"""
SCFV v6.3 - Event Store (append-only con hash chain)
"""
import sqlite3
import json
import hashlib
import time
import uuid
from typing import List, Dict, Any, Tuple

class EventStore:
    GENESIS_HASH = "0" * 64

    def __init__(self, db_path: str = "scfv.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._hash_actual = self._cargar_ultimo_hash()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                tipo_evento TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                payload TEXT NOT NULL,
                version_contexto TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                idempotency_key TEXT UNIQUE NOT NULL,
                hash_previo TEXT NOT NULL,
                hash_actual TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation ON event_store(correlation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_idempotency ON event_store(idempotency_key)")
        self.conn.commit()

    def _cargar_ultimo_hash(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT hash_actual FROM event_store ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else self.GENESIS_HASH

    def _calcular_hash(self, payload_str: str, version_str: str, hash_previo: str,
                       correlation_id: str, idempotency_key: str) -> str:
        canonical = payload_str + version_str + correlation_id + idempotency_key
        return hashlib.sha256((canonical + hash_previo).encode('utf-8')).hexdigest()

    def existe_idempotency_key(self, key: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM event_store WHERE idempotency_key = ? LIMIT 1", (key,))
        return cursor.fetchone() is not None

    def guardar(self, tipo: str, payload: Any, correlation_id: str, idempotency_key: str, version_ctx: Any = None):
        if self.existe_idempotency_key(idempotency_key):
            raise ValueError(f"I7_VIOLACION_IDEMPOTENCIA: {idempotency_key}")

        event_id = uuid.uuid4().hex
        ts = int(time.time())

        payload_str = json.dumps(payload, default=str, sort_keys=True)
        version_str = json.dumps(version_ctx) if version_ctx else "{}"

        hash_previo = self._hash_actual
        hash_actual = self._calcular_hash(payload_str, version_str, hash_previo,
                                          correlation_id, idempotency_key)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO event_store
            (event_id, tipo_evento, timestamp, payload, version_contexto,
             correlation_id, idempotency_key, hash_previo, hash_actual)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, tipo, ts, payload_str, version_str,
              correlation_id, idempotency_key, hash_previo, hash_actual))
        self.conn.commit()
        self._hash_actual = hash_actual

        return {
            'id': cursor.lastrowid,
            'event_id': event_id,
            'tipo_evento': tipo,
            'timestamp': ts,
            'payload': payload_str,
            'version_contexto': version_str,
            'correlation_id': correlation_id,
            'idempotency_key': idempotency_key,
            'hash_previo': hash_previo,
            'hash_actual': hash_actual
        }

    def verificar_cadena(self) -> Tuple[bool, str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM event_store ORDER BY id")
        rows = cursor.fetchall()

        hash_esperado = self.GENESIS_HASH
        for row in rows:
            if row['hash_previo'] != hash_esperado:
                return False, f"I8_FALLA: hash_previo no coincide en evento {row['event_id']}"

            recomputado = self._calcular_hash(
                row['payload'],
                row['version_contexto'],
                row['hash_previo'],
                row['correlation_id'],
                row['idempotency_key']
            )
            if recomputado != row['hash_actual']:
                return False, f"HASH_INVALIDO en evento {row['event_id']}"

            hash_esperado = row['hash_actual']

        return True, "CADENA_INTEGRA"

    def obtener_hash_final(self) -> str:
        return self._hash_actual

    def materializar_diario(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS negocio_diario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asiento_id TEXT UNIQUE NOT NULL,
                correlation_id TEXT NOT NULL,
                total_debe INTEGER NOT NULL,
                total_haber INTEGER NOT NULL,
                hash_chain TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
        """)
        self.conn.commit()

        eventos = self.conn.execute("SELECT * FROM event_store WHERE tipo_evento = 'ASIENTO_REGISTRADO'").fetchall()
        for e in eventos:
            payload = json.loads(e['payload'])
            self.conn.execute(
                "INSERT OR REPLACE INTO negocio_diario (asiento_id, correlation_id, total_debe, total_haber, hash_chain, timestamp) VALUES (?,?,?,?,?,?)",
                (payload['id'], e['correlation_id'], payload['total_debe'], payload['total_haber'], e['hash_actual'], e['timestamp'])
            )
        self.conn.commit()

    def cerrar(self):
        self.conn.close()

    def obtener_eventos_por_tipo(self, tipo_evento: str) -> List[Dict]:
        """Retorna todos los eventos de un tipo específico."""
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, tipo_evento, payload, correlation_id,
                   idempotency_key, hash_previo, hash_actual, timestamp
            FROM event_store
            WHERE tipo_evento = ?
            ORDER BY timestamp
        """, (tipo_evento,))
        rows = cursor.fetchall()
        eventos = []
        for row in rows:
            eventos.append({
                "id": row[0],
                "tipo_evento": row[1],
                "payload": json.loads(row[2]) if row[2] else {},
                "correlation_id": row[3],
                "idempotency_key": row[4],
                "hash_previo": row[5],
                "hash_actual": row[6],
                "timestamp": row[7]
            })
        return eventos
