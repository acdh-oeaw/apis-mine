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
        # for year in range(int(obj.start_date.strftime("%Y")), int(end.strftime("%Y"))):
        #     res[year] = members.filter(start_date__lte=f"{str(year)}-12-31", end_date__gte=f"{str(year)}-01-01").count()
        for mem in members:
            for year in range(int(obj.start_date.strftime("%Y")), int(end.strftime("%Y"))):
                if year not in res.keys():
                    res[year] = 0
                if mem.end_date is None:
                    mem_end = datetime.date.today()
                else:
                    mem_end = mem.end_date
                if year in range(int(mem.start_date.strftime("%Y")), int(mem_end.strftime("%Y"))):
                    res[year] += 1
        res2 = [{"jahr": str(k), "data": {"absolut": v}} for k, v in res.items()]
        return res2


class KommissionenZeitstrahlNazis(KommissionZeitstrahl):
    mitglieder_ns_organisation = serializers.SerializerMethodField(method_name="count_nazi_member")

    def count_nazi_member(self, obj):
        res = []
        members = self._members
        members_dict = dict()
        end = obj.end_date
        if end is None:
            end = datetime.date.today()
        if end is None or obj.start_date is None:
            return [] 
        for year in range(int(obj.start_date.strftime("%Y")), int(end.strftime("%Y"))):
            count = 0
            count_mem = 0
            #mem = members.filter(start_date__lte=f"{str(year)}-12-31", end_date__gte=f"{str(year)}-01-01")
            for m in members:
                if m.end_date is None:
                    mem_end = datetime.date.today()
                else:
                    mem_end = m.end_date
                if year not in range(int(m.start_date.strftime("%Y")), int(mem_end.strftime("%Y"))):
                    continue
                count_mem += 1
                if m.related_person in NATIONALSOZIALISTEN:
                    if m.related_person_id in members_dict.keys():
                        if members_dict[m.related_person_id] <= year:
                            count += 1
                    else:
                        r1 = m.related_person.personinstitution_set.filter(relation_type__in=[3452, 3451], start_date__lte=f"{str(year)}-12-31").order_by("start_date")
                        if r1.count() > 0:
                            count += 1
                print("test")

            res.append({"jahr": str(year), "data": {"absolut": count, "anteil": 0 if count == 0 else count/count_mem}})
        return res
