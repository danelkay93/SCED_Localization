import pytest

from main import (
    get_lang_code_region,
    get_se_agility,
    get_se_combat,
    get_se_cost,
    get_se_faction,
    get_se_intellect,
    get_se_subtype,
    get_se_willpower,
    get_se_xp,
)


@pytest.fixture
def card_data():
    return {
        "subtype_code": "basicweakness",
        "faction_code": "guardian",
        "faction2_code": "seeker",
        "faction3_code": "rogue",
        "cost": 3,
        "xp": 1,
        "skill_willpower": 3,
        "skill_intellect": 2,
        "skill_combat": 4,
        "skill_agility": 1,
    }

class TestCardAttributes:
    def test_get_lang_code_region(self) -> None:
        assert get_lang_code_region("en") == ("en", "")
        assert get_lang_code_region("en_US") == ("en", "US")
        assert get_lang_code_region("zh_CN") == ("zh", "CN")

    def test_get_se_subtype(self, card_data) -> None:
        assert get_se_subtype(card_data) == "BasicWeakness"
        assert get_se_subtype({"subtype_code": None}) == "None"
        assert get_se_subtype({}) == "None"

    def test_get_se_faction(self, card_data) -> None:
        assert get_se_faction(card_data, 0, 0) == "Guardian"
        assert get_se_faction(card_data, 1, 0) == "Seeker"
        assert get_se_faction(card_data, 2, 0) == "Rogue"
        assert get_se_faction({}, 0, 0) == "None"

    def test_get_se_cost(self, card_data) -> None:
        assert get_se_cost(card_data) == "3"
        assert get_se_cost({"cost": "X"}) == "X"
        assert get_se_cost({"cost": None}) == "-"
        assert get_se_cost({}) == "-"

    def test_get_se_xp(self, card_data) -> None:
        assert get_se_xp(card_data) == "1"
        assert get_se_xp({"xp": None}) == "0"
        assert get_se_xp({"real_text": "deck only."}) == "None"
        assert get_se_xp({}) == "0"

    def test_get_se_willpower(self, card_data) -> None:
        assert get_se_willpower(card_data) == "3"
        assert get_se_willpower({"skill_willpower": None}) == "0"
        assert get_se_willpower({}) == "0"

    def test_get_se_intellect(self, card_data) -> None:
        assert get_se_intellect(card_data) == "2"
        assert get_se_intellect({"skill_intellect": None}) == "0"
        assert get_se_intellect({}) == "0"

    def test_get_se_combat(self, card_data) -> None:
        assert get_se_combat(card_data) == "4"
        assert get_se_combat({"skill_combat": None}) == "0"
        assert get_se_combat({}) == "0"

    def test_get_se_agility(self, card_data) -> None:
        assert get_se_agility(card_data) == "1"
        assert get_se_agility({"skill_agility": None}) == "0"
        assert get_se_agility({}) == "0"

# Test for get_lang_code_region function
def test_get_lang_code_region() -> None:
    assert get_lang_code_region("en") == ("en", "")
    assert get_lang_code_region("en_US") == ("en", "US")
    assert get_lang_code_region("zh_CN") == ("zh", "CN")

# Test for get_se_subtype function
def test_get_se_subtype() -> None:
    assert get_se_subtype({"subtype_code": "basicweakness"}) == "BasicWeakness"
    assert get_se_subtype({"subtype_code": "weakness"}) == "Weakness"
    assert get_se_subtype({"subtype_code": None}) == "None"
    assert get_se_subtype({}) == "None"

# Test for get_se_faction function
def test_get_se_faction() -> None:
    card = {
        "faction_code": "guardian",
        "faction2_code": "seeker",
        "faction3_code": "rogue",
    }
    assert get_se_faction(card, 0, 0) == "Guardian"
    assert get_se_faction(card, 1, 0) == "Seeker"
    assert get_se_faction(card, 2, 0) == "Rogue"
    assert get_se_faction({}, 0, 0) == "None"

