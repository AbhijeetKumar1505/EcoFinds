from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import Account, UserProfile


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    phone_number = forms.CharField(max_length=15)
    email = forms.EmailField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Create Password',
        'class': 'form-control'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'class': 'form-control'
    }))
    communication_preference = forms.ChoiceField(
        choices=UserProfile.COMMUNICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    preferred_language = forms.ChoiceField(
        choices=UserProfile.LANGUAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    other_language = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your language'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        preferred_language = cleaned_data.get('preferred_language')
        other_language = cleaned_data.get('other_language')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        if preferred_language == 'other' and not other_language:
            raise forms.ValidationError("Please specify your language when selecting 'Other'")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class PaymentDetailsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['account_holder_name', 'bank_name', 'account_number', 'ifsc_code', 'branch_name']

    def __init__(self, *args, **kwargs):
        super(PaymentDetailsForm, self).__init__(*args, **kwargs)
        self.fields['account_holder_name'].widget.attrs['placeholder'] = 'Enter Account Holder Name'
        self.fields['bank_name'].widget.attrs['placeholder'] = 'Enter Bank Name'
        self.fields['account_number'].widget.attrs['placeholder'] = 'Enter Account Number'
        self.fields['ifsc_code'].widget.attrs['placeholder'] = 'Enter IFSC Code'
        self.fields['branch_name'].widget.attrs['placeholder'] = 'Enter Branch Name'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages = {'invalid':("Image files only")}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('address_line_1', 'address_line_2', 'city', 'state', 'country', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
