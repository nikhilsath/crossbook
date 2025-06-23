class FieldType:
    def __init__(
        self,
        name,
        sql_type="TEXT",
        validator=None,
        default_width=6,
        default_height=4,
        macro=None,
        searchable=False,
    ):
        self.name = name
        self.sql_type = sql_type
        self.validator = validator
        self.default_width = default_width
        self.default_height = default_height
        self.macro = macro
        self.searchable = searchable

FIELD_TYPES = {}

def register_type(
    name,
    sql_type="TEXT",
    validator=None,
    default_width=6,
    default_height=4,
    macro=None,
    searchable=False,
):
    FIELD_TYPES[name] = FieldType(
        name,
        sql_type,
        validator,
        default_width,
        default_height,
        macro,
        searchable,
    )


def get_field_type(name):
    return FIELD_TYPES.get(name)


def get_type_size_map():
    """Return mapping of field type -> (default_width, default_height)."""
    return {
        name: (ft.default_width, ft.default_height)
        for name, ft in FIELD_TYPES.items()
    }

