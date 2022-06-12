import random
import json
import argparse
import os
import glob
from generate import generate
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from card_utils import *
from json_utils import *

from typing import Tuple, Dict

# make_card.py 파일이 위치한 디렉토리
current_dir = os.getcwd()

#######################
### argument parser ###
#######################

parser = argparse.ArgumentParser()
parser.add_argument("--num", required=True, help="the number of images")
parser.add_argument("--dir", required=True, help="directory of json file")
parser.add_argument("--width", required=True, help="image width")
parser.add_argument("--test", type=bool, required=False, default=False, help="test mode")
parser.add_argument("--template_name", default="", required=False, help="template name")

#####################
### bbox function ###
#####################


def define_bbox(start: tuple, mode: str, content: str, type: str, x_limit: int, font):
    font_scale = font_size[type]
    while True:
        if mode == "left":
            x, y = start[0], start[1]
        elif mode == "right":
            x, y = start[0] - font.getsize(content)[0], start[1]
        elif mode == "center":
            x, y = start[0] - font.getsize(content)[0] // 2, start[1]
        bbox_width, bbox_height = font.getsize(content)

        if (
            mode in ["center", "left"]
            and x > 0
            and x + bbox_width < width
            and bbox_width < abs(x - width)
        ):
            break
        if (
            mode == "right"
            and x > 0
            and x + bbox_width < width
            and x_limit <= x
            and bbox_width < abs(x - width)
        ):
            break
        else:
            OK = False
            while True:
                font_scale -= 1
                font = ImageFont.truetype(font_family[type], font_scale)
                bbox_width, bbox_height = font.getsize(content)
                if (
                    mode in ["center", "left"]
                    and x > 0
                    and x + bbox_width < width
                    and bbox_width < abs(x - width)
                ):
                    OK = True
                    break
                if (
                    mode == "right"
                    and x > 0
                    and x + bbox_width < width
                    and x_limit <= x
                    and bbox_width < abs(x - width)
                ):
                    OK = True
                    break

                if font_scale < font_size[type] * 0.3:  # 최소한의 크기
                    OK = True
                    font_scale = 0
                    break

            if OK == True:
                break

            # 내용 변경
            if OK is False:
                content = regenerate(type)
                bbox_width, bbox_height = font.getsize(content)
                if (
                    mode in ["center", "left"]
                    and x >= 0
                    and x + bbox_width <= width
                    and bbox_width < abs(x - width)
                ):
                    break
                if (
                    mode == "right"
                    and x >= 0
                    and x + bbox_width <= width
                    and x_limit <= x
                    and bbox_width < abs(x - width)
                ):
                    break

    return (x, y), content, font_scale


def define_dep_pos_bbox(info: dict, start: tuple, mode: str, x_limit: int):
    sep = position_separator()
    font = ImageFont.truetype(font_family["position"], font_size["position"])
    font_scale = font_size["position"]
    while True:
        department, position = info["department"], info["position"]
        content = department + " " + sep + " " + position
        if mode == "left":
            x, y = start[0], start[1]
        elif mode == "right":
            x, y = start[0] - font.getsize(content)[0], start[1]
        elif mode == "center":
            x, y = start[0] - font.getsize(content)[0] // 2, start[1]

        bbox_width, bbox_height = font.getsize(content)
        if mode in ["center", "left"] and x >= 0 and x + bbox_width <= width:
            break
        if mode == "right" and x >= 0 and x + bbox_width <= width and x_limit <= x:
            break
        else:
            type = "position"
            OK = False
            while True:
                font_scale -= 1
                font = ImageFont.truetype(font_family[type], font_scale)
                bbox_width, bbox_height = font.getsize(content)
                if (
                    mode in ["center", "left"]
                    and x >= 0
                    and x + bbox_width <= width
                    and bbox_width < abs(x - width)
                ):
                    OK = True
                    break
                if (
                    mode == "right"
                    and x >= 0
                    and x + bbox_width <= width
                    and x_limit <= x
                    and bbox_width < abs(x - width)
                ):
                    OK = True
                    break

                if font_scale < font_size[type] * 0.3:  # 최소한의 크기
                    OK = True
                    font_scale = 0
                    break
            if OK == True:
                break

            # 내용 변경
            if OK is False:
                info = generate()

    return (x, y), department, sep, position, font_scale


