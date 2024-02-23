# TODO:
# "card['pack_code'] not in ['hoth', 'tdor', 'iotv', 'tdg', 'tftbw', 'bob', 'dre', 'lol', 'mtt', 'fof', 'tskp', 'tskc'] and card['code'] not in ['06347', '06348', '06349', '06350', '85037', '85038']"
# 06347 Legs of Atlach-Nacha, SE missing enemy template
# 85037 Subject 8L-08, SE missing enemy template
# WOG, SE missing colored card template
# Return to scenarios, missing swapping encounter set icons data
# Promos, LOL, TSK, MTT, FOF, no translation

import argparse
import copy
import csv
import glob
import importlib
import inspect
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import uuid
import warnings
from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import Any

import dropbox
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from PIL import Image

from card import EnemyCard, Card
from constants import *

from constants import LOCATION_ICON_MAP

DOOM_COMMENT_CARD_CODE = "04212"

SE_FACTION_FIELD = ["faction_code", "faction2_code", "faction3_code"]

SE_FACTION_MAP = {
    "guardian": "Guardian",
    "seeker": "Seeker",
    "rogue": "Rogue",
    "mystic": "Mystic",
    "survivor": "Survivor",
    "neutral": "Neutral",
    # NOTE: This is not a real SE faction type, but ADB use 'mythos' for encounter cards so add it here to avoid errors.
    "mythos": "Mythos",
    None: "None",
}

SE_SUBTYPE_MAP = {
    "weakness": "Weakness",
    "basicweakness": "BasicWeakness",
    None: "None",
}


def generate_property_count_tuple(count):
    return lambda m, m_args: m(m_args[0], m_args[1], *m_args), "{}".format, count


# Suppress BeautifulSoup useless warnings.
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

parser = argparse.ArgumentParser()
for arg, options in SCRIPT_ARGS.items():
    parser.add_argument(f"--{arg}", **options)
args = parser.parse_args()


def get_lang_code_region():
    parts = args.lang.split("_")
    return parts[0], parts[1] if len(parts) > 1 else ""

from pathlib import Path
import sys
import importlib
from typing import Optional

def import_lang_module() -> Optional[importlib.ModuleType]:
    """Import language dependent functions."""
    lang_code, region = get_lang_code_region()
    lang_folder = Path('translations') / lang_code
    if str(lang_folder) not in sys.path:
        sys.path.insert(1, str(lang_folder))
    module_name = "transform"
    if region:
        module_name += f"_{region}"
    return importlib.import_module(module_name)


def transform_lang(value):
    # NOTE: Get the corresponding process function from stack frame. Therefore it's important to call this function from the correct 'get_se_xxx' function.
    module = import_lang_module()
    attr = inspect.stack()[1].function.replace("get_se_", "")
    func_name = f"transform_{attr}"
    func = getattr(module, func_name, None)
    return func(value) if func else value


# NOTE: ADB data may contain explicit null fields, that should be treated the same as missing.
def card.get(key, default):
    return default if card.get(key) is None else card.get(key)


def get_se_subtype(card):
    subtype = card.get("subtype_code")
    return SE_SUBTYPE_MAP[subtype]


def get_se_faction(card, index, sheet):
    if index == 0 and (subtype := get_se_subtype(card)) != "None":
        return subtype

    faction = SE_FACTION_MAP.get(card.get(SE_FACTION_FIELD[index]))

    if card["code"].endswith(("-p", "-pf" if sheet == 0 else "-pb")):
        faction = f"Parallel{faction}"

    return faction

def get_se_cost(card):
    cost = card.get("cost", "-")
        if cost == ADB_VAR_HEALTH:
        cost = "X"
    return str(cost)


def get_se_xp(card):
    rule = card.get("real_text", "")
    # NOTE: Signature cards don't have xp indicator on cards.
    if "deck only." in rule:
        return "None"
    return str(card.get("xp", 0))


def get_se_willpower(card):
    return str(card.get("skill_willpower", 0))


def get_se_intellect(card):
    return str(card.get("skill_intellect", 0))


def get_se_combat(card):
    return str(card.get("skill_combat", 0))


def get_se_agility(card):
    return str(card.get("skill_agility", 0))


def get_se_skill(card, index):
    skill_list = [
        skill.capitalize() for skill in SKILL_NAMES for _ in range(card.get(f"skill_{skill}", 0))
    ]
    # Add 'None' to fill the list to 6 elements.
    skill_list += ["None"] * (6 - len(skill_list))
    return skill_list[index]


def get_se_slot(card, index):
    slots = card.get("real_slot", "").split(".")
    sep_slots = [SLOT_MAP[slot.strip()] for slot in slots if SLOT_MAP.get(slot.strip())]
    # NOTE: Slot order in ADB and SE are reversed.
    sep_slots.reverse()
    # Add 'None' to fill the list to 2 elements.
    sep_slots += ["None"] * (2 - len(sep_slots))
    return sep_slots[index]


def get_se_health(card):
    is_enemy = card["type_code"] == "enemy"
    health = card.get("health", "-") if is_enemy or card.get("sanity") is not None else "None"
    health = "X" if health == ADB_VAR_HEALTH and is_enemy else ADB_STAR_HEALTH if health == ADB_VAR_HEALTH else health
    return str(health)


def get_se_sanity(card):
    sanity = card.get("sanity", "-" if card.get("health") is not None else "None")
    sanity = ADB_STAR_HEALTH if sanity == ADB_VAR_HEALTH else sanity
    return str(sanity)


def get_se_enemy_damage(card):
    return str(card.get("enemy_damage", 0))


def get_se_enemy_horror(card):
    return str(card.get("enemy_horror", 0))


def get_se_enemy_fight(card):
    fight = card.get("enemy_fight", "-")
    # NOTE: ADB uses ADB_VAR_HEALTH to indicate variable fight.
    if fight == ADB_VAR_HEALTH:
        fight = ADB_X_VALUE
    return str(fight)


def get_se_enemy_evade(card):
    evade = card.get("enemy_evade", "-")
    # NOTE: ADB uses ADB_VAR_HEALTH to indicate variable evade.
    if evade == ADB_VAR_HEALTH:
        evade = ADB_X_VALUE
    return str(evade)


def check_se_agenda_image_front(card: dict[str, Any]) -> bool:
    return card["code"] in SE_AGENDA_FRONT_CODES


def is_se_agenda_image_back(card):
    return card["code"] in SE_AGENDA_BACK_CODES


def is_se_act_image_front(card):
    return card["code"] in SE_ACT_FRONT_CODES


def is_se_act_image_back(card):
    return card["code"] in SE_ACT_BACK_CODES


def is_se_bottom_line_transparent(card, sheet) -> bool:
    return card["type_code"] == "enemy" or (sheet == 0 and (check_se_agenda_image_front(card) or is_se_act_image_front(card))) or (sheet == 1 and (is_se_agenda_image_back(card) or is_se_act_image_back(card)))


def get_se_property(card, sheet, property_func):
    if is_se_bottom_line_transparent(card, sheet):
        return ""
    return property_func(card)

get_se_illustrator = lambda card, sheet: get_se_property(card, sheet, lambda card: card.get("illustrator", ""))
get_se_copyright = lambda card, sheet: get_se_property(card, sheet, lambda card: f'<cop> {PACK_YEAR_MAP.get(card.get("pack_code"), "")} FFG')
get_se_pack = lambda card, sheet: get_se_property(card, sheet, lambda card: PACK_CODES_TO_NAMES[card["pack_code"]])
get_se_pack_number = lambda card, sheet: get_se_property(card, sheet, lambda card: str(card.get("position", 0)))

def get_se_encounter_total(card, sheet):
    if is_se_bottom_line_transparent(card, sheet):
        return ""
    return str(ENCOUNTER_SET_TO_CARD_COUNT[card.get("encounter_code")])

