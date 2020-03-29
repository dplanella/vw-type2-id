from django.contrib import admin

from .models import (
    Mplate, ExportDestination, Type2Model,
    Type2ModelConfiguration, Type2ModelExtra,
    InteriorColor, ExteriorColor, Color,
    Engine, Gearbox, Mcode, McodeCollection,
    VwType2Model,
)

admin.site.register(Engine)
admin.site.register(Gearbox)


@admin.register(Type2ModelExtra)
class Type2ModelExtraAdmin(admin.ModelAdmin):
    search_fields = ('model', 'extras')
    list_display = ('model', 'extras', 'description', 'years')


@admin.register(Type2ModelConfiguration)
class Type2ModelConfigurationAdmin(admin.ModelAdmin):
    search_fields = ('model', 'configuration', 'description')
    list_display = ('model', 'configuration', 'description')


@admin.register(Type2Model)
class Type2ModelAdmin(admin.ModelAdmin):
    search_fields = ('model', )
    list_display = (
        'model',
        'description',
    )


@admin.register(Mplate)
class MplateAdmin(admin.ModelAdmin):
    search_fields = ('chassis_number_short',
                     'm_codes',
                     )
    list_filter = ('emden',
                   'model_year',
                   )
    list_display = ('chassis_number_short',
                    'm_codes',
                    'paint_and_interior',
                    'export_destination',
                    'destination_country',
                    'model',
                    'aggregate_code',
                    'emden',
                    'model_year',
                    'production_date_as_time',
                    'owner',
                    'created_at'
                    )
    readonly_fields = ('owner', 'created_at', 'updated_at')
    list_display_links = ('chassis_number_short', )
    view_on_site = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(McodeCollection)
class McodeCollectionAdmin(admin.ModelAdmin):
    search_fields = (
        'm_code',
        'collection',
        )
    list_display = (
        'm_code',
        'collection',
        'years',
        'remarks',
        'source',
    )


@admin.register(InteriorColor)
class InteriorColorAdmin(admin.ModelAdmin):
    search_fields = ('plate_code',
                     'color_name',
                     )
    list_display = (
        'plate_code',
        'color_name',
        'material',
        'years',
        'remarks',
        'image',
    )


@admin.register(ExteriorColor)
class ExteriorColorAdmin(admin.ModelAdmin):
    search_fields = (
        'plate_code',
        'lacquer_code_body',
        'lacquer_code_roof',
        'remarks',
    )
    list_display = (
        'plate_code',
        'lacquer_code_body',
        'lacquer_code_roof',
        'years',
        'sonderlackierung',
        'remarks',
    )


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ('lacquer_code', 'color_name')
    list_display = ('lacquer_code',
                    'color_name',
                    'chip')


@admin.register(Mcode)
class McodeAdmin(admin.ModelAdmin):
    search_fields = (
        'm_code',
        'description',
    )
    list_display = (
        'm_code',
        'description',
        'years',
        'remarks',
        'source'
        )


@admin.register(ExportDestination)
class ExportDestinationAdmin(admin.ModelAdmin):
    search_fields = (
        'export_code',
        'destination',
        'country',
    )
    list_display = (
        'export_code',
        'destination',
        'country',
        'region',
        'city',
        'port',
        'notes',
    )


@admin.register(VwType2Model)
class VwType2ModelAdmin(admin.ModelAdmin):
    search_fields = (
        'model',
        'model_description',
        'extras_description',
    )
    list_display = (
        'model',
        'configuration',
        'extras',
        'model_description',
        'configuration_description',
        'extras_description',
        'm_codes',
        'chassis_plate',
        'years',
        'schematic_vector_short',
    )
    list_filter = (
        'model',
        'configuration',
        'extras',
    )
    save_as = True

    def schematic_vector_short(self, obj):
        schematic_vector_short = obj.schematic_vector[:20]
        if schematic_vector_short:
            schematic_vector_short += ' [...]'
        return schematic_vector_short

    schematic_vector_short.short_description = "Schematic"
