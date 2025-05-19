from django.db import models

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    sample_input = models.TextField()
    sample_output = models.TextField()
    explanation = models.TextField(blank=True, null=True)  # ✅ Added this line
    max_score = models.IntegerField(default=10)
    
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    topics = models.ManyToManyField(Topic, blank=True)
    companies = models.ManyToManyField(Company, blank=True)
    year_asked = models.PositiveIntegerField(blank=True, null=True)
    
    # New custom 'id' field
    custom_id = models.PositiveIntegerField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically assign a custom ID if it's not already set
        if self.custom_id is None:
            # Get the last custom ID and increment it
            last_question = Question.objects.order_by('custom_id').last()
            if last_question:
                self.custom_id = last_question.custom_id + 1
            else:
                self.custom_id = 1  # Starting from 1 if no questions exist yet
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class TestCase(models.Model):
    question = models.ForeignKey(Question, related_name='test_cases', on_delete=models.CASCADE)
    input_data = models.JSONField()
    expected_output = models.JSONField()

    def __str__(self):
        return f"TestCase for Q{self.question.id}"