def define_num_bbox(
    start: tuple, content: str, type: str, mode: str, x_limit: int, font
):
    sep = num_separator()
    if type == "license_number":
        type = "사업자등록번호"
    item_name = type + sep
    while True:
        if mode == "left":
            item_name_x, item_name_y = start[0], start[1]
            item_x, item_y = item_name_x + font.getsize(item_name)[0], item_name_y
        elif mode == "right":
            item_x, item_y = (start[0] - font.getsize(content)[0], start[1])
            item_name_x, item_name_y = item_x - font.getsize(item_name)[0], item_y
        elif mode == "center":
            text_width = font.getsize(item_name)[0] + font.getsize(content)[0]
            item_name_x, item_name_y = start[0] - text_width // 2, start[1]
            item_x, item_y = item_name_x + font.getsize(item_name)[0], item_name_y
        bbox_width, bbox_height = font.getsize(item_name + content)

        if (
            mode in ["center", "left"]
            and item_name_x >= 0
            and item_name_x + bbox_width <= width
            and bbox_width < abs(item_name_x - width)
        ):
            break
        if (
            mode == "right"
            and item_name_x >= 0
            and item_name_x + bbox_width <= width
            and x_limit <= item_name_x
            and bbox_width < abs(item_name_x - width)
        ):
            break
        else:
            content = regenerate(type)
    return (item_name_x, item_name_y), (item_x, item_y), content, item_name


def draw_and_write(bbox_start: Tuple[int, int], content: str, item: str, font, draw):
    """
    명함 이미지에 텍스트 내용을 작성하고,
    json 파일에 annotation 정보를 저장합니다.

    Args:
        bbox_start (tuple): bbox의 시작 지점 (x, y)
        content (str): bbox에 포함된 텍스트 내용
        item (str): bbox에 포함된 정보 항목의 이름
        font : 텍스트를 표현할 글씨 정보
        draw : 이미지에 그림을 그리는 객체
    """
    draw.text(
        bbox_start,
        content,
        font=font,
        fill=font_color[item],
    )
    put_word(item, content.strip(), bbox_start, font)


def put_word(item: str, content: str, start: Tuple[int, int], font):
    """
    json 파일에 annotation 정보를 리스트에 저장합니다.

    Args:
        item (str): bbox에 포함된 정보 항목의 이름
        content (str): bbox에 포함된 텍스트 내용
        start (tuple): bbox의 시작 지점 (x, y)
        font: 텍스트를 표현할 글씨 정보
    """
    temp_word = dict()
    temp_word["category_id"] = get_category_id(item)
    temp_word["orientation"] = "Horizontal"
    temp_word["text"] = content

    text_width, text_height = int(font.getsize(content)[0]), int(
        font.getsize(content)[1]
    )
    start_x, start_y = int(start[0]), int(start[1])
    temp_word["points"] = [
        [start_x, start_y],
        [start_x + text_width, start_y],
        [start_x + text_width, start_y + text_height],
        [start_x, start_y + text_height],
    ]
    word.append(temp_word)


####################
## template class ##
####################


