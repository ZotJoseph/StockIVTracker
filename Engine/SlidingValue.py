"""
Stores a value (such as stock iv) and ensure that it's always retrieved within a 24hr timeframe
"""

from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class ValueTime:
    """
    stores a value and a time associated with the value (typically when the value is retrieved)
    """
    def __init__(self, val : Any, time = datetime.now()):
        self.iv = val
        self.time = time

class SlidingValue(ABC):
    def __init__(self, val : Any = None):
        #TODO: allow database to add value when val doesn't exist (done when program first boots up)
        self.val = None
        if val:
            self.val = ValueTime(val, datetime.now())
        self._next_val = None

    @property
    def get_iv(self):
        return self.val.iv

    @staticmethod
    @abstractmethod
    def _compare(class_value, val) -> bool:
        """
        child class decides how to implement compare (bigger or smaller)
        """
        pass

    def _should_replace_val(self, val):
        """
        child class implement this method
        such that if return True
        val should replace self.val
        """
        return self._compare(self.val.iv, val)

    def _should_replace_next_val(self, val):
        """
        child class implement this method
        such that if return True
        val should replace self._next_val
        """
        return self._compare(self._next_val.iv, val)

    def update_value(self, val) -> Any:
        """
        when a new value is being stored, update the SlidingValue

        has self.val been staying longer than 24 hours? (forced replacement)
        is val bigger than self.val? (if so must reset all values)
        is val smaller than self.val but bigger than self._next_val?

        then return self._val.val (actual value)
        """



        if not self.val or self._should_replace_val(val):
            self.val=ValueTime(val, datetime.now())
        elif not self._next_val or self._should_replace_next_val(val):
            self._next_val=ValueTime(val, datetime.now())

        # val is smaller than both self._val and self_next_val, check time
        elif self.val.time + timedelta(days = 1) > datetime.now():
            self.val, self._next_val = self._next_val, self.val
            self._next_val = ValueTime(val, datetime.now())
            #^ sets _val to _next_val, and _next_val to val

        return self.val.iv


class MinSlidingValue(SlidingValue, ABC):
    """
    makes sure smallest value goes first
    """
    def _compare(self, class_value, val):
        """
        smallest has priority
        """
        return val <= self._next_val

class MaxSlidingValue(SlidingValue, ABC):
    """
    makes sure biggest value goes first
    """
    def _compare(self, class_value, val):
        """
        biggest has priority
        """
        return val >= self._next_val






