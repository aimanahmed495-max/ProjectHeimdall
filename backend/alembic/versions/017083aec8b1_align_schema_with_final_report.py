"""align schema with final report

Revision ID: 017083aec8b1
Revises: 226eb47c96bb
Create Date: 2026-09-08 01:47:41.469873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '017083aec8b1'
down_revision: Union[str, Sequence[str], None] = '226eb47c96bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace the experimental schema with the five-table report schema."""
    op.drop_index(
        op.f("ix_alert_actions_status"),
        table_name="alert_actions",
    )
    op.drop_index(
        op.f("ix_alert_actions_threat_event_id"),
        table_name="alert_actions",
    )
    op.drop_table("alert_actions")

    op.drop_index(
        op.f("ix_threat_events_threat_level"),
        table_name="threat_events",
    )
    op.drop_index(
        op.f("ix_threat_events_source_id"),
        table_name="threat_events",
    )
    op.drop_table("threat_events")
    op.drop_table("osint_sources")

    op.create_table(
        "osint_sources",
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 1",
            name="ck_osint_sources_reliability_range",
        ),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_name"),
    )

    op.create_table(
        "threat_events",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("object_class", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'Pending'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_threat_events_confidence_range",
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        op.f("ix_threat_events_camera_id"),
        "threat_events",
        ["camera_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_threat_events_status"),
        "threat_events",
        ["status"],
        unique=False,
    )

    op.create_table(
        "alert_logs",
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column(
            "alert_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("alert_level", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "acknowledged",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["threat_events.event_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("alert_id"),
    )
    op.create_index(
        op.f("ix_alert_logs_alert_level"),
        "alert_logs",
        ["alert_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_alert_logs_event_id"),
        "alert_logs",
        ["event_id"],
        unique=False,
    )

    op.create_table(
        "camera_states",
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("fps", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=30), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("state_id"),
    )
    op.create_index(
        op.f("ix_camera_states_camera_id"),
        "camera_states",
        ["camera_id"],
        unique=False,
    )

    op.create_table(
        "system_logs",
        sa.Column("log_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column(
            "log_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["threat_events.event_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index(
        op.f("ix_system_logs_event_id"),
        "system_logs",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_system_logs_module"),
        "system_logs",
        ["module"],
        unique=False,
    )


def downgrade() -> None:
    """Restore the previous three-table prototype schema."""
    op.drop_index(
        op.f("ix_system_logs_module"),
        table_name="system_logs",
    )
    op.drop_index(
        op.f("ix_system_logs_event_id"),
        table_name="system_logs",
    )
    op.drop_table("system_logs")

    op.drop_index(
        op.f("ix_camera_states_camera_id"),
        table_name="camera_states",
    )
    op.drop_table("camera_states")

    op.drop_index(
        op.f("ix_alert_logs_event_id"),
        table_name="alert_logs",
    )
    op.drop_index(
        op.f("ix_alert_logs_alert_level"),
        table_name="alert_logs",
    )
    op.drop_table("alert_logs")

    op.drop_index(
        op.f("ix_threat_events_status"),
        table_name="threat_events",
    )
    op.drop_index(
        op.f("ix_threat_events_camera_id"),
        table_name="threat_events",
    )
    op.drop_table("threat_events")
    op.drop_table("osint_sources")

    op.create_table(
        "osint_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "threat_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("threat_score", sa.Integer(), nullable=False),
        sa.Column("threat_level", sa.String(length=30), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "threat_score >= 0 AND threat_score <= 100",
            name="ck_threat_events_score_range",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["osint_sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_threat_events_source_id"),
        "threat_events",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_threat_events_threat_level"),
        "threat_events",
        ["threat_level"],
        unique=False,
    )

    op.create_table(
        "alert_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("threat_event_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["threat_event_id"],
            ["threat_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_alert_actions_threat_event_id"),
        "alert_actions",
        ["threat_event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_alert_actions_status"),
        "alert_actions",
        ["status"],
        unique=False,
    )