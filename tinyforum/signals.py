from django.dispatch import Signal


post_created = Signal(providing_args=["instance", "form", "request"])
post_report_handled = Signal(providing_args=["instance", "form", "request"])
