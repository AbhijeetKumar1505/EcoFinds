from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Shows all models and their contents with full field details'

    def handle(self, *args, **options):
        # Get all models
        all_models = apps.get_models()
        
        for model in all_models:
            if model._meta.app_label in ['accounts', 'store', 'orders', 'carts', 'ecofinds']:
                self.stdout.write(self.style.SUCCESS(f'\nModel: {model.__name__}'))
                self.stdout.write('=' * 50)
                
                # Get all concrete fields (excluding relations)
                fields = [f.name for f in model._meta.fields]
                self.stdout.write(f'Fields: {", ".join(fields)}\n')
                
                # Get all objects with full field values
                objects = model.objects.all()
                if objects:
                    for obj in objects:
                        self.stdout.write(f'Object ID: {obj.pk}')
                        for field in model._meta.fields:
                            value = getattr(obj, field.name)
                            self.stdout.write(f'  {field.name}: {value}')
                        self.stdout.write('-' * 50)
                else:
                    self.stdout.write('No objects found\n')
