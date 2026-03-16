import scrapy


class AgenceItem(scrapy.Item):
    nom = scrapy.Field()
    groupe = scrapy.Field()
    adresse = scrapy.Field()
    ville = scrapy.Field()
    region = scrapy.Field()
    code_postal = scrapy.Field()
    site_web = scrapy.Field()
    nb_lots_geres = scrapy.Field()
    nb_collaborateurs = scrapy.Field()
    a_service_travaux = scrapy.Field()
    _create_snapshot = scrapy.Field()


class OffreItem(scrapy.Item):
    agence_nom = scrapy.Field()
    titre = scrapy.Field()
    description = scrapy.Field()
    type_poste = scrapy.Field()
    url_source = scrapy.Field()
    date_publication = scrapy.Field()


class AvisItem(scrapy.Item):
    agence_nom = scrapy.Field()
    source = scrapy.Field()
    note = scrapy.Field()
    texte = scrapy.Field()
    date_avis = scrapy.Field()
    mentionne_travaux = scrapy.Field()
    mentionne_reactivite = scrapy.Field()
