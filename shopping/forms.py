from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div

from .models import (
    Family, FamilyMember, UserProfile, GroceryStore, StoreLocation,
    ProductCategory, GroceryItem, ShoppingList, ShoppingListItem
)

class ShoppingListForm(forms.ModelForm):
    """Form for creating and editing shopping lists"""
    template_list = forms.ModelChoiceField(
        queryset=ShoppingList.objects.none(),
        required=False,
        help_text="Copy items from an existing list"
    )
    
    class Meta:
        model = ShoppingList
        fields = ['name', 'store', 'family']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter list name'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show families the user belongs to
        if self.user:
            user_families = Family.objects.filter(members__user=self.user)
            self.fields['family'].queryset = user_families
            
            # Stores available to the user's families
            self.fields['store'].queryset = GroceryStore.objects.filter(
                families__in=user_families
            ).distinct()
            
            # Lists that can be used as templates
            self.fields['template_list'].queryset = ShoppingList.objects.filter(
                family__in=user_families
            ).order_by('-created_at')
        
        # Crispy forms setup
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', wrapper_class='form-group'),
            Field('family', wrapper_class='form-group'),
            Field('store', wrapper_class='form-group'),
            Field('template_list', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML("<a href='{% url \"groceries:lists\" %}' class='btn btn-outline'>Cancel</a>"),
                css_class='form-group mt-4'
            )
        )


class FamilyForm(forms.ModelForm):
    """Form for creating and editing families"""
    class Meta:
        model = Family
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter family name'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML("<a href='{% url \"groceries:family\" %}' class='btn btn-outline'>Cancel</a>"),
                css_class='form-group mt-4'
            )
        )


class FamilyMemberForm(forms.ModelForm):
    """Form for adding members to a family"""
    email = forms.EmailField(
        label="Email address",
        required=True,
        help_text="The email address of the person you want to invite"
    )
    is_admin = forms.BooleanField(
        label="Make this person an admin",
        required=False
    )
    
    class Meta:
        model = FamilyMember
        fields = ['email', 'is_admin']
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', wrapper_class='form-group'),
            Field('is_admin', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Invite', css_class='btn btn-primary'),
                css_class='form-group mt-3'
            )
        )


class GroceryStoreForm(forms.ModelForm):
    """Form for creating and editing stores"""
    families = forms.ModelMultipleChoiceField(
        queryset=Family.objects.none(),
        required=False,
        help_text="Select which families can use this store",
        widget=forms.CheckboxSelectMultiple
    )
    
    class Meta:
        model = GroceryStore
        fields = ['name', 'address', 'website', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter store name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Store address'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['families'].queryset = Family.objects.filter(
                members__user=self.user
            ).distinct()
        
        # If editing an existing store, preselect the families
        if self.instance.pk:
            self.initial['families'] = self.instance.families.all()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', wrapper_class='form-group'),
            Field('address', wrapper_class='form-group'),
            Field('website', wrapper_class='form-group'),
            Field('logo', wrapper_class='form-group'),
            Field('families', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML("<a href='{% url \"groceries:stores\" %}' class='btn btn-outline'>Cancel</a>"),
                css_class='form-group mt-4'
            )
        )


class StoreLocationForm(forms.ModelForm):
    """Form for creating and editing store locations"""
    class Meta:
        model = StoreLocation
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location name'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Order in store (e.g. 1, 2, 3)'})
        }
    
    def __init__(self, *args, **kwargs):
        self.store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', wrapper_class='form-group'),
            Field('sort_order', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML("<a href='{% url \"groceries:store_detail\" pk=store.pk %}' class='btn btn-outline'>Cancel</a>"),
                css_class='form-group mt-3'
            )
        )


class GroceryItemForm(forms.ModelForm):
    """Form for creating and editing grocery items"""
    class Meta:
        model = GroceryItem
        fields = ['name', 'description', 'category', 'brand', 'barcode', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter item name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Item description'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item brand (e.g. Heinz)'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPC or EAN barcode'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/image.jpg'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make sure all categories are available
        self.fields['category'].queryset = ProductCategory.objects.all().order_by('name')
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', wrapper_class='form-group'),
            Row(
                Column(Field('brand'), css_class='col-md-6'),
                Column(Field('category'), css_class='col-md-6'),
                css_class='form-row'
            ),
            Field('description', wrapper_class='form-group'),
            Row(
                Column(Field('barcode'), css_class='col-md-6'),
                Column(Field('image_url'), css_class='col-md-6'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML("<a href='{% url \"groceries:dashboard\" %}' class='btn btn-outline'>Cancel</a>"),
                css_class='form-group mt-4'
            )
        )


class ShoppingListItemForm(forms.ModelForm):
    """Form for adding or editing an item on a shopping list"""
    class Meta:
        model = ShoppingListItem
        fields = ['item', 'quantity', 'unit', 'note']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '1'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. kg, pkg'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Add a note about this item'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.shopping_list = kwargs.pop('shopping_list', None)
        super().__init__(*args, **kwargs)
        
        # Hide the item field in the form - it will be set programmatically
        self.fields['item'].widget = forms.HiddenInput()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('item', type='hidden'),
            Row(
                Column(Field('quantity'), css_class='col-6'),
                Column(Field('unit'), css_class='col-6'),
                css_class='form-row'
            ),
            Field('note', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Add to List', css_class='btn btn-primary'),
                css_class='form-group mt-3'
            )
        )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profiles"""
    class Meta:
        model = UserProfile
        fields = ['default_family', 'dark_mode', 'show_categories']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['default_family'].queryset = Family.objects.filter(
                members__user=self.user
            ).distinct()
            
        # Add field labels and help text
        self.fields['show_categories'].label = "Show Categories in Shopping Lists"
        self.fields['show_categories'].help_text = "When enabled, items will be grouped by store section in your shopping lists"
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('default_family', wrapper_class='form-group'),
            Field('dark_mode', wrapper_class='form-group'),
            Field('show_categories', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Save Changes', css_class='btn btn-primary'),
                css_class='form-group mt-4'
            )
        )


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', wrapper_class='form-group'),
            Field('email', wrapper_class='form-group'),
            Field('password1', wrapper_class='form-group'),
            Field('password2', wrapper_class='form-group'),
            Div(
                Submit('submit', 'Register', css_class='btn btn-primary'),
                css_class='form-group mt-4'
            )
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user