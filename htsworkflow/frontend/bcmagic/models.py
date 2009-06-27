from django.db import models

class KeywordMap(models.Model):
    """
    Mapper object maps keyword|arg1|arg2|...|argN to REST urls
    """
    keyword = models.CharField(max_length=64)
    regex = models.CharField(max_length=1024)
    url_template = models.TextField()
