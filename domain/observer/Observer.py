from abc import ABC, abstractmethod

from domain.observer.NotificationType import NotificationType


class Observer(ABC):

    @abstractmethod
    def update(self, notification_type: NotificationType) -> None:
        pass