# Test for get_se_cost function
def test_get_se_cost() -> None:
    assert get_se_cost({"cost": 3}) == "3"
    assert get_se_cost({"cost": "X"}) == "X"
    assert get_se_cost({"cost": None}) == "-"
    assert get_se_cost({}) == "-"

# More tests can be added here

# Test for get_se_xp function
def test_get_se_xp() -> None:
    assert get_se_xp({"xp": 1}) == "1"
    assert get_se_xp({"xp": None}) == "0"
    assert get_se_xp({"real_text": "deck only."}) == "None"
    assert get_se_xp({}) == "0"

# Test for get_se_willpower function
def test_get_se_willpower() -> None:
    assert get_se_willpower({"skill_willpower": 3}) == "3"
    assert get_se_willpower({"skill_willpower": None}) == "0"
    assert get_se_willpower({}) == "0"

# Test for get_se_intellect function
def test_get_se_intellect() -> None:
    assert get_se_intellect({"skill_intellect": 2}) == "2"
    assert get_se_intellect({"skill_intellect": None}) == "0"
    assert get_se_intellect({}) == "0"

# Test for get_se_combat function
def test_get_se_combat() -> None:
    assert get_se_combat({"skill_combat": 4}) == "4"
    assert get_se_combat({"skill_combat": None}) == "0"
    assert get_se_combat({}) == "0"

# Test for get_se_agility function
def test_get_se_agility() -> None:
    assert get_se_agility({"skill_agility": 1}) == "1"
    assert get_se_agility({"skill_agility": None}) == "0"
    assert get_se_agility({}) == "0"


# Additional test cases for other functions in main.py

# Test for get_se_health function
def test_get_se_health() -> None:
    assert get_se_health({"health": 3, "type_code": "enemy"}) == "3"
    assert get_se_health({"health": "X", "type_code": "enemy"}) == "X"
    assert get_se_health({"health": None, "type_code": "enemy"}) == "-"
    assert get_se_health({"type_code": "asset"}) == "None"


# Test for get_se_sanity function
def test_get_se_sanity() -> None:
    assert get_se_sanity({"sanity": 3}) == "3"
    assert get_se_sanity({"sanity": "X"}) == "X"
    assert get_se_sanity({"sanity": None}) == "-"
    assert get_se_sanity({}) == "None"


# Test for get_se_enemy_damage function
def test_get_se_enemy_damage() -> None:
    assert get_se_enemy_damage({"enemy_damage": 2}) == "2"
    assert get_se_enemy_damage({"enemy_damage": None}) == "0"
    assert get_se_enemy_damage({}) == "0"


# Test for get_se_enemy_horror function
def test_get_se_enemy_horror() -> None:
    assert get_se_enemy_horror({"enemy_horror": 1}) == "1"
    assert get_se_enemy_horror({"enemy_horror": None}) == "0"
    assert get_se_enemy_horror({}) == "0"


# Test for get_se_enemy_fight function
def test_get_se_enemy_fight() -> None:
    assert get_se_enemy_fight({"enemy_fight": 4}) == "4"
    assert get_se_enemy_fight({"enemy_fight": "X"}) == "X"
    assert get_se_enemy_fight({"enemy_fight": None}) == "-"
    assert get_se_enemy_fight({}) == "-"


# Test for get_se_enemy_evade function
def test_get_se_enemy_evade() -> None:
    assert get_se_enemy_evade({"enemy_evade": 3}) == "3"
    assert get_se_enemy_evade({"enemy_evade": "X"}) == "X"
    assert get_se_enemy_evade({"enemy_evade": None}) == "-"
    assert get_se_enemy_evade({}) == "-"


# Test for get_se_clue function
def test_get_se_clue() -> None:
    assert get_se_clue({"clues": 2}) == "2"
    assert get_se_clue({"clues": "X"}) == "X"
    assert get_se_clue({"clues": None}) == "-"
    assert get_se_clue({}) == "-"


