from db.schema import get_field_schema

def validate_table(table: str):
    schema = get_field_schema()
    if table not in schema:
        raise ValueError(f"Invalid table: {table}")

def validate_field(table: str, field: str):
    schema = get_field_schema()
    if table not in schema:
        raise ValueError(f"Invalid table: {table}")
    if field not in schema[table]:
        raise ValueError(f"Invalid column `{field}` for table `{table}`")

def validate_fields(table: str, fields: list[str]):
    for f in fields:
        validate_field(table, f)
