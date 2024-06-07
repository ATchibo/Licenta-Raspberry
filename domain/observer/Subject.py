from abc import ABC, abstractmethod

from domain.observer.Observer import Observer
from domain.observer.ObserverNotificationType import ObserverNotificationType


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
