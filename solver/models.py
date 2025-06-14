from django.db import models
from django.contrib.auth.models import User

class MathProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    input_type = models.CharField(max_length=10, choices=[
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('PDF', 'PDF')
    ])
    original_input = models.TextField(blank=True, null=True)
    extracted_problem = models.TextField(null=True,blank=True)
    solution = models.TextField()
    explanation = models.TextField()
    processing_time = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Problem {self.id}"