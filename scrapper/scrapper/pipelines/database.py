import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")


class DatabasePipeline:
    def open_spider(self, spider):
        engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        from scrapper.items import AgenceItem, AvisItem, OffreItem

        session = self.Session()
        try:
            if isinstance(item, AgenceItem):
                self._upsert_agence(session, item)
            elif isinstance(item, OffreItem):
                self._insert_offre(session, item)
            elif isinstance(item, AvisItem):
                self._insert_avis(session, item)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return item

    def _upsert_agence(self, session, item):
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.agence_snapshot import AgenceSnapshot

        agence = session.query(Agence).filter(Agence.nom == item["nom"]).first()
        if agence:
            for field in ["groupe", "adresse", "ville", "region", "code_postal",
                          "site_web", "nb_lots_geres", "nb_collaborateurs", "a_service_travaux"]:
                if item.get(field) is not None:
                    setattr(agence, field, item[field])
            agence.derniere_maj = datetime.utcnow()
        else:
            agence = Agence(
                nom=item["nom"],
                groupe=item.get("groupe"),
                adresse=item.get("adresse"),
                ville=item.get("ville"),
                region=item.get("region"),
                code_postal=item.get("code_postal"),
                site_web=item.get("site_web"),
                nb_lots_geres=item.get("nb_lots_geres"),
                nb_collaborateurs=item.get("nb_collaborateurs"),
                a_service_travaux=item.get("a_service_travaux", False),
                derniere_maj=datetime.utcnow(),
            )
            session.add(agence)
            session.flush()

        if item.get("_create_snapshot"):
            snapshot = AgenceSnapshot(
                agence_id=agence.id,
                nb_lots_geres=agence.nb_lots_geres,
                nb_collaborateurs=agence.nb_collaborateurs,
                a_service_travaux=agence.a_service_travaux,
                note_google=agence.note_google,
                note_trustpilot=agence.note_trustpilot,
            )
            session.add(snapshot)

    def _insert_offre(self, session, item):
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.offre import OffreEmploi

        agence = session.query(Agence).filter(Agence.nom == item["agence_nom"]).first()
        if not agence:
            return

        offre = OffreEmploi(
            agence_id=agence.id,
            titre=item["titre"],
            description=item.get("description"),
            type_poste=item.get("type_poste", "autre"),
            url_source=item.get("url_source"),
            date_publication=item.get("date_publication"),
            active=True,
        )
        session.add(offre)

    def _insert_avis(self, session, item):
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.avis import Avis

        agence = session.query(Agence).filter(Agence.nom == item["agence_nom"]).first()
        if not agence:
            return

        avis = Avis(
            agence_id=agence.id,
            source=item["source"],
            note=item["note"],
            texte=item.get("texte"),
            mentionne_travaux=item.get("mentionne_travaux", False),
            mentionne_reactivite=item.get("mentionne_reactivite", False),
            date_avis=item.get("date_avis"),
        )
        session.add(avis)
