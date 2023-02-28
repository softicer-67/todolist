import logging
from datetime import datetime
from enum import IntEnum, auto
from pydantic import BaseModel
from django.conf import settings
from django.core.management import BaseCommand
from bot.models import TgUser
from bot.steps.storage import MemoryStorage
from bot.tg.client import TgClient
from bot.tg.dc import Message
from goals.models import Goal, GoalCategory


logger = logging.getLogger(__name__)


class NewGoal(BaseModel):
    cat_id: int | None = None
    goal_title: str | None = None

    @property
    def is_complete(self) -> None:
        return None not in [self.cat_id, self.goal_title]


class StateEnum(IntEnum):
    CREATE_CATEGORY_SELECT = auto()
    CHOSEN_CATEGORY = auto()


class Command(BaseCommand):
    help = "run bot"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient(settings.BOT_TOKEN)
        self.storage = MemoryStorage()

    def handle_user_without_verification(self, msg: Message, tg_user: TgUser):
        tg_user.set_verification_code()
        tg_user.save(update_fields=["verification_code"])
        self.tg_client.send_message(
            msg.chat.id, f"[verification code] {tg_user.verification_code}"
        )

    def fetch_tasks(self, msg: Message, tg_user: TgUser):
        gls = Goal.objects.filter(user=tg_user.user)
        if gls.count() > 0:
            resp_msg = [f"#{item.id} {item.title}" for item in gls]
            self.tg_client.send_message(msg.chat.id, "\n".join(resp_msg))
        else:
            self.tg_client.send_message(msg.chat.id, "[goals list is empty]")

    def handle_goals_categories(self, msg: Message, tg_user: TgUser):
        categories = GoalCategory.objects.filter(user=tg_user.user, is_deleted=False)
        if categories.count() > 0:
            resp_msg = [f"#{cat.id} {cat.title}" for cat in categories]
            self.tg_client.send_message(msg.chat.id, "Select category\n" + "\n".join(resp_msg))
        else:
            self.tg_client.send_message(msg.chat.id, "[you have no categories]")

    def handle_save_select_category(self, msg: Message, tg_user: TgUser):
        if msg.text.isdigit():
            cat_id = int(msg.text)
            if GoalCategory.objects.filter(user=tg_user.user, is_deleted=False, id=cat_id).exists():
                self.storage.update_data(chat_id=msg.chat.id, cat_id=cat_id)
                self.tg_client.send_message(msg.chat.id, '[set title]')
                self.storage.set_state(msg.chat.id, state=StateEnum.CHOSEN_CATEGORY)
            else:
                self.tg_client.send_message(msg.chat.id, '[category not found]')
        else:
            self.tg_client.send_message(msg.chat.id, "[invalid category id]")

    def handle_save_new_cat(self, msg: Message, tg_user: TgUser):
        goal = NewGoal(**self.storage.get_data(tg_user.chat_id))
        goal.goal_title = msg.text
        if goal.is_complete:
            Goal.objects.create(
                title=goal.goal_title,
                category_id=goal.cat_id,
                user=tg_user.user,
                due_date=datetime.now()
            )
            self.tg_client.send_message(msg.chat.id, '[new goal created]')
        else:
            self.tg_client.send_message(msg.chat.id, '[something went wrong]')

        self.storage.reset(tg_user.user)

    def handle_verified_user(self, msg: Message, tg_user: TgUser):
        if "/goals" in msg.text:
            self.fetch_tasks(msg, tg_user)

        elif "/create" in msg.text:
            self.handle_goals_categories(msg, tg_user)
            self.storage.set_state(msg.chat.id, state=StateEnum.CREATE_CATEGORY_SELECT)
            self.storage.set_data(msg.chat.id, data=NewGoal().dict())

        elif "/cancel" in msg.text and self.storage.get_state(tg_user.chat_id):
            self.storage.reset(tg_user.chat_id)
            self.tg_client.send_message(msg.chat.id, "[canceled]")

        elif state := self.storage.get_state(tg_user.chat_id):
            match state:
                case StateEnum.CREATE_CATEGORY_SELECT:
                    self.handle_save_select_category(msg, tg_user)
                case StateEnum.CHOSEN_CATEGORY:
                    self.handle_save_new_cat(msg, tg_user)
                case _:
                    logger.warning("Invalid state: %s", state)

        elif msg.text.startswith("/"):
            self.tg_client.send_message(msg.chat.id, "[unknown command]")

    def handle_message(self, msg: Message):
        tg_user, created = TgUser.objects.get_or_create(
            chat_id=msg.chat.id,
            defaults={"username": msg.from_.username},
        )
        if created:
            self.tg_client.send_message(msg.chat.id, "[greeting]")
        if tg_user.user:
            self.handle_verified_user(msg, tg_user)
        else:
            self.handle_user_without_verification(msg, tg_user)

    def handle(self, *args, **kwargs):
        offset = 0

        while True:
            res = self.tg_client.get_updates(offset=offset)
            for item in res.result:
                offset = item.update_id + 1
                self.handle_message(item.message)
