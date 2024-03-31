from abc import ABC, abstractmethod

from domain.observer.ObserverNotificationType import ObserverNotificationType
from domain.observer.Observer import Observer


class Subject(ABC):

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify(self, notification_type: ObserverNotificationType) -> None:
        pass