def get_se_encounter_number(card, sheet):
    if is_se_bottom_line_transparent(card, sheet):
        return ""
    return str(card.get("encounter_position", 0))

def get_se_encounter(card, sheet):
    if card.get("encounter_code") in ["vortex", "flood"] and card["code"] in SPECIAL_ENCOUNTER_CARDS:
        encounter = "black_stars_rise"
    return ENCOUNTER_SETS_TO_NAMES[encounter]





def get_se_encounter_front_visibility(card) -> str:
    return "0" if card["code"] in ["06015a", "06015b"] else "1"


def get_se_encounter_back_visibility(card) -> str:
    return "0" if card["code"] in SE_ENCOUNTER_BACK_VISIBILITY_CODES else "1"


def get_se_doom(card):
    doom = card.get("doom", "-")
    # NOTE: ADB uses ADB_VAR_HEALTH to indicate variable doom.
    if doom == ADB_VAR_HEALTH:
        doom = "Star"
    return str(doom)


def get_se_doom_comment(card) -> str:
    # NOTE: Special cases the cards with an asterisk comment on the doom or clue.
    return "1" if card["code"] in [DOOM_COMMENT_CARD_CODE] else "0"


def get_se_clue(card):
    clue = card.get("clues", "-")
    # NOTE: ADB uses ADB_VAR_HEALTH to indicate variable clue.
    if clue == ADB_VAR_HEALTH:
        clue = "Star"
    return str(clue)


def get_se_shroud(card):
    shroud = card.get("shroud", 0)
    # NOTE: ADB uses ADB_VAR_HEALTH to indicate variable shroud.
    if shroud == ADB_VAR_HEALTH:
        shroud = "X"
    return str(shroud)


def get_se_per_investigator(card) -> str:
    # NOTE: Location and act cards default to use per-investigator clue count, unless clue count is 0, variable (-2) or 'clues_fixed' is specified.
    if card["type_code"] in ["location", "act"]:
        return (
            "0" if card.get("clues", 0) in [0, -2] or card.get("clues_fixed", False) else "1"
        )
    return "1" if card.get("health_per_investigator", False) else "0"


def get_se_progress_number(card):
    return str(card.get("stage", 0))


def get_se_progress_letter(card) -> str:
    # NOTE: Special case agenda and act letters.
    if card["code"] in [
        "53029",
        "53030",
        "53031",
        "53032",
        "53033",
        "53034",
        "53035",
        "53036",
    ]:
        return "g"
    if card["code"] in [
        "04133a",
        "04134a",
        "04135",
        "04136",
        "04137a",
        "04138",
        "04139",
        "04140",
    ]:
        return "e"
    if card["code"] in [
        "03278",
        "03279a",
        "03279b",
        "03280",
        "03282",
        "04125a",
        "04126a",
        "04127",
        "04128a",
        "04129",
        "04130a",
        "04131",
        "04132",
    ]:
        return "c"
    return "a"


def is_se_progress_reversed(card):
    return card["code"] in ["03278", "03279a", "03279b", "03280", "03281"]


def get_se_progress_direction(card) -> str:
    # NOTE: Special case agenda and act direction.
    if is_se_progress_reversed(card):
        return "Reversed"
    return "Standard"


def get_se_unique(card) -> str:
    # NOTE: ADB doesn't specify 'is_unique' property for investigator cards but they are always unique.
    return "1" if card.get("is_unique", False) or card["type_code"] == "investigator" else "0"


def get_se_name(name):
    return transform_lang(name)


def get_se_front_name(card):
    name = card.get("name", "")
    return get_se_name(name)


def get_se_back_name(card):
    # NOTE: ADB doesn't have back names for scenario and investigator cards but SE have them. We need to use the front names instead to avoid getting blank on the back.
    if card["type_code"] in ["scenario", "investigator"]:
        name = card.get("name", "")
    elif card["type_code"] in ["story"]:
        # NOTE: Default back name as the same as front name for story cards for certain cards whose back name is missing.
        name = card.get("name", "")
        name = card.get("back_name", name)
    else:
        name = card.get("back_name", "")
    return get_se_name(name)


def get_se_subname(card):
    subname = card.get("subname", "")
    return get_se_name(subname)


def get_se_traits(card):
    traits = card.get("traits", "")
    traits = [f"{trait.strip()}." for trait in traits.split(".") if trait.strip()]
    traits = " ".join(traits)
    return transform_lang(traits)


def get_se_markup(rule):
    markup = [
        (r"\[action\]", "<act>"),
        (r"\[reaction\]", "<rea>"),
        (r"\[free\]", "<fre>"),
        (r"\[fast\]", "<fre>"),
        (r"\[willpower\]", "<wil>"),
        (r"\[intellect\]", "<int>"),
        (r"\[combat\]", "<com>"),
        (r"\[agility\]", "<agi>"),
        (r"\[wild\]", "<wild>"),
        (r"\[guardian\]", "<gua>"),
        (r"\[seeker\]", "<see>"),
        (r"\[rogue\]", "<rog>"),
        (r"\[mystic\]", "<mys>"),
        (r"\[survivor\]", "<sur>"),
        (r"\[skull\]", "<sku>"),
        (r"\[cultist\]", "<cul>"),
        (r"\[tablet\]", "<tab>"),
        (r"\[elder_thing\]", "<mon>"),
        (r"\[elder_sign\]", "<eld>"),
        (r"\[auto_fail\]", "<ten>"),
        (r"\[bless\]", "<ble>"),
        (r"\[curse\]", "<cur>"),
        (r"\[per_investigator\]", "<per>"),
        (r"\[frost\]", "<fro>"),
        (r"\[seal_a\]", "<seal1>"),
        (r"\[seal_b\]", "<seal2>"),
        (r"\[seal_c\]", "<seal3>"),
        (r"\[seal_d\]", "<seal4>"),
        (r"\[seal_e\]", "<seal5>"),
    ]
    for a, b in markup:
        rule = re.sub(a, b, rule, flags=re.I)
    # NOTE: Format traits. We avoid the buggy behavior of </size> in SE instead we set font size by relative percentage, 0.9 * 0.33 * 3.37 = 1.00089.
    return re.sub(r"\[\[([^\]]*)\]\]", r"<size 90%><t>\1</t><size 33%> <size 337%>", rule)


def get_se_rule(rule):
    rule = get_se_markup(rule)
    # NOTE: Get rid of the errata text, e.g. Wendy's Amulet.
    rule = re.sub(r"<i>\(Errat(um|a)[^<]*</i>", "", rule)
    # NOTE: Get rid of the FAQ text, e.g. Rex Murphy.
    rule = re.sub(r"<i>\(FAQ[^<]*</i>", "", rule)
    # NOTE: Format bold action keywords.
    rule = re.sub(r"<b>([^<]*)</b>", r"<size 95%><hdr>\1</hdr><size 105%>", rule)
    # NOTE: Convert <p> tag to newline characters.
    rule = rule.replace("</p><p>", "\n").replace("<p>", "").replace("</p>", "")
    # NOTE: Format bullet icon at the start of the line.
    rule = "\n".join([re.sub(r"^[\-—] ", "<bul> ", line.strip()) for line in rule.split("\n")])
    # NOTE: We intentionally add a space at the end to hack around a problem with SE scenario card layout. If we don't add this space,
    # the text on scenario cards doesn't automatically break lines.
    rule = f"{rule} " if rule.strip() else ""
    return transform_lang(rule)


def get_se_front_rule(card):
    rule = card.get("text", "")
    return get_se_rule(rule)


def get_se_back_rule(card):
    rule = card.get("back_text", "")
    return get_se_rule(rule)


