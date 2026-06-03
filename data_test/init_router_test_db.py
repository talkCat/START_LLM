from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path("/app/data/routes.db")
MODEL_NAME = "qwen3-embedding"
MODEL_ALIASES = ["qwen3-embedding", "text-embedding-ada-003"]
MODEL_URL = "http://qwen3-embedding-test:30000"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS backendsource (
                id INTEGER NOT NULL,
                model_url VARCHAR NOT NULL,
                api_key VARCHAR,
                sync_interval_minutes INTEGER NOT NULL,
                last_synced_at DATETIME,
                last_sync_error VARCHAR,
                created DATETIME NOT NULL,
                updated DATETIME NOT NULL,
                PRIMARY KEY (id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ix_backendsource_model_url
            ON backendsource (model_url);

            CREATE TABLE IF NOT EXISTS modelalias (
                id INTEGER NOT NULL,
                alias_name VARCHAR NOT NULL,
                model_name VARCHAR NOT NULL,
                created DATETIME NOT NULL,
                PRIMARY KEY (id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ix_modelalias_alias_name
            ON modelalias (alias_name);

            CREATE INDEX IF NOT EXISTS ix_modelalias_model_name
            ON modelalias (model_name);

            CREATE TABLE IF NOT EXISTS routersetting (
                id INTEGER NOT NULL,
                routing_policy VARCHAR NOT NULL,
                updated DATETIME NOT NULL,
                PRIMARY KEY (id)
            );

            CREATE TABLE IF NOT EXISTS modelroute (
                id INTEGER NOT NULL,
                model_name VARCHAR NOT NULL,
                model_url VARCHAR NOT NULL,
                api_key VARCHAR,
                request_param_mapping VARCHAR,
                auto_managed BOOLEAN NOT NULL,
                source_id INTEGER,
                created DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(source_id) REFERENCES backendsource (id)
            );

            CREATE INDEX IF NOT EXISTS ix_modelroute_model_name
            ON modelroute (model_name);

            CREATE INDEX IF NOT EXISTS ix_modelroute_source_id
            ON modelroute (source_id);

            CREATE TABLE IF NOT EXISTS sourcemodelexclusion (
                id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                model_name VARCHAR NOT NULL,
                created DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(source_id) REFERENCES backendsource (id)
            );

            CREATE INDEX IF NOT EXISTS ix_sourcemodelexclusion_model_name
            ON sourcemodelexclusion (model_name);

            CREATE INDEX IF NOT EXISTS ix_sourcemodelexclusion_source_id
            ON sourcemodelexclusion (source_id);
            """
        )

        now = datetime.now(timezone.utc).isoformat(sep=" ")

        cur.execute("DELETE FROM modelroute")
        cur.execute("DELETE FROM modelalias")
        cur.execute("DELETE FROM routersetting")
        cur.execute("DELETE FROM sourcemodelexclusion")
        cur.execute("DELETE FROM backendsource")

        cur.execute(
            """
            INSERT INTO modelroute (
                id, model_name, model_url, api_key, request_param_mapping,
                auto_managed, source_id, created
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, MODEL_NAME, MODEL_URL, None, None, 0, None, now),
        )

        for index, alias in enumerate(MODEL_ALIASES, start=1):
            cur.execute(
                """
                INSERT INTO modelalias (id, alias_name, model_name, created)
                VALUES (?, ?, ?, ?)
                """,
                (index, alias, MODEL_NAME, now),
            )

        cur.execute(
            """
            INSERT INTO routersetting (id, routing_policy, updated)
            VALUES (?, ?, ?)
            """,
            (1, "round_robin", now),
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
