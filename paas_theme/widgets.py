import django_filters
from django import forms


class NoUISliderInput(django_filters.widgets.RangeWidget):
    template_name = 'utils/slider.html'
    attr_names = ('date_min', 'date_max')

    class Media:
        css = {'all': ('theme/vendor/noUISlider/nouislider.min.css',
                       'theme/css/slider_custom.css',)}
        js = ("theme/vendor/noUISlider/nouislider.min.js",
              "theme/vendor/wNumb/wNumb.js",)


#https://github.com/Aalto-LeTech/mooc-jutut/blob/ce04a2e4809f95be6edb831836b880791aa6f32b/feedback/filters.py

    def __init__(self, widgets=None, attrs=None):
        if widgets is None:
            widgets = (forms.TextInput, forms.TextInput)
        # NOTE: skip parent init
        super(django_filters.widgets.RangeWidget, self).__init__(widgets,
                                                                 attrs)
