# Hand-written to match what `makemigrations listings` produces for the
# storage change on Vehicle.video.
#
# This is a no-op at the database level: FileField is a varchar column and the
# storage backend only affects where the file is written. It exists so that
# `makemigrations` reports no pending changes.
from django.db import migrations, models

import listings.models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_car_body_type_listing_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicle',
            name='video',
            field=models.FileField(
                blank=True,
                null=True,
                storage=listings.models.video_storage,
                upload_to='vehicles/videos/',
            ),
        ),
    ]
