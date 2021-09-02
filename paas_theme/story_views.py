from django.views.generic import TemplateView

from . analyze_utils import get_ns, nazi_komm_df


class NationalSozialismusStory(TemplateView):
    
    template_name = 'theme/story_ns.html'

    def get_context_data(self, **kwargs):
        kommissionen = nazi_komm_df()
        komm_grouped = kommissionen.groupby(['related_institution__name']).size().reset_index(name='counts')
        member_grouped = kommissionen.groupby(['related_person__name']).size().reset_index(name='counts')
        context = super().get_context_data(**kwargs)
        context['ns_members'] = get_ns()
        context['nazi_komm'] = kommissionen.to_dict('records')
        context['komm_grouped_html'] = komm_grouped.sort_values(by=['counts'], ascending=False).set_index('related_institution__name').to_html(table_id='kommByNazi')
        context['member_grouped'] = member_grouped.sort_values(by=['counts'], ascending=False).set_index('related_person__name').to_html(table_id='naziByKomm')

        return context