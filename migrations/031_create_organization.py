"""Peewee migrations -- 031_create_organization.py.

This migration creates the Organization table to store organization information

Some examples (model - class or model_name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name
    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import peewee as pw

from frigate.models import Organization, UserOrganization

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    UserOrganization._meta.database = database
    Organization._meta.database = database

    migrator.sql(
        """
        CREATE TABLE IF NOT EXISTS "Organization" (
            "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            "admin_id" VARCHAR(30) NOT NULL,
            "name" VARCHAR(30) NOT NULL
        )
        """
    )

    migrator.sql(
        """
        CREATE TABLE IF NOT EXISTS "UserOrganization" (
            "user_id" VARCHAR(30) NOT NULL,
            "org_id" INTEGER NOT NULL DEFAULT 0,
            "role" VARCHAR(20) NOT NULL,
            FOREIGN KEY ("org_id") REFERENCES "organization" ("id") ON DELETE CASCADE
        )
        """
    )

    migrator.sql(
        'CREATE UNIQUE INDEX IF NOT EXISTS "userorganization_user_index" ON "userorganization" ("user_id", "org_id")'
    )


def rollback(migrator, database, fake=False, **kwargs):
    migrator.sql('DROP TABLE IF EXISTS "userorganization"')
    migrator.sql('DROP TABLE IF EXISTS "organization"')
