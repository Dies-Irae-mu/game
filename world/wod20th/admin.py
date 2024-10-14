from django.contrib import admin
from .models import Stat, ShapeshifterForm
from django import forms
import json 
@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_line', 'category', 'stat_type')
    search_fields = ('name', 'game_line', 'category', 'stat_type')


class ShapeshifterFormAdminForm(forms.ModelForm):
    class Meta:
        model = ShapeshifterForm
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stat_modifier_forms = []
        if self.instance.pk:
            for stat, modifier in self.instance.stat_modifiers.items():
                self.stat_modifier_forms.append({'stat_name': stat, 'modifier': modifier})
        if not self.stat_modifier_forms:
            self.stat_modifier_forms.append({'stat_name': '', 'modifier': ''})

    def clean(self):
        cleaned_data = super().clean()
        stat_modifiers_json = self.data.get('stat_modifiers')
        if stat_modifiers_json:
            try:
                stat_modifiers = json.loads(stat_modifiers_json)
                cleaned_data['stat_modifiers'] = stat_modifiers
                print(f"Cleaned stat_modifiers: {stat_modifiers}")  # Debug print
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON for stat_modifiers")
        else:
            print("No stat_modifiers data found in form submission")  # Debug print
        return cleaned_data

@admin.register(ShapeshifterForm)
class ShapeshifterFormAdmin(admin.ModelAdmin):
    form = ShapeshifterFormAdminForm
    fieldsets = (
        (None, {
            'fields': ('name', 'shifter_type', 'description', 'form_message')
        }),
        ('Stats', {
            'fields': ('rage_cost', 'difficulty', 'stat_modifiers')
        }),
        ('Advanced', {
            'fields': ('lock_string',),
            'classes': ('collapse',)
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['shifter_type'].help_text = 'Enter the type of shapeshifter. This will be automatically sanitized.'
        form.base_fields['lock_string'].help_text = 'Enter a lock string to restrict access to this form. Leave blank for no restrictions.'
        form.base_fields['form_message'].help_text = 'Enter a message to be displayed when this form is assumed.'
        return form

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['stat_modifier_forms'] = context['adminform'].form.stat_modifier_forms
        return super().render_change_form(request, context, add, change, form_url, obj)

    class Media:
        js = ('admin/js/jquery.init.js', 'admin/js/shifter_form_admin.js')

    def save_model(self, request, obj, form, change):
        print(f"Saving model with stat_modifiers: {obj.stat_modifiers}")  # Debug print
        super().save_model(request, obj, form, change)