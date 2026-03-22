import uuid

from django.db import models


class User(models.Model):
    """Domain entity representing a user of the AI Music Generator."""

    class UserRole(models.TextChoices):
        CREATOR = 'Creator', 'Creator'
        ADMIN = 'Admin', 'Admin'

    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CREATOR,
    )

    def __str__(self):
        return self.name


class Profile(models.Model):
    """One-to-one profile for a User, holding token balance."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token_balance = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.name}"


class TokenRecord(models.Model):
    """Records token transactions (earned or spent) for a User."""

    class TokenType(models.TextChoices):
        EARNED = 'Earned', 'Earned'
        SPENT = 'Spent', 'Spent'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_records')
    amount = models.IntegerField()
    type = models.CharField(max_length=10, choices=TokenType.choices)

    def __str__(self):
        return f"{self.type} {self.amount} tokens – {self.user.name}"


class Library(models.Model):
    """Each User has exactly one Library that organises their songs into folders."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='library')

    class Meta:
        verbose_name_plural = 'libraries'

    def __str__(self):
        return f"Library of {self.user.name}"


class Folder(models.Model):
    """A named folder inside a Library."""

    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Song(models.Model):
    """Core domain entity representing a generated song."""

    class SongStatus(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        GENERATING = 'Generating', 'Generating'
        COMPLETED = 'Completed', 'Completed'
        FAILED = 'Failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='songs',
    )

    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=100, blank=True)
    occasion = models.CharField(max_length=100, blank=True)
    singer_style = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    duration = models.PositiveIntegerField(help_text='Duration in seconds', default=0)
    status = models.CharField(
        max_length=12,
        choices=SongStatus.choices,
        default=SongStatus.DRAFT,
    )
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.title
