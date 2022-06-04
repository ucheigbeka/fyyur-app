"""Added child table Genre

Revision ID: 134b3aa16c35
Revises: b0920291747a
Create Date: 2022-06-04 12:46:32.239897

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '134b3aa16c35'
down_revision = 'b0920291747a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Genre',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    genres = [
        'Alternative', 'Blues', 'Classical', 'Country', 'Electronic', 'Folk', 'Funk', 'Hip-Hop', 'Heavy Metal',
        'Instrumental', 'Jazz', 'Musical Theatre', 'Pop', 'Punk', 'R&B', 'Reggae', 'Rock n Roll', 'Soul', 'Other'
    ]
    for genre in genres:
        op.execute(f"INSERT INTO \"Genre\" (name) VALUES ('{genre}');")

    op.create_table('artist_genres',
    sa.Column('artist_id', sa.Integer(), nullable=False),
    sa.Column('genre_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], ),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], ),
    sa.PrimaryKeyConstraint('artist_id', 'genre_id')
    )
    op.create_table('venue_genres',
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.Column('genre_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], ),
    sa.ForeignKeyConstraint(['venue_id'], ['Venue.id'], ),
    sa.PrimaryKeyConstraint('venue_id', 'genre_id')
    )
    op.drop_column('Artist', 'genres')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('genres', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.drop_constraint('venue_genres_venue_id_fkey', 'venue_genres', type_='foreignkey')
    op.drop_constraint('venue_genres_genre_id_fkey', 'venue_genres', type_='foreignkey')
    op.drop_table('venue_genres')
    op.drop_constraint('artist_genres_artist_id_fkey', 'artist_genres', type_='foreignkey')
    op.drop_constraint('artist_genres_genre_id_fkey', 'artist_genres', type_='foreignkey')
    op.drop_table('artist_genres')
    op.drop_table('Genre')
    # ### end Alembic commands ###
