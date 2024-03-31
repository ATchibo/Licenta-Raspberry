from abc import ABC, abstractmethod

from domain.observer.ObserverNotificationType import ObserverNotificationType


class Observer(ABC):

    @abstractmethod
    def on_notification_from_subject(self, notification_type: ObserverNotificationType) -> None:
        pass
