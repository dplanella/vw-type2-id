from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate, MplateDecoder


class Command(BaseCommand):
    help = 'Finds unknown exterior color combinations'

    def handle(self, *args, **options):
        for mplate in Mplate.objects.all():
            decoder = MplateDecoder(mplate)

            description = mplate.get_exteriorcolor_description()
            model_year = decoder.get_model_year().year

            if 'Unknown exterior color code' in description:
                self.stdout.write(
                    self.style.WARNING(
                        f'{description}, year {model_year}. '
                    ) +
                    f'M-plate: {mplate.chassis_number_short}'
                )