def get_se_chaos(rule, index):
    rule = [line.strip() for line in rule.split("\n")]
    rule = rule[1:]
    tokens = ["[skull]", "[cultist]", "[tablet]", "[elder_thing]"]
    merge_tokens = ["Skull", "Cultist", "Tablet", "ElderThing"]
    token = tokens[index]
    for line in rule:
        if token in line:
            # NOTE: Find the greatest token this token is combined with.
            max_index = index
            for merge_token in tokens:
                if merge_token in line:
                    merge_index = tokens.index(merge_token)
                    max_index = max(max_index, merge_index)

            # NOTE: Remove tokens from the beginning of the line.
            line = re.sub(r"[:：]", "", line)
            for merge_token in tokens:
                line = line.replace(merge_token, "")
            line = line.strip()

            merge = merge_tokens[max_index] if max_index > index else "None"
            return line, merge
    return "", "None"


def get_se_front_chaos(card, index):
    return get_chaos(card, "text", index)


def get_se_back_chaos(card, index):
    return get_chaos(card, "back_text", index)


def get_se_front_chaos_rule(card, index):
    rule, _ = get_se_front_chaos(card, index)
    return get_se_rule(rule)


def get_se_front_chaos_merge(card, index):
    _, merge = get_se_front_chaos(card, index)
    return merge


def get_se_back_chaos_rule(card, index):
    rule, _ = get_se_back_chaos(card, index)
    return get_se_rule(rule)


def get_se_back_chaos_merge(card, index):
    _, merge = get_se_back_chaos(card, index)
    return merge


def get_se_tracker(card):
    tracker = ""
    if card["code"] == "04277":
        tracker = "Current Depth"
    elif card["code"] == "07274":
        tracker = "Spent Keys"
    elif card["code"] in ["83001", "83016"]:
        tracker = "Strength of the Abyss"
    return transform_lang(tracker)


def is_return_to_scenario(card):
    return (
        card["pack_code"] in ["rtnotz", "rtdwl", "rtptc", "rttfa", "rttcu"]
        and card["type_code"] == "scenario"
    )


def get_se_front_template(card) -> str:
    # NOTE: Use scenario template of story card for return to scenarios. Also for some special cards.
    if is_return_to_scenario(card) or card["code"] in ["07062a"]:
        return "Chaos"
    return "Story"


def get_se_back_template(card) -> str:
    # NOTE: Use scenario template of story card for return to scenarios.
    if is_return_to_scenario(card):
        return "ChaosFull"
    return "Story"


def get_se_deck_line(card, index):
    lines = card.get("back_text", "")
    lines = [line.strip() for line in lines.split("\n") if line.strip()]
    line = lines[index] if index < len(lines) else ""
    line = [part.strip() for part in line.replace("：", ":").split(":")]
    if len(line) < 2:
        line.append("")
    elif len(line) > 2:
        line = [line[0], ":".join(line[1:])]
    return line


def get_se_header(header):
    # NOTE: Some header text at the back of agenda/act may have markup text in it.
    header = get_se_markup(header)
    return transform_lang(header)


def get_se_deck_header(card, index):
    header, _ = get_se_deck_line(card, index)
    header = f"<size 95%>{header}<size 105%>"
    return get_se_header(header)


def get_se_deck_rule(card, index):
    _, rule = get_se_deck_line(card, index)
    return get_se_rule(rule)


def get_se_flavor(flavor):
    # NOTE: Some flavor text may contain markup.
    flavor = get_se_markup(flavor)
    return transform_lang(flavor)


def get_se_front_flavor(card):
    flavor = card.get("flavor", "")
    return get_se_flavor(flavor)


def get_se_back_flavor(card):
    flavor = card.get("back_flavor", "")
    return get_se_flavor(flavor)


def get_se_back_header(card):
    # NOTE: Back header is used by scenario card with a non-standard header. We intentionally add a space at the end to work around a formatting issue in SE.
    # If we don't add the extra space, SE doesn't perform line breaking.
    header = card.get("back_text", "")
    header = next(line.strip() for line in header.split("\n")) + " "
    return get_se_header(header)


def get_se_paragraph_line(card, text, flavor, index):
    # NOTE: Header is determined by 'b' tag ending with colon or followed by a newline (except for resolution text).
    def is_header(elem) -> bool:
        if elem.name == "b":
            elem_text = elem.get_text().strip()
            if elem_text and elem_text[-1] in (":", "："):
                return True
            if elem_text.startswith("(→"):
                return False
            next_elem = elem.next_sibling
            if next_elem and next_elem.get_text().startswith("\n"):
                return True
        return False

    # NOTE: Flavor is determined by 'blockquote' or 'i' tag.
    def is_flavor(elem):
        return elem.name in ["blockquote", "i"]

    # NOTE: If there's explicit flavor text, add it before the main text to handle them together. Merge it with existing flavor text if possible.
    if flavor:
        soup = BeautifulSoup(text, HTML_PARSER)
        if len(soup.contents):
            flavor_elem = soup.contents[0]
            if is_flavor(flavor_elem):
                flavor_elem.insert(0, f"{flavor}\n")
            else:
                flavor_elem.insert_before(f"<blockquote><i>{flavor}</i></blockquote>\n")
            text = str(soup)
        else:
            text = f"<blockquote><i>{flavor}</i></blockquote>"

    # NOTE: Normalize <hr> tag.
    text = text.replace("<hr/>", "<hr>")

    # NOTE: Swap <hr> and <b> tag in case ADB has <hr> at the beginning of the header text.
    text = re.sub(r"<b>\s*<hr>", "<hr><b>", text)

    # NOTE: Use <hr> to explicitly determine paragraphs.
    paragraphs = [paragraph.strip() for paragraph in text.split("<hr>")]

    # NOTE: Split paragraphs further before each header.
    new_paragraphs = []
    for paragraph in paragraphs:
        soup = BeautifulSoup(paragraph, "html.parser")

        splits = [0]
        for i, elem in enumerate(soup.contents):
            if is_header(elem):
                splits.append(i)
        splits.append(None)

        for i in range(len(splits) - 1):
            new_paragraph = "".join(
                str(elem) for elem in soup.contents[splits[i] : splits[i + 1]]
            ).strip()
            if new_paragraph:
                new_paragraphs.append(new_paragraph)
    paragraphs = new_paragraphs

    # NOTE: Extract out the header and flavor text from each paragraph.
    parsed_paragraphs = []
    for paragraph in paragraphs:
        soup = BeautifulSoup(paragraph, "html.parser")

        # NOTE: Remove leading whitespace before checking for header or flavor.
        def strip_leading(node) -> None:
            for child in node.contents:
                if not str(child).strip():
                    child.extract()
                else:
                    break

        strip_leading(soup)

        # NOTE: Extract out the header text from the beginning.
        header = ""
        header_elem = soup.contents[0]
        if is_header(header_elem):
            header = str(header_elem).replace("<b>", "").replace("</b>", "").strip()
            header_elem.extract()

        strip_leading(soup)

        # NOTE: Extract out the flavor text from the beginning.
        flavor = ""
        flavor_elem = soup.contents[0]
        if is_flavor(flavor_elem):
            flavor = (
                str(flavor_elem)
                .replace("<blockquote>", "")
                .replace("</blockquote>", "")
                .replace("<i>", "")
                .replace("</i>", "")
                .strip()
            )
            flavor_elem.extract()

        rule = str(soup).strip()
        parsed_paragraphs.append((header, flavor, rule))

    if index < len(parsed_paragraphs):
        return parsed_paragraphs[index]
    return "", "", ""

def get_paragraph_line(card, text_key, flavor_key, index):
    text = card.get(text_key, "")
    flavor = card.get(flavor_key, "")
    header, flavor, rule = get_se_paragraph_line(card, text, flavor, index)
    return get_se_header(header), get_se_flavor(flavor), get_se_rule(rule)

def get_location_icon(metadata, location_key, index):
    icons = metadata.get(location_key, {}).get("connections", "")
    return get_se_connection(icons, index)

