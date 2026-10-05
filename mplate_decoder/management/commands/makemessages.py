from vinaigrette.management.commands import makemessages


class Command(makemessages.Command):
    # vinaigrette 2.0.1 sets True, which Django 4.1+ rejects
    requires_system_checks = '__all__'
