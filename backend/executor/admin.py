# from django.contrib import admin
# from .models import Question, TestCase, Topic, Company

# class TestCaseInline(admin.TabularInline):
#     model = TestCase
#     extra = 1

# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ['custom_id', 'title', 'description', 'difficulty', 'year_asked']  # Add custom_id here
#     search_fields = ['title', 'description', 'difficulty']
    
#     def get_topics(self, obj):
#         return ", ".join([t.name for t in obj.topics.all()])
#     get_topics.short_description = 'Topics'

#     def get_companies(self, obj):
#         return ", ".join([c.name for c in obj.companies.all()])
#     get_companies.short_description = 'Companies'

# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Topic)
# admin.site.register(Company)


from django.contrib import admin
from .models import Question, TestCase, Topic, Company

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['custom_id', 'title', 'difficulty', 'year_asked']
    search_fields = ['title', 'description', 'difficulty']
    
    # Show fields in the detail (edit) page
    fields = [
        'custom_id',
        'title',
        'description',
        'sample_input',
        'sample_output',
        'explanation',                # ✅ New
        'constraints',                # ✅ New
        'testcase_description',       # ✅ New
        'difficulty',
        'topics',
        'companies',
        'year_asked',
       
    ]

    inlines = [TestCaseInline]

    def get_topics(self, obj):
        return ", ".join([t.name for t in obj.topics.all()])
    get_topics.short_description = 'Topics'

    def get_companies(self, obj):
        return ", ".join([c.name for c in obj.companies.all()])
    get_companies.short_description = 'Companies'

admin.site.register(Question, QuestionAdmin)
admin.site.register(Topic)
admin.site.register(Company)
