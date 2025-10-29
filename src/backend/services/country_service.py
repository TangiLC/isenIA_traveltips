from typing import List, Dict, Any, Optional
from connexion.mysql_connect import MySQLConnection
from orm.country_orm import CountryOrm


class CountryService:
    """Service pour la gestion des pays"""

    @staticmethod
    def get_by_alpha2(alpha2: str) -> Dict[str, Any]:
        """Récupère un pays par code ISO alpha-2

        Args:
            alpha2: Code ISO 3166-1 alpha-2

        Returns:
            Données complètes du pays avec relations

        Raises:
            ValueError: Si code invalide ou pays non trouvé
        """
        alpha2 = alpha2.lower().strip()

        if len(alpha2) != 2:
            raise ValueError(
                "Le code pays doit contenir exactement 2 caractères (ISO 3166-1 alpha-2)"
            )

        try:
            MySQLConnection.connect()
            country = CountryOrm.get_by_alpha2(alpha2)

            if country is None:
                raise ValueError(f"Pays '{alpha2}' non trouvé")

            return country
        finally:
            MySQLConnection.close()

    @staticmethod
    def get_by_name(name: str) -> List[Dict[str, Any]]:
        """Recherche des pays par nom

        Args:
            name: Terme de recherche

        Returns:
            Liste des pays

        Raises:
            ValueError: Si nom trop court ou aucun pays trouvé
        """
        if not name or len(name.strip()) < 4:
            raise ValueError("Le nom doit contenir au moins 4 caractères")

        try:
            MySQLConnection.connect()
            countries = CountryOrm.get_by_name(name)

            if not countries:
                raise ValueError(f"Aucun pays trouvé avec le nom '{name}'")

            return countries
        finally:
            MySQLConnection.close()

    @staticmethod
    def get_countries_by_plug_type(plug_type: str) -> List[Dict[str, Any]]:
        """Liste les pays utilisant un type de prise

        Args:
            plug_type: Identifiant du type de prise

        Returns:
            Liste des pays

        Raises:
            ValueError: Si aucun pays trouvé
        """
        try:
            MySQLConnection.connect()
            results = CountryOrm.get_countries_by_plug_type(plug_type.upper())

            if not results:
                raise ValueError(
                    f"Aucun pays trouvé pour le type de prise '{plug_type}'"
                )

            return results
        finally:
            MySQLConnection.close()

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Liste tous les pays avec pagination

        Args:
            skip: Nombre d'éléments à ignorer
            limit: Nombre maximum d'éléments

        Returns:
            Liste des pays
        """
        try:
            MySQLConnection.connect()
            return CountryOrm.get_all(skip, limit)
        finally:
            MySQLConnection.close()

    @staticmethod
    def create(country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau pays avec ses relations

        Args:
            country_data: Données du pays

        Returns:
            Pays créé

        Raises:
            ValueError: Si le pays existe déjà
        """
        iso2 = country_data["iso3166a2"].lower().strip()
        iso3 = country_data["iso3166a3"].upper().strip()

        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = CountryOrm.get_by_alpha2(iso2)
            if existing:
                raise ValueError(f"Un pays avec le code '{iso2}' existe déjà")

            # Insérer le pays
            CountryOrm.upsert_pays(
                iso2=iso2,
                iso3=iso3,
                name_en=country_data["name_en"],
                name_fr=country_data["name_fr"],
                name_local=country_data["name_local"],
                lat=country_data["lat"],
                lng=country_data["lng"],
            )

            # Insérer les relations
            if country_data.get("langues"):
                CountryOrm.insert_langues(iso2, country_data["langues"])

            if country_data.get("currencies"):
                CountryOrm.insert_monnaies(iso2, country_data["currencies"])

            if country_data.get("borders"):
                CountryOrm.insert_borders(iso2, country_data["borders"])

            if country_data.get("electricity_types"):
                CountryOrm.insert_electricite(
                    iso2,
                    country_data["electricity_types"],
                    country_data.get("voltage", ""),
                    country_data.get("frequency", ""),
                )

            MySQLConnection.commit()

            # Récupérer et retourner le pays créé
            return CountryOrm.get_by_alpha2(iso2)
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def update(alpha2: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un pays existant

        Args:
            alpha2: Code ISO alpha-2
            update_data: Données à mettre à jour

        Returns:
            Pays mis à jour

        Raises:
            ValueError: Si code invalide ou pays non trouvé
        """
        iso2 = alpha2.lower().strip()

        if len(iso2) != 2:
            raise ValueError("Le code pays doit contenir exactement 2 caractères")

        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = CountryOrm.get_by_alpha2(iso2)
            if not existing:
                raise ValueError(f"Pays '{iso2}' non trouvé")

            # Mettre à jour les données de base
            base_fields = {
                k: v
                for k, v in update_data.items()
                if k in ["iso3166a3", "name_en", "name_fr", "name_local", "lat", "lng"]
            }

            if base_fields:
                CountryOrm.update_pays(iso2, base_fields)

            # Mettre à jour les relations
            if "langues" in update_data:
                MySQLConnection.execute_update(
                    "DELETE FROM Pays_Langues WHERE country_iso3166a2 = %s", (iso2,)
                )
                if update_data["langues"]:
                    CountryOrm.insert_langues(iso2, update_data["langues"])

            if "currencies" in update_data:
                MySQLConnection.execute_update(
                    "DELETE FROM Pays_Monnaies WHERE country_iso3166a2 = %s", (iso2,)
                )
                if update_data["currencies"]:
                    CountryOrm.insert_monnaies(iso2, update_data["currencies"])

            if "borders" in update_data:
                MySQLConnection.execute_update(
                    "DELETE FROM Pays_Borders WHERE country_iso3166a2 = %s OR border_iso3166a2 = %s",
                    (iso2, iso2),
                )
                if update_data["borders"]:
                    CountryOrm.insert_borders(iso2, update_data["borders"])

            if "electricity_types" in update_data:
                MySQLConnection.execute_update(
                    "DELETE FROM Pays_Electricite WHERE country_iso3166a2 = %s", (iso2,)
                )
                if update_data["electricity_types"]:
                    voltage = update_data.get("voltage", "")
                    frequency = update_data.get("frequency", "")
                    CountryOrm.insert_electricite(
                        iso2, update_data["electricity_types"], voltage, frequency
                    )

            MySQLConnection.commit()

            # Récupérer et retourner le pays mis à jour
            return CountryOrm.get_by_alpha2(iso2)
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def delete(alpha2: str) -> Dict[str, Any]:
        """Supprime un pays et ses relations

        Args:
            alpha2: Code ISO alpha-2

        Returns:
            Informations du pays supprimé

        Raises:
            ValueError: Si code invalide, pays non trouvé ou erreur suppression
        """
        iso2 = alpha2.lower().strip()

        if len(iso2) != 2:
            raise ValueError("Le code pays doit contenir exactement 2 caractères")

        try:
            MySQLConnection.connect()

            # Vérifier existence et récupérer les infos
            existing = CountryOrm.get_by_alpha2(iso2)
            if not existing:
                raise ValueError(f"Pays '{iso2}' non trouvé")

            # Supprimer le pays
            success = CountryOrm.delete_pays(iso2)

            if not success:
                raise ValueError("Erreur lors de la suppression du pays")

            MySQLConnection.commit()

            return existing
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()
