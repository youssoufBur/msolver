# serializers.py
import json
from rest_framework import serializers

from .models import MathProblem

class MathProblemSerializer(serializers.ModelSerializer):
    original_input = serializers.SerializerMethodField()

    class Meta:
        model = MathProblem
        fields = '__all__'

    def get_original_input(self, obj):
        # Convertit les chemins Windows en format JSON valide
        if isinstance(obj.original_input, str):
            return obj.original_input.replace('\\', '/')  # Alternative: double les backslashes
        return obj.original_input