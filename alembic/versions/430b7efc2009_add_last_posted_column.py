"""add last posted column

Revision ID: 430b7efc2009
Revises: 
Create Date: 2017-09-21 14:27:32.481240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '430b7efc2009'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'issue',
        sa.Column('last_posted', sa.DateTime)
    )


def downgrade():
    pass