class OneItemTemplate:
    # company # name # department # position
    def __init__(self, info: dict, type: str, x: int, y: int, mode: str):
        self.items = info
        self.type = type
        self.bbox_x = x
        self.bbox_y = y
        self.mode = mode

        self.start = dict()
        self.start["center"] = (
            width // 2 + width * random.uniform(-MIN_X, MIN_X),
            self.bbox_y,
        )
        self.start["left"] = (self.bbox_x, self.bbox_y)
        self.start["right"] = (width - width * random.uniform(0, MIN_X), self.bbox_y)

        self.start = self.start[self.mode]

    def make(self):
        draw = ImageDraw.Draw(image)

        # 텍스트 생성 후, bbox를 범위 내로 움직이기
        font = ImageFont.truetype(font_family[self.type], font_size[self.type])

        content = self.items[self.type]
        self.start, content, font_scale = define_bbox(
            self.start, self.mode, content, self.type, self.bbox_x, font
        )
        bbox_x, bbox_y = self.start
        bbox_width, bbox_height = font.getsize(content)

        if bbox_y + bbox_height > height:
            return (bbox_x, bbox_y + bbox_height)
        if font_scale != 0:  # 제외
            font = ImageFont.truetype(font_family[self.type], font_scale)
            draw_and_write(self.start, content, self.type, font, draw)
            return (bbox_x + bbox_width, bbox_y + bbox_height)

        else:
            return (bbox_x, bbox_y + bbox_height)


class TwoItemsTemplate:
    # department & position
    def __init__(self, items: Dict[str, str], x: int, y: int, mode: str):
        self.items = items

        self.bbox_x = x
        self.bbox_y = y
        self.mode = mode

        self.start = dict()
        self.start["center"] = (width // 2, self.bbox_y)
        self.start["left"] = (self.bbox_x, self.bbox_y)
        self.start["right"] = (width - width * random.uniform(0, MIN_X), self.bbox_y)

        self.start = self.start[self.mode]

    def make(self):
        draw = ImageDraw.Draw(image)

        # 텍스트 생성 후, bbox를 범위 내로 움직이기 # regenerate 필요 없음
        font = ImageFont.truetype(font_family["position"], font_size["position"])

        # 내용만 변경하면 오래 걸림
        self.start, department, sep, position, font_scale = define_dep_pos_bbox(
            self.items, self.start, self.mode, self.bbox_x
        )
        bbox_x, bbox_y = self.start
        bbox_width, bbox_height = font.getsize(department + " " + sep + " " + position)

        if font_scale == 0:  # 제외
            return (bbox_x, bbox_y + bbox_height)

        else:
            font = ImageFont.truetype(font_family["position"], font_scale)

            if random.random() >= 0.5:  # dep + pos 순서
                # department
                draw_and_write(
                    self.start,
                    department,
                    "department",
                    font,
                    draw,
                )
                # sep
                draw_and_write(
                    (
                        self.start[0]
                        + font.getsize(department)[0]
                        + font.getsize(" ")[0],
                        self.start[1],
                    ),
                    sep,
                    "UNKNOWN",
                    font,
                    draw,
                )
                # position
                draw_and_write(
                    (
                        self.start[0]
                        + font.getsize(department)[0]
                        + font.getsize(" ")[0]
                        + font.getsize(sep)[0]
                        + font.getsize(" ")[0],
                        self.start[1],
                    ),
                    position,
                    "position",
                    font,
                    draw,
                )

                return (bbox_x + bbox_width, bbox_y + bbox_height)
            else:
                # department
                draw_and_write(
                    self.start,
                    position,
                    "position",
                    font,
                    draw,
                )
                # sep
                draw_and_write(
                    (
                        self.start[0]
                        + font.getsize(position)[0]
                        + font.getsize(" ")[0],
                        self.start[1],
                    ),
                    sep,
                    "UNKNOWN",
                    font,
                    draw,
                )
                # position
                draw_and_write(
                    (
                        self.start[0]
                        + font.getsize(position)[0]
                        + font.getsize(" ")[0]
                        + font.getsize(sep)[0]
                        + font.getsize(" ")[0],
                        self.start[1],
                    ),
                    department,
                    "department",
                    font,
                    draw,
                )

                return (bbox_x + bbox_width, bbox_y + bbox_height)


class NumTemplate:
    """
    숫자 및 기타 정보의 bbox 위치를 지정합니다.

    Attributes:
        items (Dict[str, str]): 숫자 및 기타 정보 (key: value)
        start (Tuple[Tuple[int, int]]): 각 mode에 대한 bbox의 시작 지점 (x, y)
        mode (List[str]): 명함 이미지의 왼쪽에 위치하면, 'left' / 오른쪽에 위치하면, 'right'

    Methods:
        make: 랜덤으로 mode를 선택하여,
              숫자 및 기타 정보의 bbox 위치를 지정하고, 명함 이미지를 생성합니다.
    """

    def __init__(
        self,
        items: Dict[str, str],
        x: int,
        y: int,
        mode: str,
    ):
        self.items = items
        self.bbox_x = x
        self.bbox_y = y
        self.mode = mode

        self.start = dict()
        self.start["center"] = (
            width // 2 + width * random.uniform(-MIN_X, MIN_X),
            self.bbox_y,
        )
        self.start["left"] = (self.bbox_x, self.bbox_y)
        self.start["right"] = (width - width * random.uniform(0, MIN_X), self.bbox_y)

        self.start = self.start[self.mode]

    def make(self):
        draw = ImageDraw.Draw(image)
        y_margin = height * random.uniform(MIN_Y, MAX_Y)

        random_items = list(self.items.keys())
        random.shuffle(random_items)
        for item in random_items:
            item_name, content = item, self.items[item]

            font = ImageFont.truetype(font_family[item_name], font_size[item_name])

            # bbox 영역이 범위 내에 존재하는지 확인
            item_name_bbox, item_bbox, content, item_name = define_num_bbox(
                self.start, content, item, self.mode, self.bbox_x, font
            )

            num_height = item_bbox[1] + font.getsize(content)[1]

            # 숫자 및 기타 정보가 이름 정보의 높이를 넘어가는지 확인
            if num_height <= height:  # - height*random.uniform(0.01, 0.05):
                draw_and_write(item_name_bbox, item_name, "UNKNOWN", font, draw)
                draw_and_write(item_bbox, content, item, font, draw)

            else:
                break

            self.start = self.start[0], num_height + y_margin
        return self.start[1]  # y, height


class Template1:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        x = width * random.uniform(MIN_X, MAX_X)  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.6)  # 시작지점 y

        x, y = OneItemTemplate(self.items, "company", 0, y, "left").make()

        loc = ["center", "right", "left"]

        if random.random() >= 0.5:  # template 1
            x = width * random.uniform(MIN_X, MAX_X)

            index = random.randint(0, len(loc) - 1)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
            x += width * random.uniform(-MIN_X, MIN_X)
            y += height * random.uniform(MIN_Y, MAX_Y)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:
                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
        else:  # template 2
            x = width * random.uniform(MIN_X, MAX_X)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:

                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
            x += (
                width * random.uniform(MIN_X, MAX_X)
                if random.random() >= 0.5
                else -width * random.uniform(MIN_X, MAX_X)
            )
            y += height * random.uniform(MIN_Y, MAX_Y)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        use = ["phone", "website","email"]
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()


