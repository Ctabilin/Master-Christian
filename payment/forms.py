from django import forms
from .models import ShippingAddress, CustomerSubmission, UserDesign

class ShippingForm(forms.ModelForm):
    shipping_full_name = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name'}),required=True)
    shipping_email = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Email'}),required=True)
    shipping_phone = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Phone'}),required=True)
    shipping_address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Address 1'}),required=True)
    shipping_address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Address 2'}),required=False)
    shipping_barangay = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Barangay'}),required=True)
    shipping_city = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'City'}),required=True)
    shipping_zipcode = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Zipcode'}),required=True)

    class Meta:
        model = ShippingAddress
        fields = ['shipping_full_name','shipping_email', 'shipping_phone', 'shipping_address1', 'shipping_barangay', 'shipping_city', 'shipping_zipcode']

        exclude = ['user',]

class PaymentForms(forms.Form):
    card_name = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Name On Card'}),required=True)
    card_number = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Card Number'}),required=True)
    card_exp_date = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Expiration Date'}),required=True)
    card_cvv_number = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'CVV Number'}),required=True)
    card_address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Billing Address 1'}),required=True)
    card_address2 = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Billing Address 2'}),required=False)
    card_city = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Billig City'}),required=True)
    card_zipcode = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Billing Zipcode'}),required=True)
    card_country = forms.CharField(label="", widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Billing Country'}),required=True)

#not in use
class CustomerSubmissionForm(forms.ModelForm):
    class Meta:
        model = CustomerSubmission
        fields = ['description', 'image']

class UserDesignForm(forms.ModelForm):
    class Meta:
        model = UserDesign
        fields = ['user_design', 'user_description']





