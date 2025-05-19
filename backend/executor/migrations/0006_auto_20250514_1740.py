from django.db import migrations

def populate_custom_ids(apps, schema_editor):
    Question = apps.get_model('executor', 'Question')  # Fetch the Question model
    for index, question in enumerate(Question.objects.all(), start=1):  # Enumerate to get a numbered list
        question.custom_id = index
        question.save()

class Migration(migrations.Migration):

    dependencies = [
        ('executor', '0005_question_custom_id'),  # This should refer to the last migration before this one
    ]

    operations = [
        migrations.RunPython(populate_custom_ids),  # Run the custom function to populate the custom_id
    ]
