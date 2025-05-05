import json
from django.db import models
from utils import make_UUID
from django.utils import timezone
from django.core.exceptions import ValidationError



class DbModel(models.Model):
    uuid = models.UUIDField(default=make_UUID, blank=True)
    date_created = models.DateTimeField(auto_now=True, auto_now_add=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ArrayField(models.TextField):
    """
    Array field for storing collection of a single data_type
    Useful for Vehicle Featues
    """

    def __init__(self, *args, **kwargs):
        self.data_type = kwargs.pop("data_type", None)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        # convert value to pyhton object
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for ArrayField.")
        return []


    def get_prep_value(self, value):
        """Convert Python list to JSON string for database storage."""
        if value is None:
            return "[]"
        if not isinstance(value, list):
            raise ValidationError("ArrayField requires a list.")
        return json.dumps(value)

    def validate(self, value, model_instance):
        """Ensure all items in the list match the specified type (if set)."""
        super().validate(value, model_instance)

        print("Validating ", self, self.data_type, value)

        if value is None:
            raise ValidationError("Value cannot be None.")

        if not isinstance(value, (list)):  # Ensure value is iterable
            raise ValidationError("Value must be a list or tuple.")

        if self.data_type and value:
            for item in value:
                if not type(item) == self.data_type:
                    raise ValidationError(f"All items must be of type {self.data_type}.")

    def from_db_value(self, value, expression, connection):
        """Convert database value to Python list when fetching data."""
        return self.to_python(value)