# Test for get_se_shroud function
def test_get_se_shroud() -> None:
    assert get_se_shroud({"shroud": 4}) == "4"
    assert get_se_shroud({"shroud": "X"}) == "X"
    assert get_se_shroud({"shroud": None}) == "0"
    assert get_se_shroud({}) == "0"


# Test for get_se_per_investigator function
def test_get_se_per_investigator() -> None:
    assert get_se_per_investigator({"type_code": "location", "clues": 1}) == "1"
    assert get_se_per_investigator({"type_code": "location", "clues": 0}) == "0"
    assert get_se_per_investigator({"type_code": "location", "clues": "X"}) == "1"
    assert get_se_per_investigator({"type_code": "location", "clues_fixed": True}) == "0"
    assert get_se_per_investigator({"type_code": "act"}) == "1"
    assert get_se_per_investigator({"type_code": "enemy", "health_per_investigator": True}) == "1"
    assert get_se_per_investigator({"type_code": "enemy"}) == "0"


# Test for get_se_progress_number function
def test_get_se_progress_number() -> None:
    assert get_se_progress_number({"stage": 1}) == "1"
    assert get_se_progress_number({"stage": None}) == "0"
    assert get_se_progress_number({}) == "0"


# Test for get_se_progress_letter function
def test_get_se_progress_letter() -> None:
    assert get_se_progress_letter({"code": "53029"}) == "g"
    assert get_se_progress_letter({"code": "04133a"}) == "e"
    assert get_se_progress_letter({"code": "03278"}) == "c"
    assert get_se_progress_letter({"code": "00000"}) == "a"


# Test for get_se_progress_direction function
def test_get_se_progress_direction() -> None:
    assert get_se_progress_direction({"code": "03278"}) == "Reversed"
    assert get_se_progress_direction({"code": "00000"}) == "Standard"


# Test for get_se_unique function
def test_get_se_unique() -> None:
    assert get_se_unique({"is_unique": True}) == "1"
    assert get_se_unique({"is_unique": False}) == "0"
    assert get_se_unique({"type_code": "investigator"}) == "1"
    assert get_se_unique({}) == "0"


# Test for get_se_name function
def test_get_se_name() -> None:
    assert get_se_name("Card Name") == "Card Name"
    assert get_se_name("") == ""


# Test for get_se_front_name function
def test_get_se_front_name() -> None:
    assert get_se_front_name({"name": "Front Name"}) == "Front Name"
    assert get_se_front_name({}) == ""


# Test for get_se_back_name function
def test_get_se_back_name() -> None:
    assert get_se_back_name({"back_name": "Back Name"}) == "Back Name"
    assert get_se_back_name({"name": "Front Name", "type_code": "scenario"}) == "Front Name"
    assert get_se_back_name({}) == ""


# Test for get_se_subname function
def test_get_se_subname() -> None:
    assert get_se_subname({"subname": "Subname"}) == "Subname"
    assert get_se_subname({}) == ""


# Test for get_se_traits function
def test_get_se_traits() -> None:
    assert get_se_traits({"traits": "Trait1. Trait2."}) == "Trait1. Trait2."
    assert get_se_traits({}) == ""


# Test for get_se_rule function
def test_get_se_rule() -> None:
    assert get_se_rule("Rule text") == "Rule text "
    assert get_se_rule("") == ""


# Test for get_se_front_rule function
def test_get_se_front_rule() -> None:
    assert get_se_front_rule({"text": "Front rule text"}) == "Front rule text "
    assert get_se_front_rule({}) == ""


# Test for get_se_back_rule function
def test_get_se_back_rule() -> None:
    assert get_se_back_rule({"back_text": "Back rule text"}) == "Back rule text "
    assert get_se_back_rule({}) == ""


# Test for get_se_chaos function
def test_get_se_chaos() -> None:
    rule = "[skull]: +1. [cultist]: -2."
    assert get_se_chaos(rule, 0) == ("+1", "None")
    assert get_se_chaos(rule, 1) == ("-2", "Cultist")
    assert get_se_chaos("", 0) == ("", "None")