def get_chaos(card, text_key, index):
    rule = card.get(text_key, "")
    rule, merge = get_se_chaos(rule, index)
    return get_se_rule(rule), merge

def get_se_front_paragraph_line(card, index):
    return get_paragraph_line(card, "text", "flavor", index)



def get_se_front_paragraph_header(card, index):
    header, _, _ = get_se_front_paragraph_line(card, index)
    return get_se_header(header)


def get_se_front_paragraph_flavor(card, index):
    _, flavor, _ = get_se_front_paragraph_line(card, index)
    return get_se_flavor(flavor)


def get_se_front_paragraph_rule(card, index):
    _, _, rule = get_se_front_paragraph_line(card, index)
    return get_se_rule(rule)


def get_se_back_paragraph_line(card, index):
    return get_paragraph_line(card, "back_text", "back_flavor", index)


def get_se_back_paragraph_header(card, index):
    header, _, _ = get_se_back_paragraph_line(card, index)
    return get_se_header(header)


def get_se_back_paragraph_flavor(card, index):
    _, flavor, _ = get_se_back_paragraph_line(card, index)
    return get_se_flavor(flavor)


def get_se_back_paragraph_rule(card, index):
    _, _, rule = get_se_back_paragraph_line(card, index)
    return get_se_rule(rule)


def get_se_vengeance(card):
    vengeance = card.get("vengeance")
    vengeance = f"Vengeance {vengeance}." if isinstance(vengeance, int) else ""
    return transform_lang(vengeance)


def get_se_victory(card):
    victory = card.get("victory")
    victory = f"Victory {victory}." if isinstance(victory, int) else ""
    return transform_lang(victory)


def get_se_shelter(card):
    shelter = card.get("shelter")
    shelter = f"Shelter {shelter}." if isinstance(shelter, int) else ""
    return transform_lang(shelter)


def get_se_blob(card):
    blob = card.get("blob")
    blob = f"Blob {blob}." if isinstance(blob, int) else ""
    return transform_lang(blob)


def get_se_point(card):
    vengeance = get_se_vengeance(card)
    victory = get_se_victory(card)
    # NOTE: Special points have different formatting on location and enemy cards.
    if card["type_code"] == "location":
        shelter = get_se_shelter(card)
        point = "\n".join([point for point in [vengeance, shelter, victory] if point])
    else:
        blob = get_se_blob(card)
        point = "\n".join([point for point in [victory, vengeance, blob] if point])
    return point


def get_se_location_icon(icon):
    # NOTE: SCED metadata on location may include special location types for game logic, they are not printed on cards.
    return LOCATION_ICON_MAP.get(icon, "None")


def get_se_front_location(metadata, index):
    return get_location_icon(metadata, "locationFront", index)


def get_se_back_location(metadata, index):
    return get_location_icon(metadata, "locationBack", index)



def get_se_connection(icons, index):
    icons = [get_se_location_icon(icon) for icon in icons.split("|")]
    while len(icons) < 6:
        icons.append("None")
    return icons[index]


def get_se_front_connection(metadata, index):
    icons = metadata.get("locationFront", {}).get("connections", "")
    return get_se_connection(icons, index)


def get_se_back_connection(metadata, index):
    icons = metadata.get("locationBack", {}).get("connections", "")
    return get_se_connection(icons, index)


def apply_partials_with_args(functions, *args):
    return {partial(func, *args): keys for func, keys in functions.items()}


def get_static_assignments(image_move_x, image_move_y, image_scale):
    return {
        image_move_x: ("port0X", "port1X"),
        image_move_y: ("port0Y", "port1Y"),
        image_scale: ("port0Scale", "port1Scale"),
        "0": ("$PortraitShare", "port0Rot", "$port1Rot"),
    }


def get_dynamic_assignments(card, metadata, image_sheet):
    dynamic_functions = {
        partial(func, card, image_sheet): keys
        for func, keys in {
            (get_se_front_name, card): ("name",),
            (get_se_subname, card): ("$Subtitle",),
            (get_se_back_name, card): ("$TitleBack",),
            (get_se_subtype, card): ("$Subtype",),
            (get_se_unique, card): ("$Unique",),
            (get_se_cost, card): ("$ResourceCost",),
            (get_se_xp, card): ("$Level",),
            (get_se_willpower, card): ("$Willpower",),
            (get_se_intellect, card): ("$Intellect",),
            (get_se_combat, card): ("$Combat",),
            (get_se_agility, card): ("$Agility",),
            (get_se_health, card): ("$Stamina", "$Sanity", "$Health"),
            (get_se_enemy_damage, card): ("$Damage",),
            (get_se_enemy_horror, card): ("$Horror",),
            (get_se_enemy_fight, card): ("$Attack",),
            (get_se_enemy_evade, card): ("$Evade",),
            (get_se_traits, card): ("$Traits",),
            (get_se_front_rule, card): ("$Rules",),
            (get_se_front_flavor, card): ("$Flavor",),
            (get_se_back_flavor, card): ("$FlavorBack", "$InvStoryBack"),
            (get_se_illustrator, card, image_sheet): ("$Artist", "$ArtistBack"),
            (get_se_copyright, card, image_sheet): ("$Copyright",),
            (get_se_pack, card, image_sheet): ("$Collection",),
            (get_se_pack_number, card, image_sheet): ("$CollectionNumber",),
            (get_se_encounter, card, image_sheet): ("$Encounter",),
            (get_se_encounter_number, card, image_sheet): ("$EncounterNumber",),
            (get_se_encounter_total, card, image_sheet): ("$EncounterTotal",),
            (get_se_encounter_front_visibility, card): ("$ShowEncounterIcon",),
            (get_se_encounter_back_visibility, card): ("$ShowEncounterIconBack",),
            (get_se_doom, card): ("$Doom",),
            (get_se_doom_comment, card): ("$Asterisk",),
            (get_se_clue, card): ("$Clues",),
            (get_se_shroud, card): ("$Shroud",),
            (get_se_per_investigator, card): ("$PerInvestigator",),
            (get_se_progress_number, card): ("$ProgressNumber",),
            (get_se_progress_letter, card): ("$ProgressLetter",),
            (is_se_progress_reversed, card): ("$ProgressReversed",),
            (get_se_progress_direction, card): ("$ProgressDirection",),
            (get_se_tracker, card): ("$Tracker",),
            (get_se_front_template, card): ("$Template",),
            (get_se_back_template, card): ("$TemplateBack",),
            (get_se_back_header, card): ("$HeaderBack",),
            (get_se_point, card): ("$Victory",),
            (get_se_front_location, metadata): ("$LocationFront",),
            (get_se_back_location, metadata): ("$LocationBack",),
        }.items()
    }
    return dynamic_functions


def get_final_card(assignments):
    final_card = {
        key: value for value, keys in assignments[AssignmentType.STATIC].items() for key in keys
    }
    final_card.update(
        {key: method() for method, key in assignments[AssignmentType.DYNAMIC].items()}
    )
    return final_card


def set_property_assignments(final_card, property_var_by_key) -> None:
    for property_key, property_count in SE_PROPERTY_COUNTS.items():
        val = generate_property_count_tuple(property_count)
        property_method, property_name_pattern, property_count = val
        property_args = property_var_by_key[property_key]
        for i in range(property_count):
            m_arg, add_args = (
                property_args if isinstance(property_args, tuple) else (property_args, ())
            )
            final_card[f"${property_name_pattern(i + 1)}"] = property_method(m_arg, *add_args)


