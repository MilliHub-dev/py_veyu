from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    pass
    
    # @abstractmethod
    # def initiate_deposit(self, amount, currency, customer_details, reference):
    #     pass

    # @abstractmethod
    # def verify_deposit(self, reference):
    #     pass

    # @abstractmethod
    # def initiate_withdrawal(self, transaction_id, amount):
    #     pass

