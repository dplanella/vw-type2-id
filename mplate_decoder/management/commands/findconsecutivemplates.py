from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate
from itertools import groupby
from operator import itemgetter


class Command(BaseCommand):
    help = 'Finds consecutive M-plates'

    def handle(self, *args, **options):

        consec = []

        for mplate in Mplate.objects.all():
            consec.append(int(mplate.chassis_number_short))

        consec.sort()

        for k, g in groupby(enumerate(consec), lambda ix: ix[0] - ix[1]):
            group = list(map(itemgetter(1), g))
            if len(group) > 1:
                print(group)
