"""normalize threat event origins and preserve alerts

Revision ID: fc324d2ad8ad
Revises: 4d70a0dd39ea
Create Date: 2026-10-02 00:29:09.529354

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fc324d2ad8ad"
down_revision: Union[str, Sequence[str], None] = "4d70a0dd39ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow source-only threats and preserve referenced records."""

    op.drop_constraint(
        "alert_logs_event_id_fkey",
        "alert_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_alert_logs_event_id_threat_events",
        "alert_logs",
        "threat_events",
        ["event_id"],
        ["event_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        "fk_threat_events_source_id_osint_sources",
        "threat_events",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_threat_events_source_id_osint_sources",
        "threat_events",
        "osint_sources",
        ["source_id"],
        ["source_id"],
        ondelete="RESTRICT",
    )

    op.alter_column(
        "threat_events",
        "camera_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_check_constraint(
        "ck_threat_events_has_origin",
        "threat_events",
        "source_id IS NOT NULL OR camera_id IS NOT NULL",
    )


def downgrade() -> None:
    """Restore the previous threat-event relationship behavior."""

    op.drop_constraint(
        "ck_threat_events_has_origin",
        "threat_events",
        type_="check",
    )
    op.alter_column(
        "threat_events",
        "camera_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint(
        "fk_threat_events_source_id_osint_sources",
        "threat_events",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_threat_events_source_id_osint_sources",
        "threat_events",
        "osint_sources",
        ["source_id"],
        ["source_id"],
        ondelete="SET NULL",
    )

    op.drop_constraint(
        "fk_alert_logs_event_id_threat_events",
        "alert_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "alert_logs_event_id_fkey",
        "alert_logs",
        "threat_events",
        ["event_id"],
        ["event_id"],
        ondelete="CASCADE",
    )
