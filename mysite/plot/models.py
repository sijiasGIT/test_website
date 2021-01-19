from django.db import models

class Shareholder(models.Model):
	pid = models.CharField(max_length=200)
	name = models.CharField(max_length=200)
	address = models.CharField(max_length=200)
	share = models.IntegerField(default=0)
	percent = models.FloatField()
	def __str__(self):
		return self.name

class Participant(models.Model):
	date = models.CharField(max_length=10)
	pid = models.CharField(max_length=2000)
	name = models.CharField(max_length=2000)
	def __str__(self):
		return self.date