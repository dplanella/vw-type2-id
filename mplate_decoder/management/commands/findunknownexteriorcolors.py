from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate


class Command(BaseCommand):
    help = 'Finds unknown exterior color combinations'

    def handle(self, *args, **options):
        for mplate in Mplate.objects.all():
            description = mplate.get_exteriorcolor_description()
            model_year = mplate.model_year

            if 'Unknown exterior color code' in description:
                self.stdout.write(
                    self.style.WARNING(
                        f'{description}, year {model_year}. '
                    ) +
                    f'M-plate: {mplate.chassis_number_short}'
                )
