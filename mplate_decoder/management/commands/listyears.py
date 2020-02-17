from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate


class Command(BaseCommand):
    help = 'List submitted years'

    def handle(self, *args, **options):

        years = {}
        years_submissions_count = 0

        for mplate in Mplate.objects.all():
            model_year = mplate.model_year

            try:
                years[model_year].append(
                    mplate.chassis_number_short)
            except KeyError:
                years[model_year] = \
                            [mplate.chassis_number_short]
            years_submissions_count += 1

        sorted_years = {k: v for k, v in sorted(
            years.items(),
            key=lambda item: len(item[1]),
            reverse=True)}

        for year, mplates in sorted_years.items():
            self.stdout.write(
                self.style.WARNING(
                    f'{year}: '
                    ) +
                f"{len(mplates)}" +
                f" ({round((len(mplates)/years_submissions_count)*100, 1)}%)"
                )
