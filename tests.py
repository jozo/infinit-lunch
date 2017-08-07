from restaurants import DonQuijoteRestaurant


class TestDonQuijoteRestaurantTest:
    def setup(self):
        self.rest = DonQuijoteRestaurant()
        self.rest.content = DON_FB_MESSAGE

    def test_can_find_monday_menu(self):
        menu = self.rest.parse_menu(day=0)
        assert menu.foods == ['Letná minestrone',
                              'Medovo-horčicové kuracie prsia so špargľou a hruškami, bylinková ryža',
                              'Penne so špenátom a gorgonzolou']



DON_FB_MESSAGE = """Dobre ranko vsetkym priatelom a znamym prajeme:)

a....nove obedove menu na tento tyzden prinasame...;)

OBEDOVÉ MENU na 7.8.-11.8. (11:00 - 14:00)
Obedové menu s polievkou: 4.90€, bez polievky: 4.40€

Pondelok:
250ml Letná minestrone (9)
300/140g Medovo-horčicové kuracie prsia so špargľou a hruškami, bylinková ryža (7,10)
300g Penne so špenátom a gorgonzolou (1,3,7)

Utorok:
250ml Šošovicovo-paradajková polievka s baby špenátom (7)
300/140g Pečené hovädzie so šalátom, tzatziky, zeleninovým kuskusom a pita chlebom (1,3,7,10)
300g Zemiakový quiche s baklažánom, cuketou, paradajkami, zapečený s camembertom, listový šalát (1,3,7)

Streda:
250ml Cuketový krém s bazalkou (7)
300/100g Špenátové tagliatelle s lososom, smotanou a kôprom (1,3,7)
300g Šampiňónové rizoto s pečenou tekvicou a parmezánom (7)

Štvrtok:
250ml Špenátovo-šampiňónová polievka s tortellini (1,3,7)
300/140g Grilovaná panenka na pomarančoch a badiáne, tlačené zemiačky s cibuľkou (7,9,10)
300g Mrkvovo-cícerové karí s kokosovým mliekom a tofu, basmati ryža (6,7)

Piatok:
250ml Chladený hráškový krém s crème fraîche (7)
300/140g Grilované kuracie prsia s paradajkovou “bruschettou”, parmezánom a sušenou šunkou, risotto bianco (7,12)
300g Gnocchi s bylinkovým maslom, grilovanou zeleninou a balkánskym syrom (1,3,7)

Všetky naše jedlá MÔŽU OBSAHOVAŤ ktorýkoľvek z nižšie uvedených alergénov v stopových množstvách.
1. Obilniny obsahujúce lepok (t.j. pšenica, raž, jačmeň, ovos, špalda, kamut alebo ich hybridné odrody); 2. Kôrovce a výrobky z nich; 3. Vajcia a výrobky z nich; 4. Ryby a výrobky z nich; 5. Arašidy a výrobky z nich; 6. Sójové zrná a výrobky z nich; 7. Mlieko a výrobky z neho; 8. Orechy, ktorými sú mandle, lieskové orechy, vlašské orechy, kešu, pekanové orechy, para orechy, pistácie, makadamové orechy a queenslandské orechy a výrobky z nich; 9. Zeler a výrobky z neho; 10. Horčica a výrobky z nej; 11. Sezamové semená a výrobky z nich; 12. Oxid siričitý a siričitany v koncentráciách vyšších ako 10 mg/kg alebo 10 mg/l; 13. Vlčí bob a výrobky z neho; 14. Mäkkýše a výrobky z nich"""