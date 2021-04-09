from rest_framework import serializers


def get_mitgliedschaft_from_relation(rel, abbreviate=True):
    lbl = rel.label.split(">>")[1].strip()
    if abbreviate:
        res = re.search(r"\((.+)\)", lbl)
        return res.group(1)
    else:
        return lbl



def get_child_classes(objids, obclass, labels=False):
    """used to retrieve a list of primary keys of sub classes"""
    if labels:
        labels_lst = []
    for obj in objids:
        obj = obclass.objects.get(pk=obj)
        p_class = list(obj.vocabsbaseclass_set.all())
        p = p_class.pop() if len(p_class) > 0 else False
        while p:
            if p.pk not in objids:
                if labels:
                    labels_lst.append((p.pk, p.label))
                objids.append(p.pk)
            p_class += list(p.vocabsbaseclass_set.all())
            p = p_class.pop() if len(p_class) > 0 else False
    if labels:
        return (objids, labels_lst)
    else:
        return objids


def get_child_institutions_from_parent(insts):
    res = []
    for i in insts:
        res.extend(
            list(
                InstitutionInstitution.objects.filter(
                    related_institutionA_id=i
                ).values_list("related_institutionB_id", flat=True)
            )
        )
    return res


def abbreviate(value):
    if value.name == "MATHEMATISCH-NATURWISSENSCHAFTLICHE KLASSE":
        return "math.-nat. Klasse"
    elif value.name == "PHILOSOPHISCH-HISTORISCHE KLASSE":
        return "phil.-hist. Klasse"
    else:
        return value


def get_date_range(rel, extended=False, original=False, format="%d.%m.%Y"):
    res = ""
    if extended:
        if rel.start_date_written is not None:
            res += f"von {rel.start_date_written if original else rel.start_date.strftime(format)}"
        if rel.end_date_written is not None:
            res += f" bis {rel.end_date_written if original else rel.end_date.strftime(format)}"
    else:
        if rel.start_date is not None:
            res += f"{rel.start_date.strftime('%Y')}"
        if rel.end_date_written is not None:
            res += f"-{rel.end_date.strftime('%Y')}"

    return res.strip()


berufslaufbahn_ids = get_child_classes([1851, 1385], PersonInstitutionRelation)

subs_akademie = get_child_institutions_from_parent([500, 2, 3])

promotion_inst_ids, promotion_inst_labels = get_child_classes(
    [1386], PersonInstitutionRelation, labels=True
)
daten_mappings = {1369: "Studium", 1371: "Studienaufenthalt", 1386: "Promotion"}

for i in promotion_inst_labels:
    daten_mappings[i[0]] = i[1].replace(">>", "in")


classes = {}
classes["vorschlag"] = get_child_classes(
    [3061, 3141], PersonPersonRelation, labels=True
)



class PersonMinSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(null=True)
    first_name = serializers.CharField(null=True)
    label = serializers.SerializersMethodField(method_name="add_label")

    def add_label(self, object):
        return str(object)

    class Meta:
        fields = ["id", "name", "first_name", "label"]
        model = Person


class WahlSerializer(serializers.Serializer):
    term = serializers.SerializerMethodField(method_name="add_term")
    date = serializers.SerializerMethodField(method_name="add_date")

    def add_term(self, object):
        object.related


class PaasPersonSerializer(serializers.Serializer):
    akademiemitgliedschaft = serializers.SerializerMethodField(
        method_name="add_akademiemitgliedschaft"
    )
    akademiefunktion = serializers.SerializerMethodField(
        method_name="add_akademiefunktion"
    )
    geschlecht = serializers.CharField(source="gender")
    geburtsort = serializers.SerializerMethodField(method_name="add_geburtsort")
    schule = serializers.SerializerMethodField(method_name="add_schule")
    hochschule = serializers.SerializerMethodField(method_name="add_hochschule")
    beruf = serializers.SerializerMethodField(method_name="add_beruf")
    funktionen_akademie_inst = serializers.SerializerMethodField(
        method_name="add_funktionen_akademie_inst"
    )
    austausch = serializers.SerializerMethodField(method_name="add_austausch")
    auszeichnungen = serializers.SerializerMethodField(method_name="add_auszeichnungen")
    wahlvorschlaege = serializers.SerializerMethodField(
        method_name="add_wahlvorschlaege"
    )
    staatl_funktionen = serializers.SerializerMethodField(
        method_name="add_staatliche_funktionen"
    )

    def add_akademiemitgliedschaft(self, object):
