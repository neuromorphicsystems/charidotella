name_to_icon = {
    "ant": "🐜",
    "badger": "🦡",
    "bat": "🦇",
    "bear": "🐻",
    "beaver": "🦫",
    "beetle": "🪲",
    "bird": "🐦",
    "bison": "🦬",
    "blowfish": "🐡",
    "boar": "🐗",
    "buffalo": "🐃",
    "bug": "🐛",
    "butterfly": "🦋",
    "camel": "🐪",
    "cat": "🐈",
    "chicken": "🐔",
    "chipmunk": "🐿 ",
    "coral": "🪸",
    "cow": "🐄",
    "crab": "🦀",
    "cricket": "🦗",
    "crocodile": "🐊",
    "deer": "🦌",
    "dodo": "🦤",
    "dog": "🐕",
    "dolphin": "🐬",
    "dove": "🕊 ",
    "dragon": "🐉",
    "duck": "🦆",
    "eagle": "🦅",
    "elephant": "🐘",
    "ewe": "🐑",
    "fish": "🐟",
    "flamingo": "🦩",
    "fly": "🪰",
    "fox": "🦊",
    "frog": "🐸",
    "giraffe": "🦒",
    "goat": "🐐",
    "gorilla": "🦍",
    "hamster": "🐹",
    "hedgehog": "🦔",
    "hippopotamus": "🦛",
    "honeybee": "🐝",
    "horse": "🐎",
    "kangaroo": "🦘",
    "koala": "🐨",
    "leopard": "🐆",
    "lion": "🦁",
    "lizard": "🦎",
    "llama": "🦙",
    "lobster": "🦞",
    "mammoth": "🦣",
    "monkey": "🐒",
    "mosquito": "🦟",
    "mouse": "🐁",
    "octopus": "🐙",
    "orangutan": "🦧",
    "otter": "🦦",
    "owl": "🦉",
    "ox": "🐂",
    "panda": "🐼",
    "parrot": "🦜",
    "peacock": "🦚",
    "penguin": "🐧",
    "pig": "🐖",
    "poodle": "🐩",
    "rabbit": "🐇",
    "raccoon": "🦝",
    "ram": "🐏",
    "rat": "🐀",
    "rhinoceros": "🦏",
    "rooster": "🐓",
    "sauropod": "🦕",
    "scorpion": "🦂",
    "seal": "🦭",
    "shark": "🦈",
    "shrimp": "🦐",
    "skunk": "🦨",
    "sloth": "🦥",
    "snail": "🐌",
    "snake": "🐍",
    "spider": "🕷 ",
    "squid": "🦑",
    "swan": "🦢",
    "t-rex": "🦖",
    "tiger": "🐅",
    "turkey": "🦃",
    "turtle": "🐢",
    "unicorn": "🦄",
    "whale": "🐋",
    "wolf": "🐺",
    "zebra": "🦓",
}


def composite_name_to_icon(composite_name: str):
    for name, icon in name_to_icon.items():
        if name in composite_name:
            return icon
    return "🐾"


def generate_names(count: int):
    import copy

    import coolname
    import coolname.data

    config = copy.copy(coolname.data.config)
    config["animal"]["words"] = list(name_to_icon.keys())
    config["subj"]["lists"] = ["animal"]
    generator = coolname.RandomGenerator(config)
    coolname_length = 4
    for length in (2, 3):
        if count < generator.get_combinations_count(length) / 2:
            coolname_length = length
            break
    names = []
    while len(set(names)) < count:
        while len(names) < count:
            names.append(generator.generate_slug(coolname_length))
    names.sort()
    return names
