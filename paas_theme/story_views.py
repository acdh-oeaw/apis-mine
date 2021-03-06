from paas_theme.analyze_views import mitglieder
from django.views.generic import TemplateView

from . analyze_utils import get_ns, nazi_komm_df, proposed_by_nazi_data, ruhend_gestellt_df, kommission_mitglied_per_year
from . provide_data import NATIONALSOZIALISTEN

class NationalSozialismusStory(TemplateView):
    
    template_name = 'theme/story_ns.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposed_by_nazi_df = proposed_by_nazi_data()
        proposed_by_nazi_grouped_by_nazi = proposed_by_nazi_df.groupby(
            ['NSDAP Mitglied']
        ).size().reset_index(name='counts')
        proposed_by_nazi = proposed_by_nazi_df.groupby(
            ['gewähltes Mitglied']
        ).size().reset_index(name='counts')
        kommissionen = nazi_komm_df()
        komm_grouped = kommissionen.groupby(['related_institution__name']).size().reset_index(name='counts')
        member_grouped = kommissionen.groupby(['related_person__name']).size().reset_index(name='counts')
        
        context['mitglieder_kommission'] = kommission_mitglied_per_year(
            start_year=1936, end_year=1961
        )
        context['nazi_kommission'] = kommission_mitglied_per_year(
            person=NATIONALSOZIALISTEN, start_year=1936, end_year=1961
        )
        context['ns_members'] = get_ns()
        context['nazi_komm'] = kommissionen.to_dict('records')
        context['komm_grouped_html'] = komm_grouped.sort_values(by=['counts'], ascending=False).set_index('related_institution__name').to_html(table_id='kommByNazi')
        context['member_grouped'] = member_grouped.sort_values(by=['counts'], ascending=False).set_index('related_person__name').to_html(table_id='naziByKomm')
        context['proposed_by_nazi_table'] = proposed_by_nazi_df[['gewähltes Mitglied', 'NSDAP Mitglied', 'Wahldatum', 'Art der Mitgliedschaft']].to_html(table_id='proposedByNaziAll', index=False, border=0)
        context['proposed_by_nazi_grouped_by_nazi'] = proposed_by_nazi_grouped_by_nazi.sort_values(by=['counts'], ascending=False).set_index('NSDAP Mitglied').to_html(table_id='nazisProposing')
        context['proposed_by_nazi'] = proposed_by_nazi.sort_values(by=['counts'], ascending=False).set_index('gewähltes Mitglied').to_html(table_id='proposedByNazi')
        context['ruhend'] = ruhend_gestellt_df().to_dict('records')
        context['ruhend_by_klasse'] = ruhend_gestellt_df().groupby(['related_institution__name']).size().reset_index(name='counts').set_index('related_institution__name').to_html(table_id='ruhendByKlasse')

        return context