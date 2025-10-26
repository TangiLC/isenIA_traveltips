-- ============================================
-- Alignement Villes -> Pays (clé étrangère ISO 3166-1 alpha-2)
-- ============================================
UPDATE Villes 
SET country_3166a2 = NULL 
WHERE country_3166a2 IS NOT NULL 
  AND country_3166a2 NOT IN (SELECT iso3166a2 FROM Pays);

ALTER TABLE Villes
ADD CONSTRAINT fk_villes_pays
    FOREIGN KEY (country_3166a2)
    REFERENCES Pays(iso3166a2)
    ON DELETE SET NULL   
    ON UPDATE CASCADE;    

CREATE INDEX idx_villes_country ON Villes(country_3166a2);