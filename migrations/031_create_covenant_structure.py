"""Peewee migrations -- 031_create_covenant_structure.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Create organization, userorganization, station, and camera tables."""

    # Create organization table with integer autoincrement primary key
    migrator.sql("""
        CREATE TABLE IF NOT EXISTS organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(30),
            user_id VARCHAR(30) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(username) ON DELETE CASCADE
        )
    """)

    # Create userorganization table with composite unique constraint
    migrator.sql("""
        CREATE TABLE IF NOT EXISTS userorganization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(30) NOT NULL,
            org_id INTEGER NOT NULL,
            role VARCHAR(20) DEFAULT 'admin',
            UNIQUE (user_id, org_id),
            FOREIGN KEY (user_id) REFERENCES user(username) ON DELETE CASCADE,
            FOREIGN KEY (org_id) REFERENCES organization(id) ON DELETE CASCADE
        )
    """)

    # Create station table
    migrator.sql("""
        CREATE TABLE IF NOT EXISTS station (
            id VARCHAR(32) PRIMARY KEY NOT NULL,
            org_id INTEGER,
            FOREIGN KEY (org_id) REFERENCES organization(id) ON DELETE CASCADE
        )
    """)

    # Create camera table
    migrator.sql("""
        CREATE TABLE IF NOT EXISTS camera (
            id VARCHAR(30) PRIMARY KEY NOT NULL,
            name VARCHAR(30) NOT NULL,
            station_id VARCHAR(32) NOT NULL,
            FOREIGN KEY (station_id) REFERENCES station(id) ON DELETE CASCADE
        )
    """)


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Rollback the migration - drop all created tables."""

    migrator.sql("DROP TABLE IF EXISTS camera")
    migrator.sql("DROP TABLE IF EXISTS station")
    migrator.sql("DROP TABLE IF EXISTS userorganization")
    migrator.sql("DROP TABLE IF EXISTS organization")
