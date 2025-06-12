def validate_table(table: str):
    from db.schema import get_field_schema
    schema = get_field_schema()
    if table not in schema:
        raise ValueError(f"Invalid table: {table}")

def validate_field(table: str, field: str):
    from db.schema import get_field_schema
    schema = get_field_schema()
    if table not in schema:
        raise ValueError(f"Invalid table: {table}")
    if field not in schema[table]:
        raise ValueError(f"Invalid column `{field}` for table `{table}`")

def validate_fields(table: str, fields: list[str]):
    from db.schema import get_field_schema
    for f in fields:
        validate_field(table, f)
