def make_trial_xml(
    nct_id="NCT00000001",
    gender="All",
    minimum_age="18 Years",
    maximum_age="65 Years",
    healthy_volunteers="No",
    phase="Phase 2",
    conditions=(),
):
    """Construit un XML minimal, avec la structure réelle de ClinicalTrials.gov.

    Un champ à None est omis, comme dans les fichiers d'origine.
    """
    eligibility_fields = {
        "gender": gender,
        "minimum_age": minimum_age,
        "maximum_age": maximum_age,
        "healthy_volunteers": healthy_volunteers,
    }
    eligibility = "".join(
        f"<{tag}>{value}</{tag}>" for tag, value in eligibility_fields.items() if value is not None
    )
    phase_xml = f"<phase>{phase}</phase>" if phase is not None else ""
    conditions_xml = "".join(f"<condition>{condition}</condition>" for condition in conditions)
    if conditions:  # le vrai XML ajoute des termes MeSH, qui ne sont pas les conditions saisies
        conditions_xml += "<condition_browse><mesh_term>MESH TERM</mesh_term></condition_browse>"
    return (
        "<clinical_study>"
        f"<id_info><nct_id>{nct_id}</nct_id></id_info>"
        f"{phase_xml}{conditions_xml}"
        f"<eligibility><criteria><textblock>Inclusion Criteria: x</textblock></criteria>{eligibility}</eligibility>"
        "</clinical_study>"
    ).encode()
