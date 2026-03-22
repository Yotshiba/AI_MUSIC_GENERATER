from django.db import models

from .library import Library


class Folder(models.Model):
    """A named folder inside a Library."""

    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