# Test for get_se_tracker function
def test_get_se_tracker() -> None:
    assert get_se_tracker({"code": "04277"}) == "Current Depth"
    assert get_se_tracker({"code": "00000"}) == ""


# Test for get_se_front_template function
def test_get_se_front_template() -> None:
    assert get_se_front_template({"code": "07062a"}) == "Chaos"
    assert get_se_front_template({}) == "Story"


# Test for get_se_back_template function
def test_get_se_back_template() -> None:
    assert get_se_back_template({"pack_code": "rtnotz"}) == "ChaosFull"
    assert get_se_back_template({}) == "Story"


# Test for get_se_deck_line function
def test_get_se_deck_line() -> None:
    card = {"back_text": "Header: Rule text\nHeader2: Rule text 2"}
    assert get_se_deck_line(card, 0) == ["Header", "Rule text"]
    assert get_se_deck_line(card, 1) == ["Header2", "Rule text 2"]
    assert get_se_deck_line({}, 0) == ["", ""]


# Test for get_se_header function
def test_get_se_header() -> None:
    assert get_se_header("Header text") == "Header text"
    assert get_se_header("") == ""


# Test for get_se_deck_header function
def test_get_se_deck_header() -> None:
    card = {"back_text": "Header: Rule text\nHeader2: Rule text 2"}
    assert get_se_deck_header(card, 0) == "<size 95%>Header<size 105%>"
    assert get_se_deck_header(card, 1) == "<size 95%>Header2<size 105%>"
    assert get_se_deck_header({}, 0) == "<size 95%><size 105%>"


# Test for get_se_deck_rule function
def test_get_se_deck_rule() -> None:
    card = {"back_text": "Header: Rule text\nHeader2: Rule text 2"}
    assert get_se_deck_rule(card, 0) == "Rule text "
    assert get_se_deck_rule(card, 1) == "Rule text 2 "
    assert get_se_deck_rule({}, 0) == ""


# Test for get_se_flavor function
def test_get_se_flavor() -> None:
    assert get_se_flavor("Flavor text") == "Flavor text"
    assert get_se_flavor("") == ""


# Test for get_se_front_flavor function
def test_get_se_front_flavor() -> None:
    assert get_se_front_flavor({"flavor": "Front flavor text"}) == "Front flavor text"
    assert get_se_front_flavor({}) == ""


# Test for get_se_back_flavor function
def test_get_se_back_flavor() -> None:
    assert get_se_back_flavor({"back_flavor": "Back flavor text"}) == "Back flavor text"
    assert get_se_back_flavor({}) == ""


# Test for get_se_back_header function
def test_get_se_back_header() -> None:
    assert get_se_back_header({"back_text": "Header text\nRule text"}) == "Header text "
    assert get_se_back_header({}) == ""


# Test for get_se_paragraph_line function
def test_get_se_paragraph_line() -> None:
    card = {"text": "Header: Rule text\nFlavor text", "flavor": "Flavor text"}
    assert get_se_paragraph_line(card, "Header: Rule text\nFlavor text", "Flavor text", 0) == ("Header", "Flavor text"
                                                                                                         "Rule text")
    assert get_se_paragraph_line({}, "", "", 0) == ("", "", "")


# Test for get_se_location_icon function
def test_get_se_location_icon() -> None:
    assert get_se_location_icon("TILDE") == "Slash"
    assert get_se_location_icon("UNKNOWN") == "None"


# Test for get_se_front_paragraph_line function
def test_get_se_front_paragraph_line() -> None:
    card = {"text": "Header: Rule text\nFlavor text", "flavor": "Flavor text"}
    assert get_se_front_paragraph_line(card, 0) == ("Header", "Flavor text", "Rule text")
    assert get_se_front_paragraph_line({}, 0) == ("", "", "")


# Test for get_se_front_paragraph_header function
def test_get_se_front_paragraph_header() -> None:
    card = {"text": "Header: Rule text\nFlavor text", "flavor": "Flavor text"}
    assert get_se_front_paragraph_header(card, 0) == "Header"
    assert get_se_front_paragraph_header({}, 0) == ""


