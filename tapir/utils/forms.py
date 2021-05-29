from django import forms
from django.forms import ModelForm


class DateInput(forms.DateInput):
    input_type = "date"


class CombinedFormBase(forms.Form):
    # From https://stackoverflow.com/a/24349234/6328976
    form_classes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.form_classes:
            name = f.__name__.lower()
            if f.Meta.model.__name__ in kwargs["initial"]:
                kwargs["instance"] = kwargs["initial"][f.Meta.model.__name__]
            setattr(self, name, f(*args, **kwargs))
            form: ModelForm = getattr(self, name)
            self.fields.update(form.fields)
            self.initial.update(form.initial)

    def is_valid(self):
        is_valid = True
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            if not form.is_valid():
                is_valid = False
        if not super(CombinedFormBase, self).is_valid():
            is_valid = False
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            self.errors.update(form.errors)
        return is_valid

    def clean(self):
        cleaned_data = super(CombinedFormBase, self).clean()
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            cleaned_data.update(form.cleaned_data)
        return cleaned_data

    def save(self):
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            form.save()
