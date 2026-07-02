from src.exceptions import NotFoundException


class PostNotFoundException(NotFoundException):
    def __init__(self, post_id: int):
        super().__init__(detail=f"Post with id {post_id} not found")
