from django.apps import AppConfig
import vinaigrette


class MplateDecoderConfig(AppConfig):
    name = 'mplate_decoder'

    def ready(self):
        from .models import (
            Mcode, Engine, Gearbox, Color, ExportDestination,
        )
        vinaigrette.register(Mcode, ['description', 'remarks'])
        vinaigrette.register(Engine, ['engine_type', 'fuel_induction',
                                      'extra_specs'])
        vinaigrette.register(Gearbox, ['gearbox_description'])
        vinaigrette.register(Color, ['color_name'])
        vinaigrette.register(ExportDestination, ['country'])
