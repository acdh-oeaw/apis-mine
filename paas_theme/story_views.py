from django.views.generic import TemplateView

from . analyze_utils import get_ns, nazi_komm_df


class NationalSozialismusStory(TemplateView):
    
    template_name = 'theme/story_ns.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ns_members'] = get_ns()
        context['nazi_komm'] = nazi_komm_df().to_dict('records')
        return context