def get_se_card(result_id, card, metadata, image_filename, image_scale, image_move_x, image_move_y):
    image_sheet = decode_result_id(result_id)[-1]
    property_var_by_key = {prop: (card, image_sheet) if prop == SEProperties.FACTION else card for prop in SEProperties}

    assignments = {
        AssignmentType.STATIC: get_static_assignments(image_move_x, image_move_y, image_scale),
        AssignmentType.DYNAMIC: get_dynamic_assignments(card, metadata, image_sheet),
    }

    final_card = get_final_card(assignments)
    set_property_assignments(final_card, property_var_by_key)

    return final_card


from pathlib import Path


def download_repo(repo_folder: Path, repo: str) -> Path:
    if Path(repo_folder).is_dir():
        return repo_folder
    print(f"Cloning {repo}...")
    Path(args.repo_dir).mkdir(parents=True, exist_ok=True)
    repo_name = repo.split("/")[-1]
    repo_folder = args.repo_dir / repo_name
    subprocess.run(["git", "clone", "--quiet", f"https://github.com/{repo}.git", repo_folder])
    return repo_folder


ahdb = {}


def update_encounter_code(translation) -> None:
    for card in translation.values():
        if "linked_card" in card:
            linked_card = card["linked_card"]
            card_encounter = card.get("encounter_code")
            linked_encounter = linked_card.get("encounter_code")

            if card_encounter and not linked_encounter:
                linked_card["encounter_code"] = card_encounter
            elif not card_encounter and linked_encounter:
                card["encounter_code"] = linked_encounter


def download_card(ahdb_id):
    def copy_card_properties(old_card, card, properties):
        temp_card = copy.deepcopy(card)
        temp_card["code"] = f'{old_card["code"]}-pb'
        for prop in properties:
            temp_card[prop] = old_card.get(prop, 0)
        return temp_card

    ahdb_folder = Path(args.cache_dir) / "ahdb"
    Path(ahdb_folder).mkdir(parents=True, exist_ok=True)
    lang_code, _ = get_lang_code_region()
    filename = f"{ahdb_folder}/{lang_code}.json"

    if not Path(filename).is_file():
        print("Downloading ArkhamDB data...")

        def load_folder(folder):
            all_cards = {}
            for data_filename in glob.glob(f"{folder}/**/*.json"):
                with open(data_filename, encoding="utf-8") as file:
                    folder_cards = json.loads(file.read())
                    if not hasattr(folder_cards, "__iter__"):
                        print(f"Error: {data_filename} contains non-iterable.")
                        continue
                    for folder_card in folder_cards:
                        if not hasattr(folder_card, "keys"):
                            print(f"Error: {data_filename} contains non-object.")
                            continue
                        if "code" in folder_card:
                            all_cards[folder_card["code"]] = folder_card
                        else:
                            print(
                                f"Warning: {data_filename} contains {folder_card=} without 'code' property."
                            )
            return all_cards

        repo_folder = download_repo(args.ahdb_dir, "Kamalisk/arkhamdb-json-data")
        english = load_folder(f"{repo_folder}/pack")
        translation = load_folder(f"{repo_folder}/translations/{lang_code}/pack")

        # NOTE: Patch translation data while maintain the original properties as 'real_*' to match the API result.
        for ecid, english_card in english.items():
            if ecid in translation:
                translation_card = translation[ecid]
                for key, value in translation_card.items():
                    if key in english_card and key != "code":
                        english_card[f"real_{key}"] = english_card[key]
                    english_card[key] = value
        translation = english

        # NOTE: Patch 'back_link' property to match the API result.
        for cid, card in translation.items():
            if card.get("back_link"):
                card["linked_card"] = copy.deepcopy(translation[card["back_link"]])

        # NOTE: Patch 'duplicate_of' property to match the API result.
        for cid, card in translation.items():
            if card.get("duplicate_of"):
                new_card = copy.deepcopy(translation[card["duplicate_of"]])
                for key, value in card.items():
                    new_card[key] = value
                translation[cid] = new_card

        # NOTE: Patch linked cards missing encounter set.
        update_encounter_code(translation)

        with open(filename, "w", encoding="utf-8") as file:
            json_str = json.dumps(list(translation.values()), indent=2, ensure_ascii=False)
            file.write(json_str)

    if not len(ahdb):
        print("Processing ArkhamDB data...")

        cards = []
        with open(filename, encoding="utf-8") as file:
            cards.extend(json.loads(file.read()))
        # NOTE: Add taboo cards with -t suffix.
        with open(f"translations/{lang_code}/taboo.json", encoding="utf-8") as file:
            cards.extend(json.loads(file.read()))
        for card in cards:
            ahdb[card["code"]] = card
        # NOTE: Add parallel cards with all front back combinations.
        for cid in ["90001", "90008", "90017", "90024", "90037"]:
            card = ahdb[cid]
            old_id = card["alternate_of"]
            old_card = ahdb[old_id]

            pid = f"{old_id}-p"
            pp_card = copy.deepcopy(card)
            pp_card["code"] = pid
            ahdb[pid] = pp_card

            pfid = f"{old_id}-pf"
            pf_card = copy.deepcopy(card)
            pf_card["code"] = pfid
            pf_card["back_text"] = old_card.get("back_text", "")
            pf_card["back_flavor"] = old_card.get("back_flavor", "")
            ahdb[pfid] = pf_card

            properties = [
                "pack_code",
                "illustrator",
                "position",
                "text",
                "flavor",
                "health",
                "sanity",
                "skill_willpower",
                "skill_intellect",
                "skill_combat",
                "skill_agility",
            ]
            pb_card = copy_card_properties(old_card, card, properties)
            ahdb[pb_card["code"]] = pb_card

        # NOTE: Patching special point attributes as separate fields.
        points = {
            "shelter": [
                "08502",
                "08503",
                "08504",
                "08505",
                "08506",
                "08507",
                "08508",
                "08509",
                "08510",
                "08511",
                "08512",
                "08513",
                "08514",
            ],
            "blob": ["85039", "85040", "85041", "85042"],
        }
        for point_key, ids in points.items():
            for cid in ids:
                card = ahdb[cid]
                re_point = r"\s*<b>.*?(\d+)(</b>[.。]|[.。]</b>)\s*$"
                match = re.search(re_point, card["text"])
                point = int(match.group(1))
                card[point_key] = point
                card["text"] = re.sub(re_point, "", card["text"])
    try:
        return ahdb[ahdb_id]
    except KeyError:
        print(f"Error: Card with ID {ahdb_id} not found in ArkhamDB data", file=sys.stderr)
        return None


url_map = None


def read_url_map():
    global url_map
    if not (url_file_path := args.url_file):
        print("Error: URL file not specified.")
        return {}, {}
    if not (url_file := Path(url_file_path)).is_file():
        with url_file.open("w", encoding="utf-8") as fh:
            json_str = json.dumps({}, indent=2, ensure_ascii=False)
            fh.write(json_str)
    if url_map is None:
        with Path.open(encoding="utf-8") as fh:
            url_map = json.loads(fh.read())

    if not (url_map and hasattr(url_map, "keys")):
        print("Error: URL file is empty or not an object.")
        return {}, {}

    url_id_map = {
        url: url_id for lang, url_set in url_map.items() for url_id, url in url_set.items()
    }

    return url_map, url_id_map


def write_url_map() -> None:
    Path(args.cache_dir).mkdir(parents=True, exist_ok=True)
    if url_map is not None:
        with open(args.url_file, "w", encoding="utf-8") as file:
            json_str = json.dumps(url_map, indent=2, sort_keys=True)
            file.write(json_str)


def get_en_url_id(url: str) -> str | None:
    if not url:
        print("Error: URL not specified.")
        return None
    en_url_map, url_id_map = read_url_map()
    if url in url_id_map:
        return url_id_map[url]
    url_uuid = str(uuid.uuid4()).replace("-", "")
    en_url_map.setdefault("en", {})[url_uuid] = url
    write_url_map()
    return url_uuid


