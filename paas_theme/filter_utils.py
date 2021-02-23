from . utils import person_place_born, person_place_death


def born_in_filter(qs, name, value):
    lookup = '__'.join([name, 'icontains'])
    per_pl_rels = [x.related_person.id for x in person_place_born.filter(**{lookup: value})]
    new_qs = qs.filter(id__in=per_pl_rels)
    return new_qs


def died_in_filter(qs, name, value):
    lookup = '__'.join([name, 'icontains'])
    per_pl_rels = [x.related_person.id for x in person_place_death.filter(**{lookup: value})]
    new_qs = qs.filter(id__in=per_pl_rels)
    return new_qs