class Template2:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        logo_size = random.randint(50, 70)
        x = random.randint(0, width - logo_size)
        y = height * random.uniform(0.1, 0.3)  # 시작지점 y

        # 로고 이미지
        logo_index = random.randint(0, len(logo) - 1)
        logo_image = Image.open(logo[logo_index]).convert("RGBA")
        logo_size = random.randint(50, 70)
        logo_image = logo_image.resize((logo_size, logo_size))
        image.paste(logo_image, (int(x), int(y)), logo_image)
        y += logo_size + height * random.uniform(0, MAX_Y)  # 시작지점 y

        loc = ["center", "right", "left"]

        if random.random() >= 0.5:  # template 1
            x = width * random.uniform(MIN_X, MAX_X)

            index = random.randint(0, len(loc) - 1)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
            x += width * random.uniform(-MIN_X, MIN_X)
            y += height * random.uniform(MIN_Y, MAX_Y)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:
                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
        else:  # template 2
            x = width * random.uniform(MIN_X, MAX_X)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:

                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
            x += (
                width * random.uniform(MIN_X, MAX_X)
                if random.random() >= 0.5
                else -width * random.uniform(MIN_X, MAX_X)
            )
            y += height * random.uniform(MIN_Y, MAX_Y)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        num = ["phone", "tel", "website", "license_number", "fax", "email", "address"]
        use = []
        while not use:
            use += use_item(num, 0.7)
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()


