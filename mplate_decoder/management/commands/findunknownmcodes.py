from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate, MplateDecoder


class Command(BaseCommand):
    help = 'Finds unknown M-codes'

    def handle(self, *args, **options):

        unknowns = {}

        for mplate in Mplate.objects.all():
            decoder = MplateDecoder(mplate)

            mcodes = decoder.get_mcodes()

            for mcode, description in mcodes.items():
                if 'Unknown' in description or 'Undefined' in description:

                    try:
                        unknowns[f'{mcode}: {description}'].append(
                            mplate.chassis_number_short)
                    except KeyError:
                        unknowns[f'{mcode}: {description}'] = \
                            [mplate.chassis_number_short]

        for unknown, mplate_list in sorted(unknowns.items(), key=lambda item: item[0]):
            self.stdout.write(
                self.style.WARNING(
                    f'{unknown}. '
                    ) +
                'M-plates: ' + ', '.join(mplate_list)
                )
