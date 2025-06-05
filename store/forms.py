from django import forms
from .models import Product, ReviewRating, Category, Auction, Bid
from django.utils import timezone

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

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['start_price', 'end_time', 'min_bid_increment']
        widgets = {
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if end_time <= timezone.now():
            raise forms.ValidationError("End time must be in the future")
        return end_time

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)
        if self.auction:
            self.fields['amount'].widget.attrs['min'] = str(self.auction.current_price + self.auction.min_bid_increment)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.auction:
            if amount < self.auction.current_price + self.auction.min_bid_increment:
                raise forms.ValidationError(f"Bid must be at least {self.auction.min_bid_increment} more than current price")
        return amount
