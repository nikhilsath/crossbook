import os
from huey import SqliteHuey

# Huey queue for background imports
huey = SqliteHuey(
    'crossbook-tasks',                         # queue name
    filename=os.path.join(os.getcwd(),         # ensure this points to your data/ folder
                          'data',
                          'huey.db'),
    store_none=False                            # don’t clutter the DB with None results
)