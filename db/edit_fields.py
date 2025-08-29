import json
from db.database import get_connection
from db.config import get_layout_defaults
from db.validation import validate_table, validate_field
from utils.field_registry import get_field_type, get_type_size_map


def add_field_to_schema(
    table,
    field_name,
    field_type,
    field_options=None,
    foreign_key=None,
    layout=None,
    styling=None,
    title: int | bool = 0,
    readonly: int | bool = 0,
):
    """Insert a new field into the field_schema table."""
    validate_table(table)
    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Serialize the list of options (if any) to JSON text
        options_str = json.dumps(field_options or [])
        styling_str = json.dumps(styling) if styling else None

        # 2) Compute the new field's row_start by finding the current bottom edge
        cur.execute(
            "SELECT COALESCE(MAX(row_start + row_span), 0) FROM field_schema WHERE table_name = ?",
            (table,),
        )
        max_bottom = cur.fetchone()[0]  # if no rows yet, that's 0

        # 3) Determine col_start, col_span, row_start, row_span
        defaults = get_layout_defaults() or {}
        width_overrides = defaults.get('width', {})
        height_overrides = defaults.get('height', {})
        size_map = get_type_size_map()

        ft = get_field_type(field_type)

        col_start = 0
        base_width, base_height = size_map.get(
            field_type,
            (
                ft.default_width if ft else 6,
                ft.default_height if ft else 4,
            ),
        )
        col_span = width_overrides.get(field_type, base_width)
        row_start = max_bottom
        row_span = height_overrides.get(field_type, base_height)

        # 4) Insert into field_schema including optional 'title' and 'readonly' flags
        title_flag = 1 if bool(title) else 0
        readonly_flag = 1 if bool(readonly) else 0
        cur.execute("PRAGMA table_info('field_schema')")
        cols = {r[1] for r in cur.fetchall()}

        col_names = [
            'table_name', 'field_name', 'field_type', 'field_options', 'foreign_key',
            'col_start', 'col_span', 'row_start', 'row_span'
        ]
        values = [
            table, field_name, field_type, options_str, foreign_key,
            col_start, col_span, row_start, row_span
        ]
        if 'title' in cols:
            col_names.append('title')
            values.append(title_flag)
        if 'readonly' in cols:
            col_names.append('readonly')
            values.append(readonly_flag)
        col_names.append('styling')
        values.append(styling_str)

        placeholders = ', '.join(['?'] * len(values))
        cur.execute(
            f"INSERT INTO field_schema ({', '.join(col_names)}) VALUES ({placeholders})",
            tuple(values),
        )
        conn.commit()

def add_column_to_table(table_name, field_name, field_type):
    from db.database import get_connection

    validate_table(table_name)

    ft = get_field_type(field_type)
    if not ft:
        raise ValueError(f"Unsupported field type: {field_type}")
    sql_type = ft.sql_type

    # Validate names are safe (simple alphanumeric check)
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name}")
    if not field_name.isidentifier():
        raise ValueError(f"Invalid field name: {field_name}")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{field_name}" {sql_type}')
        conn.commit()

def drop_column_from_table(table, field_name):
    validate_table(table)
    validate_field(table, field_name)
    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Get column definitions and names excluding the one to remove
        cur.execute(f"PRAGMA table_info('{table}')")
        info = cur.fetchall()
        remaining = [row for row in info if row[1] != field_name]
        if len(remaining) == len(info):
            return

        col_defs = []
        col_names = []
        for cid, name, col_type, notnull, dflt, pk in remaining:
            col_names.append(f'"{name}"')
            col_def = f'"{name}" {col_type}' if col_type else f'"{name}"'
            if pk:
                col_def += " PRIMARY KEY"
            if notnull:
                col_def += " NOT NULL"
            if dflt is not None:
                col_def += f" DEFAULT {dflt}"
            col_defs.append(col_def)

        cols_csv = ", ".join(col_names)
        temp_table = f"{table}_temp"

        # 2) Create temp table and copy data while preserving column definitions
        cur.execute(f'CREATE TABLE "{temp_table}" ({", ".join(col_defs)})')
        cur.execute(
            f'INSERT INTO "{temp_table}" ({cols_csv}) SELECT {cols_csv} FROM "{table}"'
        )
        # 3) Drop original
        cur.execute(f'DROP TABLE "{table}"')
        # 4) Rename temp to original
        cur.execute(f'ALTER TABLE "{temp_table}" RENAME TO "{table}"')

        conn.commit()

def remove_field_from_schema(table, field_name):
    validate_table(table)
    validate_field(table, field_name)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM field_schema WHERE table_name = ? AND field_name = ?",
            (table, field_name),
        )
        conn.commit()