def set_url_id(url_id, url) -> None:
    url_map, _ = read_url_map()
    if args.lang not in url_map:
        url_map[args.lang] = {}
    url_map[args.lang][url_id] = url
    write_url_map()


def encode_result_id(url_id, deck_w, deck_h, deck_x, deck_y, rotate, sheet) -> str:
    return f"{url_id}-{deck_w}-{deck_h}-{deck_x}-{deck_y}-{1 if rotate else 0}-{sheet}"


def decode_result_id(result_id):
    parts = result_id.split("-")
    return (
        parts[0],
        int(parts[1]),
        int(parts[2]),
        int(parts[3]),
        int(parts[4]),
        bool(int(parts[5])),
        int(parts[6]),
    )


def download_deck_image(url) -> Path:
    decks_folder = f"{args.cache_dir}/decks"
    Path(decks_folder).mkdir(parents=True, exist_ok=True)
    url_id = get_en_url_id(url)
    if url_id is None:
        raise ValueError("URL not specified.")
    filename = f"{decks_folder}/{url_id}.jpg"
    if not os.path.isfile(filename):
        print(f"Downloading {url_id}.jpg...")
        urllib.request.urlretrieve(url, filename)
    return filename


def crop_card_image(result_id, deck_image_filename):
    cards_folder = f"{args.cache_dir}/cards"
    Path(cards_folder).mkdir(parents=True, exist_ok=True)
    filename = f"{cards_folder}/{result_id}.png"
    if not os.path.isfile(filename):
        print(f"Cropping {result_id}.png...")
        _, deck_w, deck_h, deck_x, deck_y, rotate, _ = decode_result_id(result_id)
        deck_image = Image.open(deck_image_filename)
        width = deck_image.width / deck_w
        height = deck_image.height / deck_h
        left = deck_x * width
        top = deck_y * height
        card_image = deck_image.crop((left, top, left + width, top + height))
        if rotate:
            card_image = card_image.transpose(method=Image.Transpose.ROTATE_90)
        card_image.save(filename)
    return filename


se_types = [
    "asset",
    "asset_encounter",
    "event",
    "skill",
    "investigator_front",
    "investigator_back",
    "investigator_encounter_front",
    "investigator_encounter_back",
    "treachery_weakness",
    "treachery_encounter",
    "enemy_weakness",
    "enemy_encounter",
    "agenda_front",
    "agenda_back",
    "act_front",
    "act_back",
    "image_front",
    "image_back",
    "location_front",
    "location_back",
    "scenario_front",
    "scenario_back",
    "scenario_header",
    "story",
]
se_cards = dict(zip(se_types, [[] for _ in range(len(se_types))], strict=False))
result_set = set()


def get_decks(card_obj):
    return [(int(deck_id), deck) for deck_id, deck in card_obj["CustomDeck"].items()]


def translate_sced_card(url, deck_w, deck_h, deck_x, deck_y, is_front, card, metadata) -> None:
    card_type = card["type_code"]
    rotate = card_type in ["investigator", "agenda", "act"]
    sheet = 0 if is_front else 1
    result_id = encode_result_id(get_en_url_id(url), deck_w, deck_h, deck_x, deck_y, rotate, sheet)
    if result_id in result_set:
        return
    print(f"Translating {result_id}...")

    if card_type == "asset":
        se_type = "asset_encounter" if card.get("encounter_code") else "asset"
    elif card_type == "event":
        se_type = "event"
    elif card_type == "skill":
        se_type = "skill"
    elif card_type == "investigator":
        if card.get("encounter_code") is not None:
            se_type = "investigator_encounter_front" if is_front else "investigator_encounter_back"
        else:
            se_type = "investigator_front" if is_front else "investigator_back"
    elif card_type == "treachery":
        if card.get("subtype_code") in ["basicweakness", "weakness"]:
            se_type = "treachery_weakness"
        else:
            se_type = "treachery_encounter"
    elif card_type == "enemy":
        if card.get("subtype_code") in ["basicweakness", "weakness"]:
            se_type = "enemy_weakness"
        else:
            se_type = "enemy_encounter"
    elif card_type == "agenda":
        # NOTE: Agenda with image are special cased.
        if is_front and check_se_agenda_image_front(card):
            se_type = "image_front"
        elif not is_front and is_se_agenda_image_back(card):
            se_type = "image_back"
        else:
            se_type = "agenda_front" if is_front else "agenda_back"
    elif card_type == "act":
        # NOTE: Act with image are special cased.
        if is_front and is_se_act_image_front(card):
            se_type = "image_front"
        elif not is_front and is_se_act_image_back(card):
            se_type = "image_back"
        else:
            se_type = "act_front" if is_front else "act_back"
    elif card_type == "location":
        se_type = "location_front" if is_front else "location_back"
    elif card_type == "scenario":
        # NOTE: Return to scenario cards are using story with scenario template.
        if is_return_to_scenario(card):
            se_type = "story"
        else:
            se_type = "scenario_front" if is_front else "scenario_back"
    elif card_type == "story":
        # NOTE: Some scenario cards are recorded as story in ADB, handle them specially here.
        se_type = "scenario_header" if card["code"] == "06078" and not is_front else "story"
    else:
        se_type = None

    try:
        deck_image_filename = download_deck_image(url)
        if not deck_image_filename:
            raise ValueError("Deck image not found.")
    except ValueError as e:
        print(f"Error: {e}")
        return
    image_filename = crop_card_image(result_id, deck_image_filename)
    image = Image.open(image_filename)
    template_width = 375
    image_scale = template_width / (image.height if rotate else image.width)
    move_map = {
        "asset": (0, 93),
        "asset_encounter": (0, 93),
        "event": (0, 118),
        "skill": (0, 75),
        "investigator_front": (247, -48),
        "investigator_back": (168, 86),
        "investigator_encounter_front": (247, -48),
        "investigator_encounter_back": (168, 86),
        "treachery_weakness": (0, 114),
        "treachery_encounter": (0, 114),
        "enemy_weakness": (0, -122),
        "enemy_encounter": (0, -122),
        "agenda_front": (110, 0),
        "agenda_back": (0, 0),
        "act_front": (-98, 0),
        "act_back": (0, 0),
        "image_front": (0, 0),
        "image_back": (0, 0),
        "location_front": (0, 83),
        "location_back": (0, 83),
        "scenario_front": (0, 0),
        "scenario_back": (0, 0),
        "scenario_header": (0, 0),
        "story": (0, 0),
    }
    # NOTE: Handle the case where agenda and act direction reversed on cards.
    if se_type in ["agenda_front", "act_front"] and is_se_progress_reversed(card):
        move_map_se_type = "act_front" if se_type == "agenda_front" else "agenda_front"
    else:
        move_map_se_type = se_type
    image_move_x, image_move_y = move_map[move_map_se_type]
    image_filename = os.path.abspath(image_filename)
    se_cards[se_type].append(
        get_se_card(
            result_id,
            card,
            metadata,
            image_filename,
            image_scale,
            image_move_x,
            image_move_y,
        )
    )
    result_set.add(result_id)


