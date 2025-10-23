-- ============================================
-- Alignement Villes -> Pays (clé étrangère ISO 3166-1 alpha-2)
-- ============================================
ALTER TABLE Villes
    ADD CONSTRAINT fk_villes_pays
        FOREIGN KEY (country_3166a2)
        REFERENCES Pays(iso3166a2)
        ON DELETE SET NULL
        ON UPDATE CASCADE;