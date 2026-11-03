from __future__ import annotations

import io
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from PIL import Image, ImageColor, ImageDraw, ImageFont

from accounts.models import User
from items.models import Item, ItemPictures

DEFAULT_USERNAME = "seed"
DEFAULT_EMAIL = "seed@example.com"
DEFAULT_PASSWORD = "seed-password"
DEFAULT_PICTURES = 3

PICTURE_SIZE = (960, 640)
TITLE_FONT = ImageFont.load_default(size=56)
INDEX_FONT = ImageFont.load_default(size=28)
BRAND_FONT = ImageFont.load_default(size=24)
PALETTES: tuple[tuple[str, str], ...] = (
    ("#3d5a80", "#98c1d9"),
    ("#7f5539", "#ddb892"),
    ("#588157", "#a3b18a"),
    ("#7d5ba6", "#c9ada7"),
    ("#9a031e", "#e8b4a2"),
)

ITEMS: tuple[tuple[str, str], ...] = (
    (
        "Brass Sextant",
        "Marine sextant in a mahogany case, engraved with the maker's mark of "
        "Heath & Co, London. Mirrors are bright and the index arm moves freely.",
    ),
    (
        "First Edition 'The Hobbit'",
        "Second impression, 1937, with the four colour plates. Original green "
        "cloth, a little faded at the spine, otherwise a clean, tight copy.",
    ),
    (
        "Victorian Mourning Brooch",
        "Black enamel and seed pearl brooch enclosing a lock of woven hair, "
        "the reverse glazed and inscribed 'In Memoriam, 1861'.",
    ),
    (
        "Persian Silk Rug",
        "Hand-knotted Qom silk, approximately 2.1m by 1.4m, with a central "
        "medallion on an ivory field. Even pile throughout, no repairs.",
    ),
    (
        "Rolex Submariner 5513",
        "Four-digit reference, matte dial with even patina on the tritium "
        "markers. Recently serviced and keeping time within specification.",
    ),
)


class Command(BaseCommand):
    help = "Seed a demo user with five items, each with generated pictures."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--username", default=DEFAULT_USERNAME, help="Username of the seeded user."
        )
        parser.add_argument(
            "--email", default=DEFAULT_EMAIL, help="Email of the seeded user."
        )
        parser.add_argument(
            "--password", default=DEFAULT_PASSWORD, help="Password of the seeded user."
        )
        parser.add_argument(
            "--pictures",
            type=int,
            default=DEFAULT_PICTURES,
            help="Pictures to generate per item.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete the seeded user's items and pictures before seeding again.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        username: str = options["username"]
        email: str = options["email"]
        password: str = options["password"]
        pictures: int = options["pictures"]
        flush: bool = options["flush"]

        user = self._user(username, email, password)
        if flush:
            self._delete_items(user)
        for index, (name, description) in enumerate(ITEMS):
            item, created = Item.objects.get_or_create(
                owner=user,
                name=name,
                defaults={"description": description},
            )
            self._pictures(item, index, pictures)
            self.stdout.write(
                f"{'created' if created else 'kept    '} item {item.id}: {item.name}"
            )

    def _user(self, username: str, email: str, password: str) -> User:
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            self.stdout.write(f"created user {user.id}: {user.username}")
        else:
            self.stdout.write(f"kept    user {user.id}: {user.username}")
        return user

    def _delete_items(self, user: User) -> None:
        # on_delete=DO_NOTHING, so the pictures have to go first.
        deleted_pictures, _ = ItemPictures.objects.filter(item__owner=user).delete()
        deleted_items, _ = Item.objects.filter(owner=user).delete()
        self.stdout.write(
            f"flushed {deleted_items} items and {deleted_pictures} pictures"
        )

    def _pictures(self, item: Item, palette: int, count: int) -> None:
        existing = set(
            ItemPictures.objects.filter(item=item).values_list("sort_order", flat=True)
        )
        for sort_order in range(count):
            if sort_order in existing:
                continue
            ItemPictures.objects.create(
                item=item,
                blob=render_picture(item.name, palette, sort_order, count),
                sort_order=sort_order,
            )


def render_picture(label: str, palette: int, index: int, total: int) -> bytes:
    """A placeholder PNG: a gradient card carrying the item's name."""
    top, bottom = PALETTES[palette % len(PALETTES)]
    image = _gradient(top, bottom)
    draw = ImageDraw.Draw(image)
    width, height = PICTURE_SIZE
    margin = 36

    draw.rectangle(
        [margin, margin, width - margin, height - margin], outline="#ffffff", width=4
    )
    _centre(draw, label, TITLE_FONT, height // 2, width, "#ffffff")
    _centre(draw, f"{index + 1} / {total}", INDEX_FONT, height - 96, width, "#e8e8e8")
    _centre(draw, "AUCTIONITE", BRAND_FONT, margin + 48, width, "#f0f0f0")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _gradient(top: str, bottom: str) -> Image.Image:
    width, height = PICTURE_SIZE
    start = ImageColor.getrgb(top)
    end = ImageColor.getrgb(bottom)
    image = Image.new("RGB", PICTURE_SIZE, start)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / (height - 1)
        colour = tuple(
            round(a + (b - a) * blend) for a, b in zip(start, end, strict=True)
        )
        draw.line([(0, y), (width, y)], fill=colour)
    return image


def _centre(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    y: int,
    width: int,
    fill: str,
) -> None:
    left, top, right, _ = draw.textbbox((0, 0), text, font=font)
    x, y = int((width - (right - left)) // 2 - left), int(y - top)
    draw.text((x + 2, y + 2), text, font=font, fill="#000000")
    draw.text((x, y), text, font=font, fill=fill)
