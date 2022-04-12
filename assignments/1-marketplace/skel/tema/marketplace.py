"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

import unittest  # for unit testing
import itertools  # for converting dict.values into a list
from collections import defaultdict  # for dictionaries with key = int and value = list
from threading import Lock  # for syncronization
import time  # for settimg gmtime
import logging  # for logging
from logging.handlers import RotatingFileHandler  # for rotating log files

logging.basicConfig(
    handlers=[RotatingFileHandler('./marketplace.log', maxBytes=100000, backupCount=10)],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt='%Y-%m-%dT%H:%M:%S')
logging.Formatter.converter = time.gmtime


class MarketplaceTestCase(unittest.TestCase):
    """
        Class that tests all functionalities of the Marketplace.
    """

    def setUp(self):
        """
            Method that allowes user to define instructions
            that will be executed before each test method
            In this particular case: defining marketplace
        """
        self.marketplace = Marketplace(2)

    def test_register_producer(self):
        """
            Tests register_producer() from marketplace
        """
        self.assertEqual(self.marketplace.register_producer(), 0, 'wrong id registering producer')
        self.assertEqual(self.marketplace.producer_id, 1, 'wrong id producer')

    def test_publish(self):
        """
            Tests publish(producer_id, product) from marketplace
            Can't add more than 2 products because queue_size = 2
        """
        self.marketplace.register_producer()
        self.assertTrue(self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }), 'error publishing')
        self.assertTrue(self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }), 'error publishing')
        # should return false because queue is full
        self.assertFalse(self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }), 'error publishing')

    def test_new_cart(self):
        """
            Tests new_cart() from marketplace
            Should return 0 and increase cart_id
        """
        self.assertEqual(self.marketplace.new_cart(), 0, 'wrong id returned for new cart')
        self.assertEqual(self.marketplace.cart_id, 1, 'wrong id for new cart')

    def test_add_to_cart(self):
        """
            Tests add_to_cart(cart_id, product) from marketplace
            Should return true for Linden Tea and false for Error Tea
        """
        self.marketplace.new_cart()
        self.marketplace.register_producer()
        self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.assertTrue(self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }), 'error adding to cart')
        self.assertFalse(self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Error",
            "type": "Error",
            "price": 7
        }), 'this product is not in market')

    def test_remove_from_cart(self):
        """
            Tests remove_from_cart(cart_id, product) from marketplace
            Adding two products and removing one.
        """
        self.marketplace.register_producer()
        self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.new_cart()
        self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.remove_from_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.assertEqual(self.marketplace.carts[0], {0: [{
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }]}, 'error removing from cart')
        self.assertEqual(self.marketplace.producers[0], [{
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }], 'error adding product back in market')

    def test_place_order(self):
        """
            Tests place_order(cart_id) from marketplace
            Places order of two products
        """
        self.marketplace.register_producer()
        self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.publish(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.new_cart()
        self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.marketplace.add_to_cart(0, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        })
        self.assertEqual(self.marketplace.place_order(0), [{
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }, {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }], 'cart should have 2 products')


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
        logging.info('queue size per producer is %d', queue_size_per_producer)
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
        logging.info('registered producer with id %d', current_producer_id)
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
        logging.info('publishing: producer id is %d and product is %s', producer_id, product)
        # with self.publish_lock:
        if len(self.producers[producer_id]) >= self.queue_size_per_producer:
            logging.debug('returning false, queue is full')
            return False

        with self.publish_lock:
            self.producers[producer_id].append(product)
        logging.info('successfuly published product in queue')
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
        logging.info('registered cart with id %d', current_cart_id)
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
                logging.info('successfuly added to cart %d: %s', cart_id, product)
                return True
        logging.debug('product not in marketplace')
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
                    logging.info('successfuly removed from cart %d: %s', cart_id, product)
                    break

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        list_of_lists_of_products = self.carts[cart_id].values()
        products = list(itertools.chain.from_iterable(list_of_lists_of_products))
        logging.info('cart %d placed order with products: %s', cart_id, products)
        return products
