"""empty message

Revision ID: 363e83e5b0ca
Revises: 
Create Date: 2025-01-27 22:10:39.122559

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "363e83e5b0ca"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("verify_email", sa.Boolean(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "beneficiaries",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("account_number", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "transaction_type",
            sa.Enum("CREDIT", "DEBIT", name="transactiontype"),
            nullable=True,
        ),
        sa.Column(
            "transaction_status",
            sa.Enum(
                "PENDING", "SUCCESS", "FAILED", "REFUNDED", name="transactionstatus"
            ),
            nullable=True,
        ),
        sa.Column("category_id", sa.String(length=50), nullable=True),
        sa.Column("receiver_account_number", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("transaction_ref", sa.String(length=255), nullable=True),
        sa.Column("sender_account_number", sa.String(length=255), nullable=True),
        sa.Column("receiver_name", sa.String(length=255), nullable=True),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("current_balance", sa.Float(), nullable=True),
        sa.Column("user_id", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_account",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("account_number", sa.String(length=255), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_data",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_data")
    op.drop_table("user_account")
    op.drop_table("transactions")
    op.drop_table("beneficiaries")
    op.drop_table("users")
    op.drop_table("categories")
    # ### end Alembic commands ###
