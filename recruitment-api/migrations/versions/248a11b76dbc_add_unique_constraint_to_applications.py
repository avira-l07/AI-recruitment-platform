"""add_unique_constraint_to_applications

Revision ID: 248a11b76dbc
Revises: 86eb4da6e114
Create Date: 2026-07-19 01:23:29.706466

"""
from typing import Sequence, Union
from collections import defaultdict
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '248a11b76dbc'
down_revision: Union[str, Sequence[str], None] = '86eb4da6e114'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    
    # Check if table exists
    result = bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'"))
    if not result.fetchone():
        return

    # Select all applications to deduplicate
    rows_res = bind.execute(sa.text("SELECT id, candidate_id, job_id, status FROM applications"))
    rows = rows_res.fetchall()
    
    groups = defaultdict(list)
    for r in rows:
        groups[(r[1], r[2])].append(r)
        
    status_priority = {
        "Hired": 8, "Offer": 7, "Interview": 6, "Shortlisted": 5, 
        "Manual Review": 4, "AI Review": 3, "Applied": 2, 
        "Rejected": 1, "Withdrawn": 0
    }
    
    for key, app_rows in groups.items():
        if len(app_rows) > 1:
            # Find oldest row (smallest id)
            oldest_row = min(app_rows, key=lambda x: x[0])
            # Find most advanced status
            best_status = max(app_rows, key=lambda x: status_priority.get(x[3], 2))[3]
            
            # If oldest row status is not the best status, update it
            if oldest_row[3] != best_status:
                bind.execute(
                    sa.text("UPDATE applications SET status = :status WHERE id = :id"),
                    {"status": best_status, "id": oldest_row[0]}
                )
            
            # Delete other duplicates
            for r in app_rows:
                if r[0] != oldest_row[0]:
                    bind.execute(
                        sa.text("DELETE FROM applications WHERE id = :id"),
                        {"id": r[0]}
                    )

    # Apply batch alter table to create unique constraint
    with op.batch_alter_table("applications") as batch_op:
        batch_op.create_unique_constraint("uq_candidate_job_application", ["candidate_id", "job_id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("applications") as batch_op:
        batch_op.drop_constraint("uq_candidate_job_application", type_="unique")
