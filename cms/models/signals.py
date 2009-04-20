from django.dispatch import Signal

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired when some of nodes (Title) with applications gets saved
application_post_changed = Signal(providing_args=["instance"])
