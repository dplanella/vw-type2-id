from django.core.management.base import BaseCommand
from mplate_decoder.models import Mplate


class Command(BaseCommand):
    help = 'Save all m-plates'

    def handle(self, *args, **options):
        all_plates = Mplate.objects.all()
        for plate in all_plates:
            plate.save()
