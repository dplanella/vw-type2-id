from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Assign M-plate to user'

    def add_arguments(self, parser):
        parser.add_argument('chassis_number_short', nargs='+', type=str)
        parser.add_argument('username', nargs='+', type=str)

    def handle(self, *args, **options):
        user_mplate = Mplate.objects.get(
            chassis_number_short=options['chassis_number_short'])
        user = CustomUser.objects.get(username=options['username'])
        user_mplate.owner = user
        user_mplate.save()
        self.stdout.write(f'M-plate {user_mplate} assigned to user {user}')
