from django import forms
from .models import AuthUser
from decimal import Decimal
from django.contrib.auth import forms as auth_forms

invalid_error = 'User with this {} already exists.'

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control',
                                                            'required': 'True'}),
                             max_length=254, required=True,
                             error_messages={'unique': invalid_error.format('email')})
    first_name = forms.CharField(max_length=30, required=True,
                                 widget=forms.TextInput(attrs={'class': 'form-control',
                                                               'required': 'True'}))
    last_name = forms.CharField(max_length=30, required=True,
                                widget=forms.TextInput(attrs={'class': 'form-control',
                                                              'required': 'True'}))
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'class':'form-control',
                                                                  'required': 'True'}))
    password2 = forms.CharField(label='Password confirmation',
                                widget=forms.PasswordInput(attrs={'class':'form-control',
                                                                  'required': 'True'}))
    coupon = forms.CharField(label='Coupon code', required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'required': 'False'}))
    class Meta:
        model = AuthUser
        fields = ('email', 'first_name', 'last_name', 'password1',
                  'password2')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class SellerRegistrationForm(RegistrationForm):
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs={'required': 'True'}))

    class Meta:
        model = AuthUser
        fields = ('email', 'first_name', 'last_name', 'password1',
                  'password2')


class EditAccountForm(forms.Form):
    niches = forms.CharField(max_length=250,
                             help_text='If you have multiple, separate each with comma.',
                             required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control niches-input'}))
    price = forms.DecimalField(label='Price Per ShoutOut($US)',
                               widget=forms.NumberInput(attrs={'class': 'form-control'}),
                               min_value=Decimal(0), max_value=Decimal(1000000 * 1000),
                               decimal_places=2)
    note = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}),
                           max_length=1000, label='Other Note/Request', required=False)


class NewAccountForm(EditAccountForm):
    username = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.session_username = kwargs.pop('session_username')
        self.network = kwargs.pop('network')
        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        username = self.cleaned_data['username']
        if self.session_username != username:
            raise forms.ValidationError('This page is outdated.'
                                        ' Please try to authenticate with {} again.'
                                        .format(self.network))
        return self.cleaned_data

class IgSearchForm(forms.Form):
    min_followers = forms.IntegerField(min_value=0, required=False,
                            help_text='Min number of followers')
    max_followers = forms.IntegerField(min_value=0, required=False,
                            help_text='Max number of followers')
    min_cpm = forms.DecimalField(min_value=0, required=False,
                            help_text='Min CPM amount')
    max_cpm = forms.DecimalField(min_value=0, required=False,
                            help_text='Max CPM amount')
    niches = forms.CharField(max_length=255, required=False,
                             help_text='Enter multiple niches by inputting a space or comma.',
                             widget=forms.TextInput(attrs={'class': 'form-control niches-input'}))
    min_engagement = forms.DecimalField(min_value=0, required=False,
                            help_text='Min engagement percent')
    max_engagement = forms.DecimalField(min_value=0, required=False,
                            help_text='Max engagement percent')

class TwSearchForm(forms.Form):
    tw_min_followers = forms.IntegerField(min_value=0, required=False,
                            help_text='Min number of followers',
                            label='Min # followers')
    tw_max_followers = forms.IntegerField(min_value=0, required=False,
                            help_text='Max number of followers',
                            label='Max # followers')
    tw_min_cpm = forms.DecimalField(min_value=0, required=False,
                            help_text='Min CPM amount',
                            label='Min CPM')
    tw_max_cpm = forms.DecimalField(min_value=0, required=False,
                            help_text='Max CPM amount',
                            label='Max CPM')
    tw_niches = forms.CharField(max_length=255, required=False,
                             help_text='Enter multiple niches by pressing enter.',
                             label='Niches',
                             widget=forms.TextInput(attrs={'class': 'form-control niches-input'}))


class LoginForm(auth_forms.AuthenticationForm):
    username = forms.EmailField(max_length=254, label='Email',
                               widget=forms.EmailInput(attrs={'class': 'form-control',
                                                             'required': 'True'}))
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'required': 'True'}))
    next_ = forms.CharField(widget=forms.HiddenInput())


class PassResetForm(auth_forms.PasswordResetForm):
    email = forms.EmailField(label='Email', max_length=254,
                             widget=forms.EmailInput(attrs={'class': 'form-control',
                                                            'required': 'True'}))


class SetPassForm(auth_forms.SetPasswordForm):
    new_password1 = forms.CharField(label="New password",
                                    widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                      'required': 'True'}))
    new_password2 = forms.CharField(label="New password confirmation",
                                    widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                      'required': 'True'}))