from rest_framework import serializers
from .provide_data import classes, NATIONALSOZIALISTEN
import datetime

class KommissionZeitstrahl(serializers.Serializer):
    name = serializers.CharField()
    start = serializers.DateField(source="start_date")
    ende = serializers.DateField(source="end_date")
    mitglieder = serializers.SerializerMethodField(method_name="count_members")

    def count_members(self, obj):
        res = dict()
        members = obj.personinstitution_set.filter(relation_type_id__in=classes["akad_funktionen"]["obfrau/obmann"][0]+classes["akad_funktionen"]["mitglied kommission"][0])
        self._members = members
        end = obj.end_date
        if end is None:
            end = datetime.date.today()
        if end is None or obj.start_date is None:
            return [] 
        for year in range(int(obj.start_date.strftime("%Y")), int(end.strftime("%Y"))):
            res[year] = members.filter(start_date__lte=f"{str(year)}-12-31", end_date__gte=f"{str(year)}-01-01").count()
        return res


class KommissionenZeitstrahlNazis(KommissionZeitstrahl):
    mitglieder_nsdap = serializers.SerializerMethodField(method_name="count_nazi_member")

    def count_nazi_member(self, obj):
        res = dict()
        members = self._members.filter(related_person__in=NATIONALSOZIALISTEN)
        end = obj.end_date
        if end is None:
            end = datetime.date.today()
        if end is None or obj.start_date is None:
            return [] 
        for year in range(int(obj.start_date.strftime("%Y")), int(end.strftime("%Y"))):
            count = 0
            mem = members.filter(start_date__lte=f"{str(year)}-12-31", end_date__gte=f"{str(year)}-01-01")
            for m in mem:
                if m.related_person.personinstitution_set.filter(relation_type__in=[3452, 3451], start_date__lte=f"{str(year)}-12-31").count() > 0:
                    count += 1
            res[year] = count
        return res