def translate_sced_card_object(card_obj, metadata, card) -> None:
    # Create a Card or EnemyCard object
    if card['type'] == 'Enemy':
        card_instance = EnemyCard(card)
    else:
        card_instance = Card(card)

    deck_id, deck = get_decks(card_obj)[0]
    deck_w = deck["NumWidth"]
    deck_h = deck["NumHeight"]
    deck_xy = card_obj["CardID"] % 100
    deck_x = deck_xy % deck_w
    deck_y = deck_xy // deck_w

    front_card = card
    back_card = card
    # NOTE: The first front means the front side in SCED using front url, the second front means whether it's the logical front side for the card type.
    front_is_front = True
    back_is_front = False
    # NOTE: Some cards on ADB have separate entries for front and back, where the front one is the main card data. Always ensure the card id in SCED is the front one,
    # and get the correct back card data through the 'linked_card' property.
    if "linked_card" in card:
        back_card = card["linked_card"]
        back_is_front = True
        # NOTE: In certain cases the face order in SCED is opposite to that on ArkhamDB.
        if card["code"] in REVERSED_CARD_CODES:
            front_card, back_card = back_card, front_card
    else:
        # NOTE: SCED thinks the front side of location is the unrevealed side, which is different from what SE expects. Reverse it here apart from single faced locations.
        # The same goes for some special cards.
        if (card["type_code"] == "location" and card.get("double_sided", False)) or card[
            "code"
        ] in ["06078", "06346"]:
            front_is_front = False
            back_is_front = True

        # NOTE: Certain location card backs show different pack code from its true pack to make cards indistinguishable during randomization.
        location_map = {
            "53039": "04168",
        }
        if card["code"] in location_map:
            front_card = copy.deepcopy(card)
            front_card["pack_code"] = download_card(location_map[card["code"]])["pack_code"]

    front_url = deck["FaceURL"]
    translate_front = True
    # NOTE: Do not translate front image for full portrait.
    if card["code"] in ["06346"]:
        translate_front = False

    if translate_front:
        translate_sced_card(
            front_url,
            deck_w,
            deck_h,
            deck_x,
            deck_y,
            front_is_front,
            front_card,
            metadata,
        )

    back_url = deck["BackURL"]
    translate_back = True
    # NOTE: Test whether it's generic player or encounter card back urls.
    if "EcbhVuh" in back_url or "sRsWiSG" in back_url:
        translate_back = False
    # NOTE: Special cases to skip generic player or encounter card back in deck images.
    if (deck_id, deck_x, deck_y) in [
        (2335, 9, 5),
        (2661, 2, 1),
        (2661, 3, 1),
        (2661, 4, 1),
        (2661, 2, 2),
        (2661, 3, 2),
        (2661, 4, 2),
        (2661, 5, 2),
        (2661, 6, 2),
        (2661, 7, 2),
        (2661, 8, 2),
        (2661, 9, 2),
        (2661, 0, 3),
        (2661, 1, 3),
        (2661, 2, 3),
        (2661, 3, 3),
        (2661, 4, 3),
        (2661, 5, 3),
        (2661, 6, 3),
        (2661, 7, 3),
        (2661, 8, 3),
        (2661, 9, 3),
        (2661, 0, 4),
        (2661, 1, 4),
        (4547, 0, 4),
        (4547, 1, 4),
        (2662, 1, 1),
        (2662, 2, 1),
        (2662, 3, 1),
        (2662, 4, 1),
        (2662, 5, 1),
        (2662, 6, 1),
        (2662, 7, 1),
        (5469, 6, 1),
        (5469, 7, 1),
    ]:
        translate_back = False

    if translate_back:
        # NOTE: If back side has a separate entry, then it's treated as if it's the front side of the card.
        if deck["UniqueBack"]:
            translate_sced_card(
                back_url,
                deck_w,
                deck_h,
                deck_x,
                deck_y,
                back_is_front,
                back_card,
                metadata,
            )
        else:
            # NOTE: Even if the back is non-unique, SCED may still use it for interesting cards, e.g. Sophie: It Was All My Fault.
            translate_sced_card(back_url, 1, 1, 0, 0, back_is_front, back_card, metadata)


def translate_sced_token_object(token_obj, metadata, card) -> None:
    image_url = token_obj["CustomImage"]["ImageURL"]
    is_front = token_obj["Description"].endswith("Easy/Standard")
    translate_sced_card(image_url, 1, 1, 0, 0, is_front, card, metadata)


def translate_sced_object(sced_obj, metadata, card, _1, _2) -> None:
    if sced_obj["Name"] in ["Card", "CardCustom"]:
        translate_sced_card_object(sced_obj, metadata, card)
    elif sced_obj["Name"] == "Custom_Token":
        translate_sced_token_object(sced_obj, metadata, card)


def is_translatable(ahdb_id):
    # NOTE: Skip minicards.
    return "-m" not in ahdb_id


def process_player_cards(callback: Callable) -> None:
    repo_folder = download_repo(args.mod_dir_primary, "argonui/SCED")
    player_folder = f"{repo_folder}/objects/AllPlayerCards.15bb07"
    for filename in os.listdir(player_folder):
        if filename.endswith(".gmnotes"):
            metadata_filename = f"{player_folder}/{filename}"
            with open(metadata_filename, encoding="utf-8") as metadata_file:
                try:
                    metadata = json.loads(metadata_file.read())
                    ahdb_id = metadata["id"]
                    if is_translatable(ahdb_id):
                        card = download_card(ahdb_id)
                        if not card:
                            print(f"Empty card with {ahdb_id=}")
                            continue
                    if eval(args.filter):
                        object_filename = metadata_filename.replace(".gmnotes", ".json")
                        with open(object_filename, encoding="utf-8") as object_file:
                            card_obj = json.loads(object_file.read())
                        callback(card_obj, metadata, card, object_filename, card_obj)
                        # NOTE: Process card objects with alternative states, e.g. Revised Core investigators.
                        if "States" in card_obj:
                            for state_object in card_obj["States"].values():
                                callback(
                                    state_object,
                                    metadata,
                                    card,
                                    object_filename,
                                    card_obj,
                                )
                except KeyError as e:
                    print(
                        f"Warning: Missing key {e} in metadata for file {filename}",
                        file=sys.stderr,
                    )
                    continue


def process_encounter_cards(callback, **kwargs) -> None:
    include_decks = kwargs.get("include_decks", False)
    repo_folder = download_repo(args.mod_dir_secondary, "Chr1Z93/loadable-objects")
    folders = ["campaigns", "scenarios"]
    # NOTE: These campaigns don't have data on ADB yet.
    skip_files = [
        "the_scarlet_keys.json",
        "fortune_and_folly.json",
        "machinations_through_time.json",
        "meddling_of_meowlathotep.json",
    ]
    for folder in folders:
        campaign_folder = f"{repo_folder}/{folder}"
        for filename in os.listdir(campaign_folder):
            if filename in skip_files:
                continue
            campaign_filename = f"{campaign_folder}/{filename}"
            with open(campaign_filename, encoding="utf-8") as object_file:

                def find_encounter_objects(en_obj):
                    if isinstance(en_obj, dict):
                        if include_decks and en_obj.get("Name") == "Deck":
                            results = find_encounter_objects(en_obj["ContainedObjects"])
                            results.append(en_obj)
                            return results
                        if (
                            en_obj.get("Name")
                            in [
                                "Card",
                                "CardCustom",
                            ]
                            and en_obj.get("GMNotes", "").startswith("{")
                        ) or (
                            en_obj.get("Name") == "Custom_Token"
                            and en_obj.get("Nickname") == "Scenario"
                            and en_obj.get("GMNotes", "").startswith("{")
                        ):
                            return [en_obj]
                        if "ContainedObjects" in en_obj:
                            return find_encounter_objects(en_obj["ContainedObjects"])
                        return []
                    if isinstance(en_obj, list):
                        results = []
                        for inner_obj in en_obj:
                            results.extend(find_encounter_objects(inner_obj))
                        return results
                    return []

                campaign = json.loads(object_file.read())
                for en_object in find_encounter_objects(campaign):
                    if en_object.get("Name", None) == "Deck":
                        callback(en_object, None, None, campaign_filename, campaign)
                    else:
                        try:
                            metadata: dict[str, Any] = json.loads(en_object["GMNotes"])
                            ahdb_id = metadata.get("id")
                            if ahdb_id and is_translatable(ahdb_id):
                                card: dict[str, Any] | None = download_card(ahdb_id)
                                if card and eval(args.filter):
                                    callback(
                                        en_object,
                                        metadata,
                                        card,
                                        campaign_filename,
                                        campaign,
                                    )
                            elif not ahdb_id:
                                print(
                                    f"Warning: Missing id in GMNotes for file {campaign_filename}"
                                )
                        except KeyError as e:
                            print(
                                f"Warning: Missing key {e} in GMNotes for object in file {filename}"
                            )
                            continue