class Template3:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        x = width * random.uniform(MIN_X, MAX_X)  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.6)  # 시작지점 y

        loc = ["center", "right", "left"]

        if random.random() >= 0.5:  # template 1
            x = width * random.uniform(MIN_X, MAX_X)

            index = random.randint(0, len(loc) - 1)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
            x += width * random.uniform(-MIN_X, MIN_X)
            y += height * random.uniform(MIN_Y, MAX_Y)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:
                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
        else:  # template 2
            x = width * random.uniform(MIN_X, MAX_X)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:

                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
            x += (
                width * random.uniform(MIN_X, MAX_X)
                if random.random() >= 0.5
                else -width * random.uniform(MIN_X, MAX_X)
            )
            y += height * random.uniform(MIN_Y, MAX_Y)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        num = ["phone", "tel", "website", "license_number", "fax", "email", "address"]

        use = []
        while not use:
            use += use_item(num, 0.7)
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()


class Template4:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        x = width * random.uniform(MIN_X, MAX_X)  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.6)  # 시작지점 y

        loc = ["center", "right", "left"]

        x = width * random.uniform(MIN_X, MAX_X)

        index = random.randint(0, len(loc) - 1)

        x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
        x += width * random.uniform(-MIN_X, MIN_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        index = random.randint(0, len(loc) - 1)

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        num = ["phone", "tel", "website", "license_number", "fax", "email", "address"]
        use = []
        while not use:
            use += use_item(num, 0.7)
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()


class Template5:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        x = width * random.uniform(MIN_X, MAX_X)  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.6)  # 시작지점 y

        x, y = OneItemTemplate(self.items, "company", x, y, "center").make()

        loc = ["center", "right", "left"]
        index = random.randint(0, len(loc) - 1)

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        num = ["phone", "tel", "website", "license_number", "fax", "email", "address"]
        use = []
        while not use:
            use += use_item(num, 0.7)
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)

        index = random.randint(0, len(loc) - 1)
        y += height * random.uniform(MIN_Y, MAX_Y)
        x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()


class Template6:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        logo_size = random.randint(50, 70)
        x = random.randint(0, width - logo_size)  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.2)  # 시작지점 y

        # 로고 이미지
        logo_index = random.randint(0, len(logo) - 1)
        logo_image = Image.open(logo[logo_index]).convert("RGBA")

        logo_image = logo_image.resize((logo_size, logo_size))
        image.paste(logo_image, (int(x), int(y)), logo_image)
        y += logo_size + height * random.uniform(0, MAX_Y)  # 시작지점 y

        x, y = OneItemTemplate(self.items, "company", x, y, "center").make()

        loc = ["center", "right", "left"]

        if random.random() >= 0.5:  # template 1
            x = width * random.uniform(MIN_X, MAX_X)

            index = random.randint(0, len(loc) - 1)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
            x += width * random.uniform(-MIN_X, MIN_X)
            y += height * random.uniform(MIN_Y, MAX_Y)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:
                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
        else:  # template 2
            x = width * random.uniform(MIN_X, MAX_X)
            index = random.randint(0, len(loc) - 1)

            if random.random() >= 0.5:
                x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
            else:
                if random.random() >= 0.5:

                    x, y = OneItemTemplate(
                        self.items, "department", x, y, loc[index]
                    ).make()
                else:
                    x, y = OneItemTemplate(
                        self.items, "position", x, y, loc[index]
                    ).make()
            x += (
                width * random.uniform(MIN_X, MAX_X)
                if random.random() >= 0.5
                else -width * random.uniform(MIN_X, MAX_X)
            )
            y += height * random.uniform(MIN_Y, MAX_Y)

            x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        num = ["phone", "tel", "website", "license_number", "fax", "email", "address"]
        use = []
        while not use:
            use += use_item(num, 0.7)
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()


