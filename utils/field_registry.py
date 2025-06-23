class FieldType:
    def __init__(
        self,
        name,
        sql_type="TEXT",
        validator=None,
        default_width=6,
        default_height=4,
        macro=None,
        filter_macro=None,
        normalizer=None,
        numeric=False,
        allows_options=False,
        allows_foreign_key=False,
        searchable=False,
    ):
        self.name = name
        self.sql_type = sql_type
        self.validator = validator
        self.default_width = default_width
        self.default_height = default_height
        self.macro = macro
        self.filter_macro = filter_macro
        self.normalizer = normalizer
        self.numeric = numeric
        self.allows_options = allows_options
        self.allows_foreign_key = allows_foreign_key
        self.searchable = searchable

FIELD_TYPES = {}

def register_type(
    name,
    sql_type="TEXT",
    validator=None,
    default_width=6,
    default_height=4,
    macro=None,
    filter_macro=None,
    normalizer=None,
    numeric=False,
    allows_options=False,
    allows_foreign_key=False,
    searchable=False,
):
    FIELD_TYPES[name] = FieldType(
        name,
        sql_type,
        validator,
        default_width,
        default_height,
        macro,
        filter_macro,
        normalizer,
        numeric,
        allows_options,
        allows_foreign_key,
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

