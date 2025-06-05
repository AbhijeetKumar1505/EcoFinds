from django import forms
from .models import Product, ReviewRating, Category

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('category_name'),
        empty_label="Select Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Product
        fields = ['title', 'brand', 'category', 'description', 'price', 'stock', 'condition', 'listing_type', 'location', 'images']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'listing_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'images': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-control'}),
        }
