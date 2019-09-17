from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate, MplateDecoder


class Command(BaseCommand):
    help = 'Finds unknown M-codes'

    def handle(self, *args, **options):
        for mplate in Mplate.objects.all():
            decoder = MplateDecoder(mplate)

            mcodes = decoder.get_mcodes()

            for mcode, description in mcodes.items():
                if description == 'Unknown code':
                    self.stdout.write(
                        self.style.ERROR('{}: {}. M-plate: {}'.format(
                            mcode, description,
                            mplate.chassis_number_short)))