# Test for get_se_front_paragraph_flavor function
def test_get_se_front_paragraph_flavor() -> None:
    card = {"text": "Header: Rule text\nFlavor text", "flavor": "Flavor text"}
    assert get_se_front_paragraph_flavor(card, 0) == "Flavor text"
    assert get_se_front_paragraph_flavor({}, 0) == ""


# Test for get_se_front_paragraph_rule function
def test_get_se_front_paragraph_rule() -> None:
    card = {"text": "Header: Rule text\nFlavor text", "flavor": "Flavor text"}
    assert get_se_front_paragraph_rule(card, 0) == "Rule text "
    assert get_se_front_paragraph_rule({}, 0) == ""


# Test for get_se_back_paragraph_line function
def test_get_se_back_paragraph_line() -> None:
    card = {"back_text": "Header: Rule text\nFlavor text", "back_flavor": "Flavor text"}
    assert get_se_back_paragraph_line(card, 0) == ("Header", "Flavor text", "Rule text")
    assert get_se_back_paragraph_line({}, 0) == ("", "", "")


# Test for get_se_back_paragraph_header function
def test_get_se_back_paragraph_header() -> None:
    card = {"back_text": "Header: Rule text\nFlavor text", "back_flavor": "Flavor text"}
    assert get_se_back_paragraph_header(card, 0) == "Header"
    assert get_se_back_paragraph_header({}, 0) == ""


# Test for get_se_back_paragraph_flavor function
def test_get_se_back_paragraph_flavor() -> None:
    card = {"back_text": "Header: Rule text\nFlavor text", "back_flavor": "Flavor text"}
    assert get_se_back_paragraph_flavor(card, 0) == "Flavor text"
    assert get_se_back_paragraph_flavor({}, 0) == ""


# Test for get_se_back_paragraph_rule function
def test_get_se_back_paragraph_rule() -> None:
    card = {"back_text": "Header: Rule text\nFlavor text", "back_flavor": "Flavor text"}
    assert get_se_back_paragraph_rule(card, 0) == "Rule text "
    assert get_se_back_paragraph_rule({}, 0) == ""


# Test for get_se_vengeance function
def test_get_se_vengeance() -> None:
    assert get_se_vengeance({"vengeance": 2}) == "Vengeance 2."
    assert get_se_vengeance({"vengeance": None}) == ""
    assert get_se_vengeance({}) == ""


# Test for get_se_victory function
def test_get_se_victory() -> None:
    assert get_se_victory({"victory": 1}) == "Victory 1."
    assert get_se_victory({"victory": None}) == ""
    assert get_se_victory({}) == ""


# Test for get_se_shelter function
def test_get_se_shelter() -> None:
    assert get_se_shelter({"shelter": 3}) == "Shelter 3."
    assert get_se_shelter({"shelter": None}) == ""
    assert get_se_shelter({}) == ""


# Test for get_se_blob function
def test_get_se_blob() -> None:
    assert get_se_blob({"blob": 4}) == "Blob 4."
    assert get_se_blob({"blob": None}) == ""
    assert get_se_blob({}) == ""


# Test for get_se_point function
def test_get_se_point() -> None:
    assert get_se_point({"type_code": "location", "victory": 1, "shelter": 2}) == "Vengeance . Shelter 2. Victory 1."
    assert get_se_point({"type_code": "enemy", "victory": 1, "blob": 3}) == "Victory 1. Vengeance . Blob 3."
    assert get_se_point({}) == ""


# Test for get_se_location_icon function
def test_get_se_location_icon() -> None:
    assert get_se_location_icon("TILDE") == "Slash"
    assert get_se_location_icon("UNKNOWN") == "None"


# Test for get_se_front_location function
def test_get_se_front_location() -> None:
    metadata = {"locationFront": "TILDE"}
    assert get_se_front_location(metadata, 0) == "Slash"
    assert get_se_front_location({}, 0) == "None"
