from evennia import create_object
from typeclasses.bbs_controller import BBSController

def get_or_create_bbs_controller():
    try:
        controller = BBSController.objects.get(db_key="BBSController")
    except BBSController.DoesNotExist:
        controller = create_object(BBSController, key="BBSController")
        controller.db.boards = {}  # Initialize with an empty boards dictionary
    return controller