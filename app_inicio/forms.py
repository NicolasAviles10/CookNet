from django import forms
from .models import Receta, UsuarioFavorito

class FavoritosForm(forms.Form):
    search = forms.CharField(required=False, label="Buscar receta", widget=forms.TextInput(attrs={"placeholder": "Buscar por nombre...", "class": "form-control mb-2"}))
    favoritos = forms.ModelMultipleChoiceField(
        queryset=Receta.objects.order_by('-minutes')[:100],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Selecciona hasta 5 recetas favoritas"
    )

    def clean_favoritos(self):
        data = self.cleaned_data['favoritos']
        if len(data) > 5:
            raise forms.ValidationError("Solo puedes seleccionar hasta 5 recetas favoritas.")
        return data
