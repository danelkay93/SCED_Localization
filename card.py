import importlib
import inspect


class Card:
    def __init__(self, card_dict):
        self.card_dict = card_dict

    def get_name(self):
        name = self.card_dict.get("name", "")
        return self.transform_lang(name)

    def get_description(self):
        description = self.card_dict.get("description", "")
        return self.transform_lang(description)

    def get_type(self):
        return self.card_dict.get("type", "")

    def transform_lang(self, value):
        module = self.import_lang_module()
        attr = inspect.stack()[1].function.replace("get_se_", "")
        func_name = f"transform_{attr}"
        func = getattr(module, func_name, None)
        return func(value) if func else value

    def import_lang_module(self):
        return importlib.import_module("lang_module")

    def print_card_details(self):
        print(f"Name: {self.get_name()}")
        print(f"Description: {self.get_description()}")
        print(f"Type: {self.get_type()}")


class EnemyCard(Card):
    ADB_VAR_HEALTH = -2

    def get_health(self):
        health = self.card_dict.get("health", "-")
        if health == self.ADB_VAR_HEALTH:
            health = "X"
        return str(health)

    def get_attack(self):
        return self.card_dict.get("attack", "")

    def get_defense(self):
        return self.card_dict.get("defense", "")

    def print_card_details(self):
        super().print_card_details()
        print(f"Health: {self.get_health()}")
        print(f"Attack: {self.get_attack()}")
        print(f"Defense: {self.get_defense()}")


# Usage:
card_dict = {...}  # some dictionary representing a card
card = EnemyCard(card_dict)
