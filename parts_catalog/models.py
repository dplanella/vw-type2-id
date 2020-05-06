from django.db import models
import logging

logger = logging.getLogger(__name__)


class MainGroup(models.Model):

    number = models.PositiveSmallIntegerField(
        unique=True,
        help_text=("Main Group number.")
    )
    description = models.CharField(
        max_length=50,
        help_text=("Main Group description.")
    )


class Illustration(models.Model):
    main_group = models.ForeignKey(
        MainGroup,
        on_delete=models.CASCADE
    )
    sub_group = models.PositiveSmallIntegerField(
        unique=True,
        help_text=("Main Group number.")
    )
    number = models.CharField(
        max_length=7,
        help_text=("Main Group description.")
    )
    image = models.CharField(
        help_text=("Main Group description.")
    )
    description = models.CharField(
        max_length=50,
        help_text=("Main Group description.")
    )
    remark = models.CharField(
        max_length=50,
        help_text=("Main Group description.")
    )
    model = models.CharField(
        max_length=50,
        help_text=("Main Group description.")
    )


