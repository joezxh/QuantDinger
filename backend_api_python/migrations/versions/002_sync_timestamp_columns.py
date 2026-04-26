"""Sync timestamp columns: add missing updated_at / created_at to existing tables.

Revision ID: 002_sync_timestamp_columns
Revises: 001_initial_schema
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa


revision = "002_sync_timestamp_columns"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Tables that use TimestampMixin but were missing updated_at in older init.sql
    tables_missing_updated_at = [
        "qd_collection_records",
        "qd_graph_entity_refs",
        "qd_graph_relation_snapshots",
        "qd_graph_feature_daily",
        "qd_company_narrative_features",
        "qd_crypto_narrative_features",
        "qd_polymarket_market_features",
        "qd_polymarket_users",
        "qd_polymarket_markets",
        "qd_polymarket_opportunities",
    ]

    for table_name in tables_missing_updated_at:
        col = op.execute(
            sa.text(
                f"""SELECT column_name FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND column_name = 'updated_at'"""
            )
        ).fetchone()
        if not col:
            op.execute(
                sa.text(
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE "
                    f"DEFAULT NOW()"
                )
            )
            print(f"Added updated_at to {table_name}")

    # GraphJob had neither created_at nor updated_at
    for col_name, default_val in [
        ("created_at", "NOW()"),
        ("updated_at", "NOW()"),
    ]:
        col = op.execute(
            sa.text(
                f"""SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'qd_graph_jobs'
                    AND column_name = '{col_name}'"""
            )
        ).fetchone()
        if not col:
            op.execute(
                sa.text(
                    f"ALTER TABLE qd_graph_jobs "
                    f"ADD COLUMN {col_name} TIMESTAMP WITH TIME ZONE "
                    f"DEFAULT {default_val}"
                )
            )
            print(f"Added {col_name} to qd_graph_jobs")

    # DifyWorkflowLog missing updated_at
    col = op.execute(
        sa.text(
            """SELECT column_name FROM information_schema.columns
               WHERE table_name = 'qd_dify_workflow_logs'
               AND column_name = 'updated_at'"""
        )
    ).fetchone()
    if not col:
        op.execute(
            sa.text(
                "ALTER TABLE qd_dify_workflow_logs "
                "ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
            )
        )
        print("Added updated_at to qd_dify_workflow_logs")

    # Fix qd_polymarket_ai_analysis: add missing columns that were in old init.sql
    # but not in polymarket.py model (no action needed since these are extra columns)
    # However, rename qd_polymarket_asset_opportunities → qd_polymarket_opportunities
    # if the old table still exists with the old name
    old_table = op.execute(
        sa.text(
            """SELECT table_name FROM information_schema.tables
               WHERE table_name = 'qd_polymarket_asset_opportunities'"""
        )
    ).fetchone()
    if old_table:
        # Check if new table already exists
        new_table = op.execute(
            sa.text(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_name = 'qd_polymarket_opportunities'"""
            )
        ).fetchone()
        if not new_table:
            op.execute(
                sa.text(
                    "ALTER TABLE qd_polymarket_asset_opportunities "
                    "RENAME TO qd_polymarket_opportunities"
                )
            )
            print("Renamed qd_polymarket_asset_opportunities to qd_polymarket_opportunities")

    # Drop extra columns from qd_polymarket_markets that exist in old init.sql but not in model
    extra_cols = ["volume_24h", "liquidity", "outcome_tokens", "slug"]
    for col_name in extra_cols:
        col = op.execute(
            sa.text(
                f"""SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'qd_polymarket_markets'
                    AND column_name = '{col_name}'"""
            )
        ).fetchone()
        if col:
            try:
                op.execute(
                    sa.text(
                        f"ALTER TABLE qd_polymarket_markets DROP COLUMN {col_name}"
                    )
                )
                print(f"Dropped extra column {col_name} from qd_polymarket_markets")
            except Exception:
                pass  # Column may have constraints; skip if can't drop


def downgrade():
    # No downgrade — this is a corrective migration
    pass