def write_csv() -> None:
    data_dir = Path("SE_Generator/data")
    shutil.rmtree(data_dir, ignore_errors=True)
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    for se_type in se_types:
        print(f"Writing {se_type}.csv...")
        filename = f"{data_dir}/{se_type}.csv"
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            components = se_cards[se_type]
            if len(components):
                fields = list(components[0].keys())
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for component in components:
                    writer.writerow(component)


def generate_images() -> None:
    # NOTE: Update SE font preferences before running the generation script.
    lang_code, _ = get_lang_code_region()
    lang_preferences = f"translations/{lang_code}/preferences"
    print(f"Overwriting with {lang_preferences}...")
    overwrites = {}
    with open(lang_preferences, encoding="utf-8") as file:
        for line in file:
            if line:
                key, value = line.split("=")
                overwrites[key] = value
    lines = []
    with open(args.se_preferences, encoding="utf-8") as file:
        for line in file:
            lines.append(line)
    with open(args.se_preferences, mode="w", encoding="utf-8") as file:
        for line in lines:
            fields = line.split("=")
            if len(fields) == 2:
                key, value = fields
                value = overwrites.get(key, value)
                file.write(f"{key}={value}")
            else:
                file.write(line)

    se_script = "SE_Generator/make.js"
    print(f"Running {se_script}...")
    subprocess.run([args.se_executable, "--glang", args.lang, "--run", se_script])


def pack_images() -> None:
    deck_images = {}
    url_map, _ = read_url_map()
    for image_dir in Path("SE_Generator/data").glob("*"):
        if not image_dir.is_dir():
            print(f"Error: {image_dir} is not a directory.")
            continue
        for filename in image_dir.glob("*"):
            print(f"Packing {filename=}...")
            result_id = filename.stem
            deck_url_id, deck_w, deck_h, deck_x, deck_y, rotate, _ = decode_result_id(result_id)
            # NOTE: We use the English version of the url as the base image to pack to avoid repeated saving that reduces quality.
            deck_url = url_map["en"][deck_url_id]
            try:
                deck_image_filename = download_deck_image(deck_url)
                if not deck_image_filename:
                    raise ValueError("Deck image not found.")
            except ValueError as e:
                print(f"Error: {e}")
                continue
            if deck_url_id not in deck_images:
                deck_images[deck_url_id] = Image.open(deck_image_filename)
            deck_image = deck_images[deck_url_id]
            card_image_filename = f"{image_dir}/{filename}"
            card_image = Image.open(card_image_filename)
            if rotate:
                card_image = card_image.transpose(method=Image.Transpose.ROTATE_270)
            width = deck_image.width // deck_w
            height = deck_image.height // deck_h
            left = deck_x * width
            top = deck_y * height
            card_image = card_image.resize((width, height))
            deck_image.paste(card_image, box=(left, top))

    decks_dir = f"{args.decks_dir}/{args.lang}"
    recreate_dir(decks_dir)
    for deck_url_id, deck_image in deck_images.items():
        print(f"Writing {deck_url_id}.jpg...")
        deck_image = deck_image.convert("RGB")
        deck_image.save(f"{decks_dir}/{deck_url_id}.jpg", progressive=True, optimize=True)


def upload_images() -> None:
    dbx = dropbox.Dropbox(args.dropbox_token)
    folder = f"/SCED_Localization_Deck_Images_{args.lang}"
    # NOTE: Create a folder if not already exists.
    with suppress(Exception):
        dbx.files_create_folder(folder)

    decks_dir = Path(args.decks_dir) / str({args.lang})
    for filename in os.listdir(decks_dir):
        print(f"Uploading {filename}...")
        with open(f"{decks_dir}/{filename}", "rb") as file:
            deck_image_data = file.read()
            deck_filename = f"{folder}/{filename}"
            # NOTE: Setting overwrite to true so that the old deck image is replaced, and the sharing link still maintains.
            image = dbx.files_upload(
                deck_image_data, deck_filename, mode=dropbox.files.WriteMode.overwrite
            )
            # NOTE: Remove all existing shared links if we try to force creating new links.
            if args.new_link:
                for link in dbx.sharing_list_shared_links(
                    image.path_display, direct_only=True
                ).links:
                    dbx.sharing_revoke_shared_link(link.url)
            # NOTE: Dropbox will reuse the old sharing link if there's already one exist.
            url = dbx.sharing_create_shared_link(image.path_display, short_url=True).url
            # NOTE: Get direct download link from the dropbox sharing link.
            url = url.replace("?dl=0", "").replace("www.dropbox.com", "dl.dropboxusercontent.com")
            url_id = filename.split(".")[0]
            set_url_id(url_id, url)


updated_files = {}


def update_sced_card_object(card_obj, metadata, card, filename, root) -> None:
    url_map, url_id_map = read_url_map()
    updated_files[filename] = root
    if card:
        name = get_se_front_name(card)
        xp = get_se_xp(card)
        if xp not in ["0", "None"]:
            name += f" ({xp})"
        if card["code"].endswith("-t"):
            module = import_lang_module()
            taboo_func = getattr(module, "transform_taboo", None)
            name += f' ({taboo_func() if taboo_func else "Taboo"})'
        # NOTE: The scenario card names are saved in the 'Description' field in SCED used for the scenario splash screen.
        if card_obj["Nickname"] == "Scenario":
            card_obj["Description"] = name
        else:
            card_obj["Nickname"] = name
            # NOTE: Remove any markup formatting in the tooltip traits text.
            card_obj["Description"] = re.sub(r"<[^>]*>", "", get_se_traits(card))
        print(f"Updating {name}...")

    url_objects = []
    if card_obj.get("Name") == "Custom_Token":
        url_objects.append((card_obj["CustomImage"], "ImageURL"))
    else:
        for _, deck in get_decks(card_obj):
            url_objects.append((deck, "FaceURL"))
            url_objects.append((deck, "BackURL"))

    for url_object, url_key in url_objects:
        # NOTE: Only update if we have seen this URL and assigned an id to it before.
        if url_object[url_key] in url_id_map:
            deck_url_id = url_id_map[url_object[url_key]]
            # NOTE: Only update if we have uploaded the deck image and has a sharing URL for the language before.
            if args.lang in url_map and deck_url_id in url_map[args.lang]:
                url_object[url_key] = url_map[args.lang][deck_url_id]


def update_sced_files() -> None:
    for filename, root in updated_files.items():
        with open(filename, "w", encoding="utf-8") as file:
            print(f"Writing {filename}...")
            json_str = json.dumps(root, indent=2, ensure_ascii=False)
            # NOTE: Reverse the lower case scientific notation 'e' to upper case, in order to be consistent with those generated by TTS.
            json_str = re.sub(r"(\d+)e-(\d\d)", r"\1E-\2", json_str)
            file.write(json_str)


if args.step in [None, PROCESS_STEPS[0]]:
    process_player_cards(translate_sced_object)
    process_encounter_cards(translate_sced_object)
    write_csv()

if args.step in [None, PROCESS_STEPS[1]]:
    generate_images()

if args.step in [None, PROCESS_STEPS[2]]:
    try:
        pack_images()
    except Exception as e:
        print(f"Failed to pack images: {e}")
        raise e

if args.step in [None, PROCESS_STEPS[3]]:
    upload_images()

if args.step in [None, PROCESS_STEPS[4]]:
    process_player_cards(update_sced_card_object)
    process_encounter_cards(update_sced_card_object, include_decks=True)
    update_sced_files()
