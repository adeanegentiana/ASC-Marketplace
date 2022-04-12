"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

# import unittest
import itertools
from collections import defaultdict

# class TestMarketplace(unittest.TestCase):
#     def setup(self):
#         self.register_producer = Marketplace.register_producer()
#
#     def test_upper(self):
#         self.assertEqual('foo'.upper(), 'FOO')
from threading import Lock


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.publish_lock = Lock()
        self.remove_from_cart_lock = Lock()
        self.producer_id = 0
        self.producer_id_lock = Lock()
        self.cart_id = 0
        self.cart_id_lock = Lock()
        self.carts = {}
        self.producers = {}

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        with self.producer_id_lock:
            current_producer_id = self.producer_id
        self.producers[self.producer_id] = []
        self.producer_id += 1
        return current_producer_id

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        with self.publish_lock:
            if len(self.producers[producer_id]) >= self.queue_size_per_producer:
                return False

            self.producers[producer_id].append(product)
            return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        with self.cart_id_lock:
            current_cart_id = self.cart_id
        self.carts[self.cart_id] = defaultdict(list)
        self.cart_id += 1
        return current_cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        for id_producer, products in self.producers.items():
            if product in products:
                products.remove(product)
                self.carts[cart_id][id_producer].append(product)
                return True
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        cart = self.carts[cart_id]
        with self.remove_from_cart_lock:
            for producer_id, products in cart.items():
                if product in products:
                    cart[producer_id].remove(product)
                    self.producers[producer_id].append(product)
                    break


    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        list_of_lists_of_products = self.carts[cart_id].values()
        products = list(itertools.chain.from_iterable(list_of_lists_of_products))
        return products
