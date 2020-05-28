from django.apps import AppConfig
import vinaigrette


class MplateDecoderConfig(AppConfig):
    name = 'mplate_decoder'

    def ready(self):
        from .models import Mcode

        vinaigrette.register(Mcode, ['description', 'remarks'])
