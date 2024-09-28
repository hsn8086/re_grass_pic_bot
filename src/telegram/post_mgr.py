from src.util import SingletonMeta


class PostManager(metaclass=SingletonMeta):
    def __init__(self):
        self.tasks = {}

    def start_post_task(self, user_id, max_img=4):
        self.tasks[user_id] = {"images": [], "description": ""}
    def cancel_post_task(self, user_id):
        self.tasks.pop(user_id)

    def pop_task(self, user_id):
        return self.tasks.pop(user_id)

    def add_img(self, user_id, img):
        if user_id in self.tasks and len(self.tasks[user_id]["images"]) < 4:
            self.tasks[user_id]["images"].append(img)
            return True
        else:
            return False

    def add_description(self, user_id, description):
        if user_id in self.tasks:
            self.tasks[user_id]["description"] = description
            return True
        else:
            return False

    def check_user_task(self, user_id):
        return user_id in self.tasks