class Template7:
    def __init__(
        self,
        items: Dict[str, str],
    ):
        self.items = items

    def make(self):
        # company
        loc = ["center", "right", "left"]
        index = random.randint(0, len(loc) - 1)
        pre_x = width * random.uniform(
            MIN_X, MAX_X
        )  # (min_margin=0.05, max_margin=0.1)
        y = height * random.uniform(0.1, 0.6)  # 시작지점 y
        x, y= OneItemTemplate(self.items, "company", pre_x, y, 'left').make()

        x =  width * random.uniform(-MIN_X, MIN_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        x, y = OneItemTemplate(self.items, "name", x, y, loc[index]).make()
        y += height * random.uniform(MIN_Y, MAX_Y)

        if random.random() >= 0.5:  # template 1
            x = width * random.uniform(MIN_X, MAX_X)

            index = random.randint(0, len(loc) - 1)

            
            index = random.randint(0, len(loc) - 1)

            x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()
   
        else:  # template 2
            x = width * random.uniform(MIN_X, MAX_X)
            index = random.randint(0, len(loc) - 1)

            x, y = TwoItemsTemplate(self.items, x, y, loc[index]).make()

        x = width * random.uniform(MIN_X, MAX_X)
        y += height * random.uniform(MIN_Y, MAX_Y)
        use = ["phone", "website", "email"]
        num_list = info_item(self.items, use)
        y = NumTemplate(num_list, x, y, loc[index]).make()



##################
## main funcion ##
##################


def main(args):
    global font_family, font_size, font_color
    global word
    global draw, image
    global width, height
    global MIN_X, MAX_X, MIN_Y, MAX_Y

    MIN_X, MAX_X, MIN_Y, MAX_Y = 0.05, 0.1, 0, 0.05
    # 파일 경로
    template_name = [Template1, Template2, Template3, Template4, Template5, Template6, Template7]
    template_num = [0, 0, 0, 0, 0, 0, 0]
    if args.test == True:
        example_directory = f"{current_dir}/test"
    else:
        example_directory = f"{current_dir}/sample"
    make_dir(example_directory)
    image_name = check_file_num(example_directory, ".png")

    # json 파일 저장
    if (
        not os.path.exists(args.dir) or os.path.getsize(args.dir) == 0
    ):  # json 파일이 없거나, 비어있는 경우
        json_data = make_json(args.dir)
    else:
        with open(args.dir, "r") as f:
            json_data = json.load(f)

    for i in tqdm(range(0, int(args.num))):
        info =  {
        "company": "company",
        "department": "department",
        "position": "position",
        "name": "name",
        "phone": "010-0000-0000",
        "email": "000@emamil.com",
        "address": "",
        "license_number": "",
        "website": "000.com",
        "wise": "",
        "fax": "",
        "tel": "",
    }
        word = []

        # images
        width, height = int(args.width), int(int(args.width) * random.uniform(1.0, 1.8))
        json_images = {}
        json_images["width"] = width
        json_images["height"] = height
        json_images["file"] = f"{image_name+i:04}.png"
        json_images["id"] = image_name + i

        # annotations
        json_anno = {}
        json_anno["image_id"] = image_name + i

        font_family = make_font_family()
        font_size = make_font_size()
        background_color, font_color = make_font_color()

        image = Image.new("RGBA", (width, height), background_color)

        index = random.randint(0, len(template_name)-1)
        #  create business card #  start
        if args.test is True:
            eval(args.template_name)(info).make()
        else:
            template_name[index](info).make()
            template_num[index] += 1
            if template_num[index] == 100:
                del template_num[index]
                del template_name[index]
        
                
        #  end

        json_ocr = {}
        json_ocr["word"] = word
        json_anno["ocr"] = json_ocr

        # json 파일 업데이트
        json_data["images"].append(json_images)
        json_data["annotations"].append(json_anno)
        with open(args.dir, "w", encoding="utf-8") as make_file:
            json.dump(json_data, make_file, indent="\t", ensure_ascii=False)  # False 제거

        image.save(f"{example_directory}/{image_name+i:04}.png")


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
