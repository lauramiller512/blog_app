"""initial_schema

Revision ID: 44bb974184bd
Revises: 
Create Date: 2020-10-28 14:35:34.225191

"""

# revision identifiers, used by Alembic.
revision = '44bb974184bd'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'authors',
        sa.Column('id', UUID, primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('firstname', sa.String(length=45), nullable=False),
        sa.Column('lastname', sa.String(length=45), nullable=False),
        sa.Column('username', sa.String(length=45), nullable=False,
                  unique=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'articles',
        sa.Column('id', UUID, primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('title', sa.String(length=45), nullable=False),
        sa.Column('text', sa.String(length=516), nullable=False),
        sa.Column('author_id', UUID, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['author_id'], ['authors.id'],
            name='article_author_id_fk'
        )
    )

def downgrade():
    pass
