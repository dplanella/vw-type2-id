from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate


class Command(BaseCommand):
    help = 'List submitted countries'

    def handle(self, *args, **options):

        countries = {}
        country_submissions_count = 0

        for mplate in Mplate.objects.all():
            export_dest = mplate._get_export_destination_object()

            if export_dest and (export_dest.country or export_dest.region):

                country_or_region = export_dest.country or export_dest.region
                try:
                    countries[country_or_region].append(
                        mplate.chassis_number_short)
                except KeyError:
                    countries[country_or_region] = \
                                [mplate.chassis_number_short]
                country_submissions_count += 1

        sorted_countries = {k: v for k, v in sorted(
            countries.items(),
            key=lambda item: len(item[1]),
            reverse=True)}

        for country, mplates in sorted_countries.items():
            self.stdout.write(
                self.style.WARNING(
                    f'{country}: '
                    ) +
                f"{len(mplates)}" +
                f" ({round((len(mplates)/country_submissions_count)*100, 1)}%)"
                )
